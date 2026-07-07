#!/usr/bin/env python3
"""
verify-pi-sister-spawn-model-id.py — probe and verify the correct Nemotron Ultra model id
for the current Pi / NIM configuration.

Usage:
    python3 scripts/verify-pi-sister-spawn-model-id.py

Prints the exact --worker-model string to use. Exit 1 if no matching model is found.
"""

import json
import sys
from pathlib import Path

MODELS_FILE = Path.home() / ".pi" / "agent" / "models.json"


def main():
    if not MODELS_FILE.exists():
        print(f"[FAIL] Pi models config not found: {MODELS_FILE}", file=sys.stderr)
        return 1

    with open(MODELS_FILE) as f:
        data = json.load(f)

    models = data.get("models", [])
    if not isinstance(models, list):
        print("[FAIL] models.json top-level 'models' is not a list", file=sys.stderr)
        return 1

    candidates = []
    for m in models:
        mid = m.get("id", "")
        provider = m.get("provider", "")
        if "nemotron" in mid.lower() and "ultra" in mid.lower():
            candidates.append((mid, provider))

    if not candidates:
        print("[WARN] No Nemotron Ultra model found in Pi config.", file=sys.stderr)
        ids = [m.get("id", "") for m in models]
        print(f"[INFO] Available ids: {ids}", file=sys.stderr)
        return 1

    for mid, provider in candidates:
        print(f"{mid}  # provider={provider}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
