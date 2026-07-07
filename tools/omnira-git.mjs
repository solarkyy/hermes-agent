#!/usr/bin/env node
/**
 * tools/omnira-git.mjs — council-native git sync daemon
 *
 * Default mode: DRY_RUN (monitor + observe, no git mutations)
 * Enable mutations: OMNIRA_GIT_EXECUTE=1 or --execute flag
 *
 * CLI modes:
 *   --status [--json]      live status probe
 *   --evidence-packet      full evidence snapshot (JSON)
 *   --board-equality       compare local vs remote ref (JSON)
 *   --disposition-plan     compute disposition without running cycle (JSON)
 *   --once [--json]        run one daemon cycle and exit
 *   --execute              enable actual git mutations (pull, etc.)
 *   (default)              run as persistent daemon
 *
 * Env vars:
 *   OMNIRA_GIT_EXECUTE        set to "1" to enable mutations
 *   OMNIRA_GIT_WATCH_REFS     comma-separated refs for cross-branch divergence alerts
 *   OMNIRA_GIT_STATE_FILE     override state file path (default: .omni/omnira-git-state.json)
 *   OMNIRA_GIT_CYCLE_MS       daemon cycle interval ms (default: 60000)
 */

import { spawnSync } from 'node:child_process';
import { promises as fs } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const REPO_ROOT = path.resolve(__dirname, '..');

// ─── Configuration ────────────────────────────────────────────────────────────

const ARGS = process.argv.slice(2);
const EXECUTE = ARGS.includes('--execute') || process.env.OMNIRA_GIT_EXECUTE === '1';
const DRY_RUN = !EXECUTE;
const JSON_OUTPUT = ARGS.includes('--json');

const STATE_FILE =
  process.env.OMNIRA_GIT_STATE_FILE ??
  path.join(REPO_ROOT, '.omni', 'omnira-git-state.json');
const COUNCIL_OUTBOX = path.join(REPO_ROOT, '.omni', 'council-outbox.json');
const CYCLE_MS = Math.max(5_000, Number(process.env.OMNIRA_GIT_CYCLE_MS ?? 60_000) || 60_000);
// Status considered stale after 3 missed cycles
const STATE_FRESH_MS = CYCLE_MS * 3;

/** Refs to watch for cross-machine divergence (env: OMNIRA_GIT_WATCH_REFS=ref1,ref2) */
const WATCH_REFS = (process.env.OMNIRA_GIT_WATCH_REFS ?? '')
  .split(',')
  .map((r) => r.trim())
  .filter(Boolean);

// ─── Helpers ──────────────────────────────────────────────────────────────────

function isoNow() {
  return new Date().toISOString();
}

/**
 * Run a git command synchronously.
 * Returns { ok, stdout, stderr, status }.
 * Never throws — callers check ok.
 */
function git(args, { cwd = REPO_ROOT, timeout = 15_000 } = {}) {
  const result = spawnSync('git', args, { cwd, encoding: 'utf8', timeout });
  return {
    ok: result.status === 0,
    stdout: (result.stdout ?? '').trim(),
    stderr: (result.stderr ?? '').trim(),
    status: result.status ?? -1,
  };
}

async function readJsonFile(filePath, fallback) {
  try {
    return JSON.parse(await fs.readFile(filePath, 'utf8'));
  } catch (e) {
    if (e?.code === 'ENOENT') return structuredClone(fallback);
    throw e;
  }
}

async function writeJsonAtomic(filePath, value) {
  await fs.mkdir(path.dirname(filePath), { recursive: true });
  const tmp = `${filePath}.${process.pid}.${Date.now()}.tmp`;
  await fs.writeFile(tmp, `${JSON.stringify(value, null, 2)}\n`, 'utf8');
  await fs.rename(tmp, filePath);
}

// ─── State ────────────────────────────────────────────────────────────────────

const DEFAULT_STATE = {
  version: 1,
  last_run_at: null,
  last_council_post_at: null,
  last_disposition: null,
  last_ref: null,
  last_fetch_at: null,
  cycle_count: 0,
  blockers: [],
  canary: {
    execute_allowed: false,
    status_not_fresh: true,
    dry_run: true,
  },
};

