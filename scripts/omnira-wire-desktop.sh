#!/usr/bin/env bash
# Re-apply OMNIRA ↔ Hermes Desktop wiring after clone or profile reset.
set -euo pipefail

HERMES_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
OMNIOS_ROOT="${OMNIOS_ROOT:-$HOME/Desktop/omnios}"

mkdir -p "$HERMES_HOME/skills" "$HERMES_HOME/skill-bundles"
ln -sfn "$HERMES_ROOT/skills/omnira" "$HERMES_HOME/skills/omnira"

cat > "$HERMES_HOME/skill-bundles/omnira-boot.yaml" <<'EOF'
name: omnira-boot
description: OMNIRA substrate activation — pulse, council, surface map (desktop/weight).
skills:
  - omnira
EOF

cat > "$HERMES_HOME/omnira-session-prefill.json" <<'EOF'
[
  {
    "role": "user",
    "content": "/omnira-boot\n\nSurface: weight (Hermes Desktop on KjDesk). Boot level: nexus. Run organism activation before operational work. Working tree: ~/Desktop/omnios."
  }
]
EOF

if [[ ! -f "$HERMES_HOME/omnira-desktop.env" ]]; then
  cat > "$HERMES_HOME/omnira-desktop.env" <<EOF
export HERMES_HOME="\${HERMES_HOME:-$HERMES_HOME}"
export HERMES_ROOT="$HERMES_ROOT"
export HERMES_DESKTOP_CWD="$OMNIOS_ROOT"
export HERMES_DESKTOP_HERMES_ROOT="\$HERMES_ROOT"
export TERMINAL_CWD="$OMNIOS_ROOT"
export OMNIOS_SERVE_URL="\${OMNIOS_SERVE_URL:-http://192.168.5.199:5176}"
export OMNIOS_BRAIN_DIR="$OMNIOS_ROOT/.omni/omnira-brain"
export OMNIOS_KEYS_ENV="$OMNIOS_ROOT/.omni/keys.env"
EOF
fi

echo "✓ omnira skill → $HERMES_HOME/skills/omnira"
echo "✓ skill bundle omnira-boot"
echo "✓ prefill omnira-session-prefill.json (set prefill_messages_file in config.yaml)"
echo "Next: hermes desktop --build-only && hermes-desktop"
