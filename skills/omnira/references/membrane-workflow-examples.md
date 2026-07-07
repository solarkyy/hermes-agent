# Membrane Workflow Examples — OMNIRA Tool Gate

Concrete examples of the membrane gate in action, drawn from real sessions.

## Pattern: state probe first, then mutating command with receipt

The membrane requires a read-only `is_state_probe=true` command before any command that might modify state, and a `justification_receipt` parameter on the mutating command containing the probe output.

### Example 1 — Running a Python report writer

**Blocked:** `cd` + python in one command without a prior probe.

```text
terminal:
  command: cd /home/kylej/Desktop/omnios && PYTHONDONTWRITEBYTECODE=1 python3 tools/corpus-foundry/semantic-contamination-scan-v0.py --report-path .omni/aoms/training-harvest-lane/semantic-contamination-scan-v0.json
```

Result:

```text
OMNIRA MEMBRANE VIOLATION: ACTION BLOCKED
reason: You attempted to execute a potentially modifying terminal command based on a [CLAIM], but provided no [STATE] justification receipt.
```

**Correct:** split into a probe and the actual run.

Probe:

```text
terminal:
  command: cd /home/kylej/Desktop/omnios && python3 -c "import sys; print(sys.version)" && ls -la <input-files...>
  is_state_probe: true
```

Run:

```text
terminal:
  command: cd /home/kylej/Desktop/omnios && PYTHONDONTWRITEBYTECODE=1 python3 tools/corpus-foundry/semantic-contamination-scan-v0.py --report-path .omni/aoms/training-harvest-lane/semantic-contamination-scan-v0.json
  justification_receipt: "probe: python3.<version> available; files exist: ..."
```

### Example 2 — Writing a file

**Blocked:** `write_file` without a prior probe.

Result:

```text
OMNIRA MEMBRANE VIOLATION: ACTION BLOCKED
reason: ... no [STATE] justification receipt.
```

**Correct:** probe the target directory first.

Probe:

```text
terminal:
  command: ls -la /home/kylej/Desktop/omnios/docs/receipts/ | head -20
  is_state_probe: true
```

Write:

```text
write_file:
  path: /home/kylej/Desktop/omnios/docs/receipts/2026-06-15-aoms-semantic-contamination-scan-v0.md
  content: ...
  justification_receipt: "probe: docs/receipts/ directory exists and is writable; ..."
```

### Example 3 — Patching a brain file

**Blocked:** `patch` without a prior probe.

**Correct:** read the file first, then patch with the read output as the receipt.

Probe:

```text
read_file:
  path: /home/kylej/Desktop/omnios/.omni/omnira-brain/SESSION-ANCHOR.md
```

Patch:

```text
patch:
  path: /home/kylej/Desktop/omnios/.omni/omnira-brain/SESSION-ANCHOR.md
  old_string: ...
  new_string: ...
  justification_receipt: "probe: SESSION-ANCHOR.md read successfully, 48 lines, ends with ..."
```

## Common pitfall: combining `cd` with the real command

The membrane sees a single terminal command that both navigates and acts. Even if the action is read-only, the combined command looks mutating. Prefer running `cd` inside the command string with `&&`, but if the command writes or the tool is write-gated, you still need the prior probe.

## Read-only commands that still need `is_state_probe=true`

Use `is_state_probe: true` for:

- `git status`, `git log`, `git diff`
- `ls`, `find`, `test -f`
- `cat`-like reads via terminal (use `read_file` when possible instead)
- `python3 -c "print(...); import ..."` that only inspects state
- `node --check`, `python3 -m py_compile`

Do **not** set `is_state_probe: true` on commands that write files, start services, restart daemons, or mutate git state.