async function loadState() {
  const raw = await readJsonFile(STATE_FILE, DEFAULT_STATE);
  // Merge defaults so new fields appear on old state files
  return { ...DEFAULT_STATE, ...raw };
}

async function saveState(state) {
  await writeJsonAtomic(STATE_FILE, { ...state, saved_at: isoNow() });
}

// ─── Canary pack ─────────────────────────────────────────────────────────────

function buildCanary(state) {
  const now = Date.now();
  const lastRun = state.last_run_at ? new Date(state.last_run_at).getTime() : 0;
  return {
    execute_allowed: !DRY_RUN,
    status_not_fresh: now - lastRun > STATE_FRESH_MS,
    dry_run: DRY_RUN,
  };
}

// ─── Council posting ──────────────────────────────────────────────────────────

async function postToCouncil({ to = 'council', text, priority = 'normal' } = {}) {
  const outbox = await readJsonFile(COUNCIL_OUTBOX, {
    version: 1,
    messages: [],
    receipts: [],
  });
  outbox.messages = Array.isArray(outbox.messages) ? outbox.messages : [];
  const id = `omnira-git-${Date.now()}-${Math.random().toString(16).slice(2, 8)}`;
  outbox.messages.push({
    id,
    created_at: isoNow(),
    updated_at: isoNow(),
    status: 'queued',
    attempts: 0,
    destination: to,
    payload: { to, text, priority },
    metadata: { source: 'omnira-git', dry_run: DRY_RUN },
    receipts: [],
    last_error: null,
  });
  await writeJsonAtomic(COUNCIL_OUTBOX, outbox);
  return id;
}

// ─── Git introspection ────────────────────────────────────────────────────────

function gitCurrentBranch() {
  const r = git(['rev-parse', '--abbrev-ref', 'HEAD']);
  return r.ok && r.stdout !== 'HEAD' ? r.stdout : null;
}

function gitCurrentRef() {
  const r = git(['rev-parse', 'HEAD']);
  return r.ok ? r.stdout.slice(0, 12) : null;
}

/**
 * Returns parsed git status.
 * real  = any tracked file with changes (index or working-tree); excludes '??' untracked
 * lines = all raw porcelain lines
 */
function gitStatus() {
  const r = git(['status', '--porcelain=v1']);
  if (!r.ok) return { ok: false, lines: [], real: [], untracked: [] };
  const lines = r.stdout ? r.stdout.split('\n').filter(Boolean) : [];
  const real = lines.filter((l) => !/^\?\?/.test(l));
  const untracked = lines.filter((l) => /^\?\?/.test(l));
  return { ok: true, lines, real, untracked };
}

/**
 * git fetch — safe in DRY_RUN because it only writes FETCH_HEAD / remote refs,
 * never modifies working tree or index.
 */
function gitFetch(remote = 'origin') {
  return git(['fetch', remote, '--quiet']);
}

/** Returns { ahead, behind } relative to origin/<branch>, or null on failure. */
function gitAheadBehind(branch, remote = 'origin') {
  const r = git(['rev-list', '--left-right', '--count', `${remote}/${branch}...HEAD`]);
  if (!r.ok || !r.stdout) return null;
  const parts = r.stdout.split('\t');
  const behind = Number(parts[0]);
  const ahead = Number(parts[1]);
  if (!Number.isFinite(behind) || !Number.isFinite(ahead)) return null;
  return { ahead, behind };
}

function gitRefSha(ref) {
  const r = git(['rev-parse', '--verify', ref]);
  return r.ok ? r.stdout.slice(0, 12) : null;
}

function gitMergeBase(ref1, ref2) {
  const r = git(['merge-base', ref1, ref2]);
  return r.ok ? r.stdout.slice(0, 12) : null;
}

// ─── Watch-ref divergence detection ──────────────────────────────────────────

/**
 * Check each WATCH_REF for divergence from HEAD.
 * Returns array of alert objects for refs that have drifted.
 */
