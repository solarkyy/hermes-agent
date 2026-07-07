# Membrane-Compliant Artifact Writes

Use this when repairing or creating OMNIRA artifacts from a prior session, especially when the task involves claims about files, runtime state, gate status, backups, diagnostics, or admission.

## Durable lesson

Do not use shell heredocs for long markdown artifacts that may contain code fences, backticks, or literal delimiter examples such as `EOF`. A heredoc can close early and cause the remaining markdown to execute as shell, producing errors like `unexpected EOF while looking for matching \`` and leaving partial files.

Prefer Hermes file tools:

- `read_file` / `search_files` for inspection
- `write_file` for full artifact replacement or creation
- `patch` for targeted repair

## Membrane sequence

1. Probe state first with a read-only command/tool.
   - Confirm each target path is present/missing and capture size/line count when useful.
   - If using `terminal`, mark it as a state probe: `is_state_probe: true`.
   - If using `read_file` or `search_files`, these are inherently read-only and don't need the flag.
2. Treat that probe output as the receipt.
3. Mutate only after the receipt exists.
   - Use `write_file` or `patch`.
   - Pass the probe output as `justification_receipt` when the tool requires it.
   - For `terminal` commands that modify state (non-probe), also pass `justification_receipt`.
4. Read back the changed artifacts.
5. Verify mechanical integrity.
   - file exists
   - expected title/status/claim ceiling present
   - line count/size sane
   - markdown code fences balanced
6. Check git status for touched paths.
7. If using the session registry, release the claimed lane with what changed and what remains unadmitted.
8. Report claim ceiling clearly to Kyle/council.

## Admission discipline

Artifact creation is not runtime admission.

For gate docs, backup contracts, diagnostic checklists, or council artifacts:

- Say `template`, `checklist`, `contract`, or `receipt` when that is all that exists.
- Do not call a runtime GREEN unless the required live receipts and admission authority exist.
- If Weight/admission is required, a single surface cannot self-promote.

## Quick verification snippet

Use a small Python check rather than hand-inspecting long markdown:

```bash
python3 - <<'PY'
from pathlib import Path
for p in [
    'docs/issues/GATE-0-runtime-yellow-to-green.md',
    'docs/diagnostics/omnihive-502-checklist.md',
    'docs/ops/backup-contract-v0.md',
]:
    path = Path(p)
    if not path.exists():
        print(p, 'MISSING')
        continue
    text = path.read_text()
    print(p, 'exists', 'size', len(text.encode()), 'lines', len(text.splitlines()),
          'fences_balanced', text.count('```') % 2 == 0,
          'fences', text.count('```'))
PY
```

Adapt paths to the active artifact packet.