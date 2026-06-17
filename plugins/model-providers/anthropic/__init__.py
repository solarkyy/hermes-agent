"""Native Anthropic provider profile."""

import json
import logging
import urllib.request

from providers import register_provider
from providers.base import ProviderProfile

logger = logging.getLogger(__name__)


class AnthropicProfile(ProviderProfile):
    """Native Anthropic — supports API keys and Claude subscription OAuth."""

    @staticmethod
    def _looks_like_oauth_token(value: str) -> bool:
        """Return True for Claude Pro/Max OAuth-style credentials.

        Console API keys (``sk-ant-api*``) use ``x-api-key``. Claude Code,
        Hermes PKCE, and setup-token credentials are subscription OAuth and must
        use ``Authorization: Bearer`` so they do not masquerade as API keys.
        """
        token = (value or "").strip()
        if not token or token.startswith("sk-ant-api"):
            return False
        return token.startswith(("sk-ant-", "eyJ", "cc-"))

    def fetch_models(
        self,
        *,
        api_key: str | None = None,
        timeout: float = 8.0,
    ) -> list[str] | None:
        """Fetch models using the credential's native Anthropic auth mode."""
        if not api_key:
            return None

        header, value = (
            ("Authorization", f"Bearer {api_key}")
            if self._looks_like_oauth_token(api_key)
            else ("x-api-key", api_key)
        )
        try:
            req = urllib.request.Request("https://api.anthropic.com/v1/models")
            req.add_header(header, value)
            req.add_header("anthropic-version", "2023-06-01")
            req.add_header("Accept", "application/json")
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read().decode())
            return [
                m["id"]
                for m in data.get("data", [])
                if isinstance(m, dict) and "id" in m
            ]
        except Exception as exc:
            logger.debug("fetch_models(anthropic:%s): %s", header, exc)
            return None


anthropic = AnthropicProfile(
    name="anthropic",
    aliases=("claude", "claude-oauth", "claude-code"),
    api_mode="anthropic_messages",
    env_vars=("ANTHROPIC_API_KEY", "ANTHROPIC_TOKEN", "CLAUDE_CODE_OAUTH_TOKEN"),
    base_url="https://api.anthropic.com",
    auth_type="api_key",
    default_aux_model="claude-haiku-4-5-20251001",
)

register_provider(anthropic)
