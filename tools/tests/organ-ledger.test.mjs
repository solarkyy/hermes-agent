import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
import { scan } from '../organ-ledger.mjs';

const FIXTURE_DIR = path.join(__dirname, 'fixture_workspace');
const TOOLS_DIR = path.join(FIXTURE_DIR, 'tools');
const OMNI_DIR = path.join(FIXTURE_DIR, '.omni');
const THIRTY_TWO_DAYS = 32 * 24 * 60 * 60 * 1000;

function setup() {
    if (fs.existsSync(FIXTURE_DIR)) {
        fs.rmSync(FIXTURE_DIR, { recursive: true, force: true });
    }
    fs.mkdirSync(TOOLS_DIR, { recursive: true });
    fs.mkdirSync(path.join(OMNI_DIR, 'loops', 'heartbeats'), { recursive: true });

    // 1. Synthetic organ with fake heartbeat evidence
    const activeTool = path.join(TOOLS_DIR, 'active-tool.mjs');
    fs.writeFileSync(activeTool, '#!/usr/bin/env node\nconsole.log("active");\n');
    fs.writeFileSync(path.join(OMNI_DIR, 'loops', 'heartbeats', 'active-tool.mjs.json'), '{"alive":true}');

    // Set old date
    const oldTimeMs = Date.now() - THIRTY_TWO_DAYS;
    const oldTimeSec = oldTimeMs / 1000;
    fs.utimesSync(activeTool, oldTimeSec, oldTimeSec);

    // 2. Synthetic dormant-old organ
    const dormantTool = path.join(TOOLS_DIR, 'dormant-tool.mjs');
    fs.writeFileSync(dormantTool, '#!/usr/bin/env node\nconsole.log("dormant");\n');
    fs.utimesSync(dormantTool, oldTimeSec, oldTimeSec);

    // 3. Synthetic library-no-main-guard organ
    const libraryTool = path.join(TOOLS_DIR, 'lib-tool.mjs');
    fs.writeFileSync(libraryTool, 'export function noOp() {}\n');
    fs.utimesSync(libraryTool, oldTimeSec, oldTimeSec);

    // New tool
    const newTool = path.join(TOOLS_DIR, 'new-tool.mjs');
    fs.writeFileSync(newTool, '#!/usr/bin/env node\nconsole.log("new");\n');
}

function teardown() {
    if (fs.existsSync(FIXTURE_DIR)) {
        fs.rmSync(FIXTURE_DIR, { recursive: true, force: true });
    }
}

function runTests() {
    setup();

    try {
        const results = scan(TOOLS_DIR, OMNI_DIR);

        const active = results.find(r => r.name === 'active-tool.mjs');
        const dormant = results.find(r => r.name === 'dormant-tool.mjs');
        const lib = results.find(r => r.name === 'lib-tool.mjs');
        const newt = results.find(r => r.name === 'new-tool.mjs');

        assert(active, 'active-tool missing');
        assert(dormant, 'dormant-tool missing');
        assert(lib, 'lib-tool missing');
        assert(newt, 'new-tool missing');

        // Verify has_main_guard
        assert(active.has_main_guard === true, 'active-tool should have main guard');
        assert(lib.has_main_guard === false, 'lib-tool should NOT have main guard');

        // Verify liveness evidence
        assert(active.activated === true, 'active-tool should be activated (heartbeat found)');
        assert(dormant.activated === false, 'dormant-tool should not be activated');

        // Verify dormancy
        assert(active.is_dormant === false, 'active-tool is not dormant');
        assert(dormant.is_dormant === true, 'dormant-tool is dormant (old + no heartbeat + main)');
        assert(lib.is_dormant === false, 'lib-tool is not dormant (no main guard)');
        assert(newt.is_dormant === false, 'new-tool is not dormant (too new)');

        console.log('✅ All tests passed.');
        console.table(results.map(r => ({
            File: r.name, Age: r.age_days, Main: r.has_main_guard, Active: r.activated, Dormant: r.is_dormant
        })));
    } finally {
        teardown();
    }
}

runTests();