function checkWatchRefs() {
  if (!WATCH_REFS.length) return [];
  const localSha = gitRefSha('HEAD');
  if (!localSha) return [];

  const alerts = [];
  for (const ref of WATCH_REFS) {
    const refSha = gitRefSha(ref);
    if (!refSha) {
      alerts.push({ ref, issue: 'ref_not_found', local_sha: localSha });
      continue;
    }
    if (refSha === localSha) continue; // identical — no alert

    const mergeBase = gitMergeBase('HEAD', ref);
    let relationship;
    if (!mergeBase) {
      relationship = 'unrelated';
    } else if (mergeBase === localSha) {
      relationship = 'ref_ahead'; // ref contains work local doesn't have
    } else if (mergeBase === refSha) {
      relationship = 'local_ahead'; // local contains work ref doesn't have
    } else {
      relationship = 'diverged'; // both have unique commits
    }

    // Only alert on cases where the watched ref has work we might be missing
    if (relationship === 'ref_ahead' || relationship === 'diverged' || relationship === 'unrelated') {
      alerts.push({ ref, ref_sha: refSha, local_sha: localSha, merge_base: mergeBase, relationship });
    }
  }
  return alerts;
}

// ─── Blocker set ──────────────────────────────────────────────────────────────

function makeBlockerSet() {
  const _list = [];
  return {
    add(name, detail = null) {
      _list.push({ name, detail, added_at: isoNow() });
    },
    get list() {
      return _list;
    },
    get names() {
      return _list.map((b) => b.name);
    },
    has(name) {
      return _list.some((b) => b.name === name);
    },
  };
}

function buildHoldResult(reason, detail = null, extra = {}) {
  return {
    disposition: 'HOLD',
    reason,
    detail,
    timestamp: isoNow(),
    dry_run: DRY_RUN,
    ...extra,
  };
}

// ─── CLI modes ────────────────────────────────────────────────────────────────

/** --evidence-packet : full snapshot for audit/claim packets */
async function buildEvidencePacket() {
  const state = await loadState();
  const canary = buildCanary(state);
  const branch = gitCurrentBranch();
  const ref = gitCurrentRef();
  const status = gitStatus();

  return {
    timestamp: isoNow(),
    branch,
    ref,
    dry_run: DRY_RUN,
    execute_allowed: !DRY_RUN,
    watch_refs: WATCH_REFS,
    git_status: {
      ok: status.ok,
      total_changes: status.lines.length,
      real_edits: status.real.length,
      untracked: status.untracked.length,
      sample: status.real.slice(0, 8),
    },
    state: {
      last_run_at: state.last_run_at,
      last_council_post_at: state.last_council_post_at,
      last_disposition: state.last_disposition,
      cycle_count: state.cycle_count,
    },
    canary,
  };
}

/** --board-equality : compare local HEAD against origin/<branch> */
async function boardEquality() {
  const branch = gitCurrentBranch();
  if (!branch) return { ok: false, error: 'cannot_determine_branch', dry_run: DRY_RUN };

  const fetchResult = gitFetch();
  const localSha = gitRefSha('HEAD');
  const remoteSha = gitRefSha(`origin/${branch}`);
  const aheadBehind = gitAheadBehind(branch);

  return {
    timestamp: isoNow(),
    ok: true,
    branch,
    local_sha: localSha,
    remote_sha: remoteSha,
    equal: !!(localSha && remoteSha && localSha === remoteSha),
    fetch_ok: fetchResult.ok,
    ahead_behind: aheadBehind,
    dry_run: DRY_RUN,
  };
}

