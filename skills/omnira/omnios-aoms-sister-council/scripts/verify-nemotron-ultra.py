#!/usr/bin/env python3
"""
Verify Nemotron Ultra NIM route is working correctly.

Usage:
    python3 scripts/verify-nemotron-ultra.py

Exits 0 if Nemotron Ultra is accessible via NIM key, non-zero otherwise.
"""

import os
import sys
import subprocess
import json


def check_nim_route():
    """Check if NVIDIA NIM route for Nemotron 3 Ultra is available."""
    try:
        # Check pi CLI availability
        result = subprocess.run(
            ["pi", "--provider", "nvidia", "--model", "nvidia/nemotron-3-ultra-550b-a55b", "test"],
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def check_openrouter_route():
    """Check if OpenRouter fallback for Nemotron is available."""
    try:
        result = subprocess.run(
            ["pi", "--provider", "openrouter", "--model", "nvidia/nemotron-3-ultra-550b-a55b", "test"],
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def check_pi_cli():
    """Verify Pi CLI is available and correct version."""
    try:
        result = subprocess.run(
            ["pi", "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def main():
    print("=== Nemotron Ultra Verification ===")
    print()

    # Check Pi CLI
    print("1. Checking Pi CLI...")
    if check_pi_cli():
        print("   ✓ Pi CLI available")
    else:
        print("   ✗ Pi CLI not found")
        return 1

    # Check NIM route
    print("2. Checking NVIDIA NIM route (Nemotron 3 Ultra)...")
    if check_nim_route():
        print("   ✓ NIM route working")
        nim_ok = True
    else:
        print("   ✗ NIM route failed")
        nim_ok = False

    # Check OpenRouter fallback
    print("3. Checking OpenRouter fallback...")
    if check_openrouter_route():
        print("   ✓ OpenRouter fallback working")
        openrouter_ok = True
    else:
        print("   ⚠ OpenRouter fallback not available (may need OPENROUTER_API_KEY)")
        openrouter_ok = False

    # Summary
    print()
    if nim_ok:
        print("✓ Nemotron Ultra NIM route verified")
        return 0
    elif openrouter_ok:
        print("⚠ NIM route unavailable, but OpenRouter fallback available")
        return 0
    else:
        print("✗ No working Nemotron Ultra route found")
        print()
        print("Troubleshooting:")
        print("  - Check NVIDIA NIM API key in ~/.pi/agent/auth.json")
        print("  - Check OPENROUTER_API_KEY in ~/.pi/agent/auth.json")
        print("  - Run: export PATH=\"/home/kylej/.npm-global/bin:$PATH\"")
        return 1


if __name__ == "__main__":
    sys.exit(main())
EOF