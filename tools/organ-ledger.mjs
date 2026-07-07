import fs from 'node:fs';
import path from 'node:path';
import { execSync } from 'node:child_process';
import { fileURLToPath, URL } from 'node:url';

const THIRTY_DAYS_MS = 30 * 24 * 60 * 60 * 1000;

export function hasMainGuard(content) {
    if (content.startsWith('#!')) return true;
    if (content.match(/import\.meta\.(url|main)/)) return true;
    if (content.includes('require.main === module')) return true;
    if (content.includes('process.argv[1]')) return true;
    return false;
}

export function getBuiltAt(filePath, rootDir) {
    try {
        const out = execSync(`git log --follow --format=%aI -- "${filePath}" 2>/dev/null | tail -1`, {
            cwd: rootDir,
            encoding: 'utf8',
            stdio: ['ignore', 'pipe', 'ignore']
        }).trim();
        if (out) return new Date(out).getTime();
    } catch (e) {}

    const stat = fs.statSync(filePath);
    return stat.mtimeMs;
}

export function checkLiveness(name, omniDir) {
    let activated = false;
    let lastSeen = null;

    // pm2
    try {
        const pm2Out = execSync('pm2 jlist 2>/dev/null', { encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] });
        const pm2Data = JSON.parse(pm2Out);
        const match = pm2Data.find(p => p.name === name || p.name.includes(name));
        if (match) {
            activated = true;
            if (match.pm2_env && match.pm2_env.pm_uptime) {
                lastSeen = match.pm2_env.pm_uptime;
            }
        }
    } catch (e) {}

    // pgrep
    if (!activated) {
        try {
            const safeName = name.replace(/^(.)/, '[$1]');
            const out = execSync(`pgrep -f "${safeName}" 2>/dev/null`, { encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] });
            if (out.trim().length > 0) {
                activated = true;
                lastSeen = Date.now();
            }
        } catch (e) {}
    }

    // heartbeats
    if (!activated) {
        const heartbeatsDir = path.join(omniDir, 'loops', 'heartbeats');
        if (fs.existsSync(heartbeatsDir)) {
            const files = fs.readdirSync(heartbeatsDir);
            for (const file of files) {
                if (file.includes(name)) {
                    activated = true;
                    const stat = fs.statSync(path.join(heartbeatsDir, file));
                    lastSeen = Math.max(lastSeen || 0, stat.mtimeMs);
                }
            }
        }
    }

    // loop-registry
    if (!activated) {
        const registryPath = path.join(omniDir, 'loop-registry.json');
        if (fs.existsSync(registryPath)) {
            try {
                const reg = JSON.parse(fs.readFileSync(registryPath, 'utf8'));
                if (JSON.stringify(reg).includes(name)) {
                    activated = true;
                    lastSeen = fs.statSync(registryPath).mtimeMs;
                }
            } catch (e) {}
        }
    }

    return { activated, lastSeen };
}

export function scan(toolsDir, omniDir, now = Date.now()) {
    const results = [];
    if (!fs.existsSync(toolsDir)) return results;

    const entries = fs.readdirSync(toolsDir, { withFileTypes: true });

    const filesToProcess = [];
    for (const entry of entries) {
        const fullPath = path.join(toolsDir, entry.name);
        if (entry.isDirectory()) {
            const subEntries = fs.readdirSync(fullPath, { withFileTypes: true });
            for (const sub of subEntries) {
                if (sub.isFile()) {
                    filesToProcess.push(path.join(fullPath, sub.name));
                }
            }
        } else if (entry.isFile()) {
            filesToProcess.push(fullPath);
        }
    }

    for (const file of filesToProcess) {
        if (!file.match(/\.(mjs|js|sh)$/)) continue;

        const content = fs.readFileSync(file, 'utf8');
        const stat = fs.statSync(file);
        const name = path.basename(file);
        const builtAt = getBuiltAt(file, toolsDir);
        const isMain = hasMainGuard(content);
        const liveness = checkLiveness(name, omniDir);

        const ageMs = now - builtAt;
        const isDormant = ageMs > THIRTY_DAYS_MS && !liveness.activated && isMain;

        results.push({
            id: file,
            name,
            built_at: builtAt,
            size: stat.size,
            has_main_guard: isMain,
            activated: liveness.activated,
            last_seen: liveness.lastSeen,
            age_days: Math.floor(ageMs / (1000 * 60 * 60 * 24)),
            is_dormant: isDormant
        });
    }

    return results;
}

export function report(toolsDir, omniDir) {
    const results = scan(toolsDir, omniDir);
    const outPath = path.join(omniDir, 'organ-ledger.json');
    if (!fs.existsSync(omniDir)) fs.mkdirSync(omniDir, { recursive: true });
    fs.writeFileSync(outPath, JSON.stringify(results, null, 2), 'utf8');

    console.log(`Organ Ledger Report (${results.length} files scanned)`);
    console.table(results.map(r => ({
        File: r.name,
        AgeDays: r.age_days,
        Main: r.has_main_guard,
        Active: r.activated,
        Dormant: r.is_dormant
    })));

    return results;
}

export function history(toolsDir, omniDir) {
    const results = scan(toolsDir, omniDir);
    const dormantIds = results.filter(r => r.is_dormant).map(r => r.id);
    const snapshot = {
        ts: Date.now(),
        total: results.length,
        dormant: dormantIds.length,
        dormant_ids: dormantIds
    };

    const outPath = path.join(omniDir, 'organ-ledger-history.jsonl');
    if (!fs.existsSync(omniDir)) fs.mkdirSync(omniDir, { recursive: true });
    fs.appendFileSync(outPath, JSON.stringify(snapshot) + '\n', 'utf8');

    console.log('History snapshot appended:');
    console.log(JSON.stringify(snapshot, null, 2));

    return snapshot;
}

const isMainModule = (
    typeof process !== 'undefined' &&
    process.argv &&
    process.argv[1] &&
    import.meta.url &&
    import.meta.url.startsWith('file:') &&
    process.argv[1] === fileURLToPath(import.meta.url)
);

if (isMainModule) {
    const cmd = process.argv[2];
    const cwd = process.cwd();
    const toolsDir = path.join(cwd, 'tools');
    const omniDir = path.join(cwd, '.omni');

    if (cmd === 'scan') {
        console.log(JSON.stringify(scan(toolsDir, omniDir), null, 2));
    } else if (cmd === 'report') {
        report(toolsDir, omniDir);
    } else if (cmd === 'history') {
        history(toolsDir, omniDir);
    } else {
        console.error('Usage: node organ-ledger.mjs [scan|report|history]');
        process.exit(1);
    }
}