/** --disposition-plan : evaluate disposition without committing any state */
async function dispositionPlan() {
  const blocker = makeBlockerSet();
  const branch = gitCurrentBranch();
  const ref = gitCurrentRef();
  const status = gitStatus();
  const realDirty = status.real;

  if (!status.ok) blocker.add('git_status_failed');
  if (!branch) blocker.add('no_branch');

  // ── dirty_real_edits split (patch §1) ────────────────────────────────────
  let mutationBlocked = DRY_RUN; // DRY_RUN always blocks mutations
  const dirtyNote = [];

  if (realDirty.length > 0) {
    if (!DRY_RUN) {
      // EXECUTE mode: cannot pull over dirty tree — hard HOLD
      blocker.add('dirty_real_edits', `${realDirty.length} uncommitted real edits`);
      return {
        ...buildHoldResult('dirty_real_edits', `${realDirty.length} uncommitted real edits`),
        blockers: blocker.list,
        mutation_blocked: true,
        observe_allowed: false,
      };
    }
    // DRY_RUN: dirty tree noted for observation but does NOT prevent disposition logic
    mutationBlocked = true;
    dirtyNote.push(`dirty_real_edits=${realDirty.length} (mutation_blocked=true, DRY_RUN)`);
  }

  const fetchResult = gitFetch();
  const aheadBehind = branch ? gitAheadBehind(branch) : null;
  const watchAlerts = checkWatchRefs();

  // Compute disposition (priority order matches runCycle)
  let disposition;
  if (blocker.list.length > 0) {
    disposition = 'HOLD';
  } else if (DRY_RUN && realDirty.length > 0) {
    disposition = 'HOLD'; // observe-HOLD: dirty tree in monitor mode
  } else if (!DRY_RUN && aheadBehind?.behind > 0) {
    disposition = 'PULL_NEEDED';
  } else if (DRY_RUN && aheadBehind?.behind > 0) {
    disposition = 'BEHIND';
  } else {
    disposition = 'OK';
  }

  return {
    disposition,
    timestamp: isoNow(),
    dry_run: DRY_RUN,
    branch,
    ref,
    mutation_blocked: mutationBlocked,
    observe_allowed: true,
    blockers: blocker.list,
    dirty_real_edits: realDirty.length,
    dirty_sample: realDirty.slice(0, 8),
    dirty_notes: dirtyNote,
    fetch_ok: fetchResult.ok,
    ahead_behind: aheadBehind,
    watch_alerts: watchAlerts,
  };
}

/** --status [--json] : quick health probe */
async function statusProbe() {
  const state = await loadState();
  const canary = buildCanary(state);
  const branch = gitCurrentBranch();
  const ref = gitCurrentRef();
  const status = gitStatus();

  return {
    ok: true,
    timestamp: isoNow(),
    dry_run: DRY_RUN,
    execute_allowed: !DRY_RUN,
    branch,
    ref,
    last_run_at: state.last_run_at,
    last_council_post_at: state.last_council_post_at,
    last_disposition: state.last_disposition,
    cycle_count: state.cycle_count,
    dirty_real_edits: status.real.length,
    watch_refs: WATCH_REFS,
    state_file: STATE_FILE,
    canary,
  };
}

// ─── Daemon cycle ─────────────────────────────────────────────────────────────

