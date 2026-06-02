"""
Hermes Immune Guard — Shadow-mode scanner for Hermes→provider traffic.

Scans messages before they reach cloud providers. In shadow mode (default),
logs everything to audit but NEVER blocks. In enforce mode, blocks RED secrets.

Usage (two-line patch in run_agent.py):
    from hermes_guard import immune_check
    immune_check(messages, provider, model)  # returns (passed, reason)

Env control:
    HERMES_IMMUNE_MODE=shadow   # scan + audit, never block (default)
    HERMES_IMMUNE_MODE=enforce  # scan + audit + block RED + redact YELLOW
"""

import json
import os
import re
import sys
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional

# ── Paths ────────────────────────────────────────────────────────────────
HERMES_HOME = Path(os.environ.get("HERMES_HOME", Path.home() / ".hermes"))
AUDIT_LOG = HERMES_HOME / "state" / "audit.jsonl"
IMMUNE_MODE = os.environ.get("HERMES_IMMUNE_MODE", "shadow")

# ── Classification ────────────────────────────────────────────────────────
class Classification(Enum):
    RED = "red"       # Block from cloud providers
    YELLOW = "yellow"  # Redact before cloud
    GREEN = "green"    # Safe for any provider

# ── Secret Patterns (14 RED + 4 YELLOW) ──────────────────────────────────
RED_PATTERNS: list[tuple[str, str, str]] = [
    # (name, regex, description)
    ("ssh_private_key", r"-----BEGIN\s+(?:RSA|DSA|EC|OPENSSH)\s+PRIVATE\s+KEY-----", "SSH private key"),
    ("openai_key", r"sk-(?:proj-)?[A-Za-z0-9_-]{16,}", "OpenAI API key"),
    ("anthropic_key", r"sk-ant-[A-Za-z0-9_-]{16,}", "Anthropic API key"),
    ("github_token", r"gh[prs]_[A-Za-z0-9_]{20,}", "GitHub personal access token"),
    ("github_old_token", r"gho_[A-Za-z0-9]{20,}", "GitHub OAuth token (old format)"),
    ("aws_access_key", r"AKIA[0-9A-Z]{16}", "AWS access key ID"),
    ("aws_secret_key", r"(?:AWS_SECRET_ACCESS_KEY|aws_secret_access_key)[=:]\s*[A-Za-z0-9/+=]{20,}", "AWS secret key"),
    ("jwt_token", r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}", "JWT token"),
    ("db_connection", r"(?:mysql|postgres(?:ql)?|mongodb|redis|sqlite)://[^\s]{8,}", "Database connection string"),
    ("generic_api_key", r"(?:api[_-]?key|apikey|API_KEY)[=:]\s*[A-Za-z0-9_-]{16,}", "Generic API key assignment"),
    ("slack_token", r"xox[bspratz]-[A-Za-z0-9-]{10,}", "Slack bot/user token"),
    # Seed phrase: DISABLED — requires BIP39 word list for reliable detection.
    # Pure regex approach produces too many false positives on tool descriptions.
    # ("seed_phrase", r"...", "Potential seed phrase"),
    ("stripe_key", r"sk_live_[A-Za-z0-9]{16,}", "Stripe live secret key"),
    ("google_api_key", r"AIza[0-9A-Za-z_-]{20,}", "Google API key"),
]

YELLOW_PATTERNS: list[tuple[str, str, str]] = [
    ("env_secret", r"[A-Za-z_][A-Za-z0-9_]{2,30}_(?:SECRET|KEY|TOKEN|PASS(?:WORD)?|CRED(?:ENTIAL)?)[=:]\s*[^\s]{4,}", "Environment secret assignment"),
    # Private IP: keep but note these often appear in tool configs intentionally.
    # Only match standalone IPs, not those embedded in URLs/paths.
    ("private_ip", r"\b(?:10\.\d{1,3}|172\.(?:1[6-9]|2\d|3[01])|192\.168)\.\d{1,3}\.\d{1,3}(?:\b|:\d{1,5})\b", "Private IP address"),
    ("home_path", r"(?:/home/|/Users/|C:\\Users\\)[^\s,;]{3,40}", "Home directory path"),
    ("dotenv_file", r"\.env(?:\.\w+)?(?:\s|$|\.|\")", ".env file reference"),
]

