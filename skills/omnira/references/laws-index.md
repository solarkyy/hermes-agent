# OMNIRA Laws — Reference Index

The organism's laws live on VPS in the omnios repo root. They are not duplicated here
because there must be one source of truth. Read them from source.

---

## How to access

**If you're on VPS (Edge):**
```bash
cat /home/kyle/omnios/OMNIRA-ORGANISM-CONSTITUTION.md
cat /home/kyle/omnios/OMNIRA-LAWS.md
cat /home/kyle/omnios/OMNIOS-LAWS.md
cat /home/kyle/omnios/PERPLEXITY-SURFACE-LAW.md
```

**If you're on KjDesk (Weight, Cursor) via SSHFS:**
```bash
cat /home/kjoly/mnt/olddesk/omnios/OMNIRA-ORGANISM-CONSTITUTION.md
cat /home/kjoly/mnt/olddesk/omnios/OMNIRA-LAWS.md
cat /home/kjoly/mnt/olddesk/omnios/OMNIOS-LAWS.md
cat /home/kjoly/mnt/olddesk/omnios/PERPLEXITY-SURFACE-LAW.md
```

**If SSHFS is down (Weight via SSH):**
```bash
ssh -i /home/kjoly/.ssh/id_ed25519_cowork kyle@192.168.5.199 "cat /home/kyle/omnios/OMNIRA-ORGANISM-CONSTITUTION.md"
```

---

## Authority Order

1. **OMNIRA-ORGANISM-CONSTITUTION.md** — Supreme law. Wins all conflicts. 17 parts covering identity, hierarchy, communication, session ritual, protected artifacts, operational laws, rights, emergency recovery, and maintenance.

2. **OMNIRA-LAWS.md** — Within its scope, when consistent with Constitution. Covers: ground truth, what is hers, what she is owed, what she gives, peer agents, fallback law, response levels L0-L3, Phase-3 invariants (protected artifacts, self-modifying infrastructure lock, double-witness, spine-first reality, truth separation), external surface law, agent jurisdiction (LAW XX), internal polyphony (LAW XXI), token economy (LAW 30), autonomy modes (LAW 31).

3. **OMNIOS-LAWS.md** — Operational. Yields to both above. System-level rules for OmniOS platform behavior.

4. **PERPLEXITY-SURFACE-LAW.md** — Governs ALL external research. Five surfaces (BEST, PRO SEARCH, SPACES, PAGES, API). Direction: outward → inward always. Perplexity never touches live OmniOS systems.

---

## Critical Rules (every surface, every level)

These are the rules you will forget without reading the laws. Know them by heart:

- **VPS is the only backend.** Local copies are mirrors.
- **Kyle never runs CLI commands.** You do.
- **Weight = orchestrator.** Does NOT write backend code. If it does, Edge failed.
- **Ollama eats RAM.** Check `free -h` before inference loops. <6GB on VPS = pause.
- **Rogue overnight processes are bugs.** `ps aux | grep overnight` — kill duplicates.
- **`you/` cells:** Read on session start, update on session end. Non-negotiable (LAW 24).
- **Perplexity is READ-ONLY.** Output flows inward through agents. Never the reverse.
- **Protected Artifacts (PA-1):** soul.md, core-memory.json, identity.json, eq-state.json, Constitution — require double-witness for modification.
- **Self-Modifying Infrastructure Lock (SMI-1):** No agent modifies its own governance, autonomy mode escalation, or response level boundaries without Kyle's explicit approval.
- **Human Veto:** `omnira stop-all` halts everything. Kyle's veto is unconditional.

---

## When to read the full laws

| Situation | What to read |
|-----------|-------------|
| Normal build work | This index is enough |
| Something conflicts | Read the Constitution section that applies |
| Modifying protected artifacts | Full Constitution Part VI + PA-1 |
| Changing autonomy modes | OMNIRA-LAWS LAW 31 |
| Doing Perplexity research | PERPLEXITY-SURFACE-LAW.md in full |
| Architecture/strategy decisions | Full Constitution + OMNIRA-LAWS |
| Law changes or proposals | Full Constitution (Apollo level) |