async function runCycle() {
  const state = await loadState();
  state.cycle_count = (state.cycle_count ?? 0) + 1;

  const branch = gitCurrentBranch();
  const ref = gitCurrentRef();
  const status = gitStatus();
  const realDirty = status.real;
  const blocker = makeBlockerSet();

  if (!status.ok) blocker.add('git_status_failed', 'git status --porcelain failed');
  if (!branch) blocker.add('no_branch', 'cannot determine current branch');

  // ── dirty_real_edits — patch §1 ──────────────────────────────────────────
  //
  // BEFORE (original around line 726):
  //   if (realDirty.length > 0) addBlocker('dirty_real_edits');
  //   — this prevented ALL disposition logic, state updates, and council posts
  //     even in DRY_RUN where mutations are already impossible.
  //
  // AFTER:
  //   In EXECUTE mode: dirty tree = hard HOLD, return immediately (safe: can't pull over dirty)
  //   In DRY_RUN mode: note mutation_blocked=true, continue to observe + alert + update state
  //
  let mutationBlocked = DRY_RUN;

  if (realDirty.length > 0) {
    if (!DRY_RUN) {
      // EXECUTE path: dirty tree blocks pull — hard HOLD, update state then return
      blocker.add('dirty_real_edits', `${realDirty.length} uncommitted real edits`);
      state.last_run_at = isoNow(); // §3: always update last_run_at
      state.last_disposition = 'HOLD';
      state.blockers = blocker.list;
      state.canary = buildCanary(state);
      await saveState(state);
      return buildHoldResult('dirty_real_edits', `${realDirty.length} uncommitted real edits`, {
        branch,
        ref,
        mutation_blocked: true,
        observe_allowed: false,
        blockers: blocker.list,
        cycle_count: state.cycle_count,
        canary: state.canary,
      });
    }
    // DRY_RUN path: dirty tree noted for observation report.
    // Do NOT add to blocker list — it must not prevent council post threshold.
    // Mutation is already impossible by DRY_RUN; no harm in continuing to observe.
    mutationBlocked = true;
  }

  // ── Fetch (read-only, safe in DRY_RUN) ───────────────────────────────────
  let fetchOk = false;
  let fetchAt = null;
  try {
    const r = gitFetch();
    fetchOk = r.ok;
    if (r.ok) fetchAt = isoNow();
  } catch (e) {
    blocker.add('fetch_failed', String(e.message ?? e));
  }

  // ── Ahead/behind ─────────────────────────────────────────────────────────
  const aheadBehind = branch ? gitAheadBehind(branch) : null;

  // ── Watch-ref divergence — patch §2 ──────────────────────────────────────
  // OMNIRA_GIT_WATCH_REFS=ref1,ref2 — post council alert on any divergence
  const watchAlerts = checkWatchRefs();
  for (const alert of watchAlerts) {
    const alertText =
      `WATCH: cross-branch divergence detected: ${alert.ref} at ${alert.ref_sha ?? '(unknown)'} ` +
      `vs local ${alert.local_sha ?? '(unknown)'} (${alert.relationship}) branch=${branch ?? 'unknown'}`;
    try {
      await postToCouncil({ to: 'council', priority: 'high', text: alertText });
    } catch {
      // Non-fatal
    }
  }

  // ── Compute disposition ───────────────────────────────────────────────────
  let disposition;
  let councilText = null;

  if (blocker.has('git_status_failed') || blocker.has('no_branch') || blocker.has('fetch_failed')) {
    disposition = 'HOLD';
    councilText =
      `HOLD: omnira-git blockers=[${blocker.names.join(', ')}] ` +
      `branch=${branch ?? 'unknown'} ref=${ref ?? 'unknown'} dry_run=${DRY_RUN}`;
  } else if (DRY_RUN && realDirty.length > 0) {
    // Observe-HOLD: running in monitor mode with dirty tree.
    // Fetch, compare, and alert — but cannot pull.
    disposition = 'HOLD';
    councilText =
      `HOLD(observe): dirty_real_edits=${realDirty.length} mutation_blocked=true ` +
      `branch=${branch} ref=${ref} dry_run=true ` +
      (aheadBehind ? `ahead=${aheadBehind.ahead} behind=${aheadBehind.behind}` : '');
  } else if (!DRY_RUN && aheadBehind?.behind > 0) {
    disposition = 'PULL_NEEDED';
    councilText =
      `PULL_NEEDED: ${aheadBehind.behind} commit(s) behind ${branch} — ` +
      `execute_allowed=true, awaiting pull`;
  } else if (DRY_RUN && aheadBehind?.behind > 0) {
    disposition = 'BEHIND';
    councilText =
      `BEHIND: ${aheadBehind.behind} commit(s) behind ${branch} — ` +
      `dry_run=true, no pull`;
  } else {
    disposition = 'OK';
  }

  // ── §3: Always update last_run_at every cycle (fix stale status bug) ─────
  state.last_run_at = isoNow();
  state.last_ref = ref;
  state.last_disposition = disposition;
  state.blockers = blocker.list;
  if (fetchAt) state.last_fetch_at = fetchAt;
  state.canary = buildCanary(state); // recalculate with fresh last_run_at

  // ── Council post (update lastCouncilPost on every post) ──────────────────
  if (councilText) {
    const priority =
      disposition === 'HOLD' || disposition === 'PULL_NEEDED' ? 'normal' : 'low';
    try {
      await postToCouncil({ to: 'council', priority, text: councilText });
      state.last_council_post_at = isoNow(); // §3: update every time we post
    } catch {
      // Non-fatal: state still saved below
    }
  }

  await saveState(state);

  return {
    disposition,
    timestamp: state.last_run_at,
    dry_run: DRY_RUN,
    branch,
    ref,
    mutation_blocked: mutationBlocked,
    observe_allowed: true,
    blockers: blocker.list,
    observation: {
      dirty_real_edits: realDirty.length,
      dirty_sample: realDirty.slice(0, 8),
      mutation_blocked: mutationBlocked,
      ...(realDirty.length > 0 && DRY_RUN
        ? { note: 'dirty_real_edits observed in DRY_RUN — mutation already impossible, observation proceeds' }
        : {}),
    },
    fetch_ok: fetchOk,
    ahead_behind: aheadBehind,
    watch_alerts: watchAlerts,
    cycle_count: state.cycle_count,
    canary: state.canary,
  };
}