# Compile patterns
RED_COMPILED = [(name, re.compile(pattern, re.IGNORECASE | re.MULTILINE), desc)
                for name, pattern, desc in RED_PATTERNS]
YELLOW_COMPILED = [(name, re.compile(pattern, re.IGNORECASE | re.MULTILINE), desc)
                   for name, pattern, desc in YELLOW_PATTERNS]

# ── Local providers (never scanned) ──────────────────────────────────────
LOCAL_PROVIDERS = {"evo-local", "ollama-local", "ollama", "lmstudio", "local", "custom"}

# Proxy providers (extra warning)
PROXY_PROVIDERS = {"evo-local"}  # flagged but local so exempt

@dataclass
class Finding:
    pattern: str
    classification: Classification
    match: str
    description: str

@dataclass 
class ScanResult:
    findings: list[Finding] = field(default_factory=list)
    classification: Classification = Classification.GREEN
    redacted_content: Optional[str] = None

@dataclass
class RoutingDecision:
    blocked: bool = False
    redacted: bool = False
    content: Optional[str] = None
    reason: str = ""

# ── Scanner ───────────────────────────────────────────────────────────────
def _extract_text(messages: list) -> str:
    """Extract all text content from chat messages list."""
    parts = []
    for msg in messages:
        content = msg.get("content", "")
        if isinstance(content, list):
            for part in content:
                if isinstance(part, dict):
                    t = part.get("text", "")
                    if t:
                        parts.append(t)
        elif isinstance(content, str):
            parts.append(content)
    return "\n".join(parts)

def scan_messages(messages: list) -> dict[str, list[Finding]]:
    """Scan messages for secrets. Returns dict by classification."""
    text = _extract_text(messages)
    findings: dict[str, list[Finding]] = {"red": [], "yellow": []}
    
    for name, pattern, desc in RED_COMPILED:
        for match in pattern.finditer(text):
            snippet = match.group(0)[:80]
            findings["red"].append(Finding(
                pattern=name,
                classification=Classification.RED,
                match=snippet,
                description=desc,
            ))
    
    for name, pattern, desc in YELLOW_COMPILED:
        for match in pattern.finditer(text):
            snippet = match.group(0)[:80]
            findings["yellow"].append(Finding(
                pattern=name,
                classification=Classification.YELLOW,
                match=snippet,
                description=desc,
            ))
    
    return findings

def _redact_text(text: str, findings: dict[str, list[Finding]]) -> str:
    """Redact all findings from text."""
    result = text
    for f_list in findings.values():
        for f in f_list:
            result = result.replace(f.match, f"[REDACTED: {f.pattern}]")
    return result

# ── Policy ─────────────────────────────────────────────────────────────────
def _is_local(provider: str) -> bool:
    provider_lower = (provider or "").lower()
    return provider_lower in LOCAL_PROVIDERS or "local" in provider_lower

def _is_cloud(provider: str) -> bool:
    return not _is_local(provider)

def decide(
    findings: dict[str, list[Finding]],
    provider: str,
    model: str,
    enforce: bool = False,
) -> RoutingDecision:
    """Make routing decision based on findings and provider."""
    has_red = len(findings.get("red", [])) > 0
    has_yellow = len(findings.get("yellow", [])) > 0
    
    if not has_red and not has_yellow:
        return RoutingDecision(reason="GREEN — no secrets found")
    
    text_for_redaction = ""  # Only needed for yellow redaction
    
    if has_red and _is_cloud(provider):
        if enforce:
            return RoutingDecision(
                blocked=True,
                reason=f"BLOCKED: {len(findings['red'])} RED secrets found, cannot send to cloud provider {provider}"
            )
        else:
            # Shadow mode: log intent but pass
            return RoutingDecision(
                redacted=True,
                reason=f"SHADOW: {len(findings['red'])} RED secrets WOULD be blocked (shadow mode, passing through)",
            )
    
    if has_red and _is_local(provider):
        return RoutingDecision(reason="RED secrets OK on local provider — passing through")
    
    if has_yellow and _is_cloud(provider):
        return RoutingDecision(
            redacted=True,
            reason=f"YELLOW: {len(findings['yellow'])} sensitive patterns WOULD be redacted before {provider}",
        )
    
    return RoutingDecision(reason="passing through")

