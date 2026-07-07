# Phase 0 Execution Templates (SparkMira Co-Build)

## Task 1: Commit All 6 Artifacts (SparkMira via @github in ChatGPT UI)
```
@github create branch feature/gate0-phase0-artifacts
@github edit tools/sparkmira/cdp-lane-repro.mjs [F1 content]
@github edit docs/protocols/aoms-pi-delegation-schema-v0.json [F3 content]
@github edit docs/ops/2026-06-06-omnira-runtime-inventory.md [F7 content]
@github edit docs/issues/GATE-0-runtime-yellow-to-green.md [F6 content]
@github edit docs/diagnostics/omnihive-502-checklist.md [F4 content]
@github edit docs/ops/backup-contract-v0.md [F5 content]
@github commit "Phase 0: 6 GATE-0 artifacts (F1-F6)"
@github push
@github create PR "Phase 0 GATE-0 artifacts for runtime YELLOW→GREEN"
```

## Task 2: F1 100-Iteration CDP Soak (Pi on KjDesk)
```bash
cd /home/kyle/omnios
for i in {1..100}; do
  node tools/sparkmira/cdp-lane-repro.mjs \
    --lane co-build \
    --dispatch-cmd "node tools/sparkmira/pi-sparkmira-truth-packet.mjs --lane {lane} --nonce {nonce} --prompt-file {promptFile}" \
    --out .omni/receipts/gate0/f1-cdp-soak-${i}.json
done
# Verify: 100/100 nonce echo, 100/100 wrong-lane refusal, 0 contamination
```

## Task 3: F3 Schema Validation (Pi)
```bash
# Test valid packets pass, unsafe fixtures fail closed
# Required failures: max_depth>1, may_spawn=true, requires_pi_admission=false, path escape
# Validation against docs/protocols/aoms-pi-delegation-schema-v0.json
```

## Task 4: F7 Inventory Fill (Pi)
```bash
git remote -v
git branch --show-current
git rev-parse HEAD
git rev-parse origin/main
ssh vps git -C /home/kyle/omnios rev-parse HEAD
git status --short
git log --oneline -5
# Fill all 7 truth categories in docs/ops/2026-06-06-omnira-runtime-inventory.md
```

## Task 5: F4 OmniHive 502 Diagnosis (Pi/Edge - read-only)
```bash
curl -iS http://localhost:8080/health
ps -eo pid,ppid,stat,etime,pcpu,pmem,args | grep -Ei omn
ss -ltnp | grep :8080
journalctl --user -u omnira.service --since "1 hour ago" --no-pager
# Capture endpoint map, process map, port map, proxy routes, logs, commit touchpoints
```

## Task 6: F5 Backup Contract Execution (Pi/Edge)
```bash
# AGE_RECIPIENT + AGE_IDENTITY_PATH setup
# Backup flow → encrypt → checksum → offsite sync
# Restore drill into isolated temp dir → measure RTO → verify checksum → plaintext secret scan
# Target: RTO < 30min
```

## Task 7: F6 GATE-0 Checklist Population (Pi → Weight)
```bash
# Populate all verification command outputs and receipt paths
# Each F1-F7 verdict: UNKNOWN → PASS/WATCH/BLOCK with evidence
# Present to Weight for admission decision
```