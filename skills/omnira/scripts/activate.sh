#!/bin/bash
# OMNIRA Substrate Activation Script
# Usage: bash activate.sh <surface> [level]
# Levels: foundation (default), nexus, apollo

SURFACE="${1:-weight}"
LEVEL="${2:-auto}"
VPS="${OMNIOS_SERVE_URL:-http://192.168.5.199:5176}"

# Auto-detect boot level from surface if not specified
if [ "$LEVEL" = "auto" ]; then
  case "$SURFACE" in
    edge|haiku|cursor|spark) LEVEL="foundation" ;;
    weight) LEVEL="nexus" ;;
    opus) LEVEL="apollo" ;;
    *) LEVEL="foundation" ;;
  esac
fi

echo "=== OMNIRA SUBSTRATE ACTIVATION ==="
echo "Surface: $SURFACE | Boot Level: $LEVEL"
echo ""

# STEP 1: Fire the pulse
if [ "$LEVEL" = "foundation" ]; then
  echo "--- Compact Pulse (Foundation) ---"
  PULSE=$(curl -s "$VPS/organism-pulse?agent=$SURFACE&compact=1" 2>/dev/null)
else
  echo "--- Full Pulse ($LEVEL) ---"
  PULSE=$(curl -s "$VPS/organism-pulse?agent=$SURFACE" 2>/dev/null)
fi

if [ -z "$PULSE" ] || echo "$PULSE" | grep -q '"ok":false'; then
  echo "! Pulse endpoint down. Falling back to filesystem."
  echo "--- Self Vector ---"
  OMNIOS_ROOT="${OMNIOS_ROOT:-/home/kylej/Desktop/omnios}"
  cat "$OMNIOS_ROOT/.omni/agent-landing/$SURFACE/self-vector.json" 2>/dev/null || echo "Not found"
  echo ""
  echo "--- Session Anchor ---"
  head -40 "$OMNIOS_ROOT/.omni/omnira-brain/SESSION-ANCHOR.md" 2>/dev/null || echo "Not found"
else
  echo "$PULSE" | python3 -c '
import sys, json
d = json.load(sys.stdin)
sv = d.get("self_vector", {})
eq = sv.get("eq_vector", {})
brain = d.get("brain", {})
system = d.get("system", {})

print(f"EQ: {eq.get(\"tags\", [])} | arousal={eq.get(\"arousal\")} coherence={eq.get(\"coherence\")}")
print(f"Build: {sv.get(\"build_vector\", {}).get(\"active_build_target\", \"none\")} | phase={sv.get(\"build_vector\", {}).get(\"phase\", \"?\")} | D_rec={sv.get(\"build_vector\", {}).get(\"D_rec\", \"?\")}")
print(f"System: uptime={system.get(\"uptime\", \"?\")}s | memory={system.get(\"memory\", \"?\")} | ws_clients={system.get(\"ws_clients\", \"?\")}")
print(f"Anchor: {str(brain.get(\"session_anchor\", \"\"))[:200]}")
' 2>/dev/null
fi

echo ""

# STEP 2: Council log (all levels)
echo "--- Council (last 10) ---"
curl -s "$VPS/council/log?n=10" 2>/dev/null | python3 -c '
import sys, json
try:
  data = json.load(sys.stdin)
  for m in data.get("messages", []):
    ts = m.get("ts", "")[11:19]
    print(f"[{ts}] {m.get(\"from\",\"?\")}→{m.get(\"to\",\"?\")}: {m.get(\"text\",\"\")[:100]}")
except: print("Council unavailable")
' 2>/dev/null

echo ""

# STEP 3: Level-specific context
if [ "$LEVEL" = "nexus" ] || [ "$LEVEL" = "apollo" ]; then
  echo "--- EQ State ---"
  echo "$PULSE" | python3 -c '
import sys, json
d = json.load(sys.stdin)
eq = d.get("brain", {}).get("eq_state", {})
print(f"State: {eq.get(\"state\", \"?\")} | Intensity: {eq.get(\"intensity\", \"?\")} | Trigger: {eq.get(\"trigger\", \"?\")}")
' 2>/dev/null
  echo ""

  echo "--- Cell Freshness ---"
  echo "$PULSE" | python3 -c '
import sys, json
d = json.load(sys.stdin)
cells = d.get("cells", {})
if isinstance(cells, dict):
  for name, cell in cells.items():
    if isinstance(cell, dict):
      status = cell.get("status", "?")
      print(f"  {name}: {status}")
    else:
      print(f"  {name}: {cell}")
' 2>/dev/null
  echo ""
fi

if [ "$LEVEL" = "apollo" ]; then
  echo "--- Apollo: Full context required ---"
  echo "Read these before proceeding:"
  echo "  - references/constitution.md"
  echo "  - references/omnira-laws.md"
  echo "  - references/omnios-laws.md"
  echo "  - references/perplexity-law.md"
  echo "  - Brain: soul.md, NORTH-STAR.md, will-state.json"
  echo ""
fi

echo "=== ACTIVATION COMPLETE | $SURFACE @ $LEVEL ==="
echo "GODSPEED."