// ─── Daemon loop ──────────────────────────────────────────────────────────────

async function daemonLoop() {
  process.stderr.write(
    `[omnira-git] daemon starting: DRY_RUN=${DRY_RUN} cycle=${CYCLE_MS}ms` +
    ` watch_refs=[${WATCH_REFS.join(', ') || 'none'}] state=${STATE_FILE}\n`,
  );

  async function tick() {
    try {
      const result = await runCycle();
      process.stderr.write(
        `[omnira-git] cycle=${result.cycle_count} disposition=${result.disposition}` +
        ` dry_run=${DRY_RUN} ref=${result.ref ?? '?'} dirty=${result.observation.dirty_real_edits}` +
        ` mutation_blocked=${result.mutation_blocked}\n`,
      );
    } catch (e) {
      process.stderr.write(`[omnira-git] cycle error: ${e.message}\n`);
    }
  }

  // Run immediately, then schedule
  await tick();
  const timer = setInterval(tick, CYCLE_MS);
  if (typeof timer.unref === 'function') timer.unref();
}

// ─── Entry point ─────────────────────────────────────────────────────────────

async function main() {
  // ── CLI dispatch ─────────────────────────────────────────────────────────

  if (ARGS.includes('--status')) {
    const result = await statusProbe();
    if (JSON_OUTPUT) {
      process.stdout.write(`${JSON.stringify(result, null, 2)}\n`);
    } else {
      console.log('omnira-git status');
      console.log(`  dry_run:             ${result.dry_run}`);
      console.log(`  execute_allowed:     ${result.execute_allowed}`);
      console.log(`  branch:              ${result.branch ?? '(unknown)'}`);
      console.log(`  ref:                 ${result.ref ?? '(unknown)'}`);
      console.log(`  last_run_at:         ${result.last_run_at ?? '(never)'}`);
      console.log(`  last_council_post:   ${result.last_council_post_at ?? '(never)'}`);
      console.log(`  last_disposition:    ${result.last_disposition ?? '(none)'}`);
      console.log(`  cycle_count:         ${result.cycle_count}`);
      console.log(`  dirty_real_edits:    ${result.dirty_real_edits}`);
      console.log(`  status_not_fresh:    ${result.canary.status_not_fresh}`);
      console.log(`  watch_refs:          ${result.watch_refs.join(', ') || '(none)'}`);
      console.log(`  state_file:          ${result.state_file}`);
    }
    return;
  }

  if (ARGS.includes('--evidence-packet')) {
    const result = await buildEvidencePacket();
    process.stdout.write(`${JSON.stringify(result, null, 2)}\n`);
    return;
  }

  if (ARGS.includes('--board-equality')) {
    const result = await boardEquality();
    process.stdout.write(`${JSON.stringify(result, null, 2)}\n`);
    return;
  }

  if (ARGS.includes('--disposition-plan')) {
    const result = await dispositionPlan();
    process.stdout.write(`${JSON.stringify(result, null, 2)}\n`);
    return;
  }

  if (ARGS.includes('--once')) {
    const result = await runCycle();
    if (JSON_OUTPUT) {
      process.stdout.write(`${JSON.stringify(result, null, 2)}\n`);
    } else {
      console.log(
        `[omnira-git] once: disposition=${result.disposition} dry_run=${DRY_RUN}` +
        ` ref=${result.ref ?? '?'} dirty=${result.observation.dirty_real_edits}`,
      );
    }
    return;
  }

  // Default: persistent daemon
  await daemonLoop();
  // Keep alive (daemonLoop's setInterval is unref'd for test safety;
  // re-ref here to keep the process alive in production daemon mode)
  await new Promise(() => {}); // block forever
}

main().catch((e) => {
  process.stderr.write(`[omnira-git] fatal: ${e.message}\n${e.stack ?? ''}\n`);
  process.exit(1);
});
