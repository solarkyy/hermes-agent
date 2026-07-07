# Test Suite Hardening Pattern

Use when: running the organism's test suite to find and fix failures before a release, after a refactoring pass, or as part of systematic hardening.

## Methodology

### 1. Run the full suite, capture the summary

```bash
cd ~/Desktop/omnios && node --test tools/tests/*.test.mjs 2>&1 | grep -E "^(not ok|# tests|# pass|# fail)" | tail -10
```

Also run the base suite:
```bash
cd ~/Desktop/omnios && npm test 2>&1 | tail -10
```

### 2. Categorize failures by type

Run failing tests individually to get detailed errors:
```bash
node --test tools/tests/<failing-file>.test.mjs 2>&1 | grep -B2 -A10 "not ok"
```

**Three categories:**

| Category | Signal | Fix approach |
|----------|--------|-------------|
| **Stale test** | Import error, missing export, `MODULE_NOT_FOUND` | Remove stale imports, update exports, delete dead tests |
| **Change-detector** | Regex/count mismatch, deep-equal on changed data | Update test to match current implementation while preserving behavioral contract |
| **Real bug** | Behavioral assertion fails against correct expected value | Fix the implementation, not the test |

### 3. Fix change-detectors as behavioral contracts

The AGENTS.md rule: "if the test reads like a snapshot of current data, delete it. If it reads like a contract about how two pieces of data must relate, keep it."

**Bad (change-detector):**
```javascript
assert.match(src, /const adapter = provider === 'openai-codex' \? openaiCodexAdapter : githubCopilotAdapter;/);
```

**Good (behavioral contract):**
```javascript
assert.match(src, /'openai-codex': openaiCodexAdapter/);
assert.match(src, /const adapter = piAdapters\[provider\];/);
```

**Bad (count snapshot):**
```javascript
assert.ok(allowCount >= 4, 'should be present in 4+ allowlists');
```

**Good (minimum existence):**
```javascript
assert.ok(allowCount >= 2, 'should be present in adapter gate and adapter map');
```

### 4. Fix real bugs, not just tests

When a test reveals an actual implementation bug (like `isSparkMiraUrl` matching unrelated URLs), fix the implementation AND keep the test that caught it. The test was right — the code was wrong.

### 5. Handle env-var-gated modules

When a module gates all behavior behind an env var (like `OUTREACH_ENABLED`), tests that assume the gate is open will fail. Options:
- Add `{ skip: !ENV_VAR }` to tests that need the gate open
- Add a gate-verification test that checks behavior when the gate is closed
- Set the env var in the test runner command if the gate must be tested

### 6. Verify both suites after fixes

```bash
npm test  # base suite
node --test tools/tests/*.test.mjs  # tools suite
```

Both should be green before declaring hardening complete.

## Pitfalls

- **Don't fix tests by making them weaker.** Removing assertions to make tests pass is not hardening — it's erosion. Update the assertion to match the new behavioral contract.
- **Don't assume a passing individual test means the full suite passes.** Module caching, env var state, and test ordering can cause different results in isolation vs full suite.
- **3 skipped tests with explanation > 0 skipped tests with hidden failures.** If a test needs specific env state, skip it with a message rather than deleting it or making it always pass.