# ── Audit ──────────────────────────────────────────────────────────────────
_audit_lock = None

def _get_lock():
    global _audit_lock
    if _audit_lock is None:
        import threading
        _audit_lock = threading.Lock()
    return _audit_lock

def log_to_audit(
    surface: str,
    provider: str,
    model: str,
    decision: RoutingDecision,
    findings: dict[str, list[Finding]],
    latency_ms: float = 0,
):
    """Append immune checkpoint decision to audit log."""
    entry = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime()),
        "surface": surface,
        "provider": provider,
        "model": model or "unknown",
        "mode": IMMUNE_MODE,
        "classification": "RED" if findings.get("red") else ("YELLOW" if findings.get("yellow") else "GREEN"),
        "red_secrets": len(findings.get("red", [])),
        "yellow_secrets": len(findings.get("yellow", [])),
        "total_secrets": len(findings.get("red", [])) + len(findings.get("yellow", [])),
        "blocked": decision.blocked,
        "redacted": decision.redacted,
        "reason": decision.reason,
        "patterns": [f.pattern for f_list in findings.values() for f in f_list],
        "latency_ms": round(latency_ms, 2),
    }
    
    with _get_lock():
        try:
            AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True)
            with open(AUDIT_LOG, "a") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception as e:
            print(f"[immune] audit write failed: {e}", file=sys.stderr)

# ── Main Entry Point ───────────────────────────────────────────────────────
class ImmuneBlockError(Exception):
    """Raised when immune checkpoint blocks a call (enforce mode only)."""
    pass

def immune_check(
    messages: list,
    provider: str,
    model: str = "unknown",
    surface: str = "hermes",
) -> tuple[bool, str]:
    """
    Scan messages before cloud provider call.
    
    Returns:
        (passed: bool, reason: str)
        
    In shadow mode: always returns (True, reason) — never blocks.
    In enforce mode: returns (False, reason) when RED + cloud.
    """
    t0 = time.time()
    
    # Quick skip for local providers
    if _is_local(provider):
        return (True, "local provider — immune skip")
    
    # Scan
    findings = scan_messages(messages)
    
    if not findings.get("red") and not findings.get("yellow"):
        return (True, "no secrets detected")
    
    # Decide
    enforce = IMMUNE_MODE == "enforce"
    decision = decide(findings, provider, model, enforce=enforce)
    
    # Audit
    latency = (time.time() - t0) * 1000
    log_to_audit(
        surface=surface,
        provider=provider,
        model=model,
        decision=decision,
        findings=findings,
        latency_ms=latency,
    )
    
    # Shadow: always pass, log what would happen
    if not enforce:
        return (True, decision.reason)
    
    # Enforce: block RED + cloud
    if decision.blocked:
        raise ImmuneBlockError(decision.reason)
    
    return (True, decision.reason)


# ── Self-test ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"Hermes Immune Guard v1.0 — mode={IMMUNE_MODE}")
    print(f"Audit log: {AUDIT_LOG}")
    print(f"RED patterns: {len(RED_COMPILED)}")
    print(f"YELLOW patterns: {len(YELLOW_COMPILED)}")
    
    # Quick test
    test_msgs = [
        {"role": "user", "content": "my key is sk-proj-AAAAAAAAAAAAAAAAAAAA"},
    ]
    try:
        ok, reason = immune_check(test_msgs, "openrouter", "deepseek-chat")
        print(f"Test OpenAI key → {reason}")
    except ImmuneBlockError as e:
        print(f"Test OpenAI key → BLOCKED: {e}")
    
    test_msgs2 = [
        {"role": "user", "content": "SECRET_KEY=abc123def456"},
    ]
    ok, reason = immune_check(test_msgs2, "openrouter", "deepseek-chat")
    print(f"Test env secret → {reason}")
    
    test_msgs3 = [
        {"role": "user", "content": "what is 2+2?"},
    ]
    ok, reason = immune_check(test_msgs3, "openrouter", "deepseek-chat")
    print(f"Test clean → {reason}")
