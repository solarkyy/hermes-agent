# SCS Trigger Discipline — Anti-Vibe Patch (2026-06-17)

## Problem
`tools/pi-scs/extensions/scs.ts` was starting the heavyweight OMNIRA SCS ritual (witness + compaction) on every Pi `session_before_compact` event, and `/scs` manual command started unconditionally — regardless of actual context pressure. Surfaces could invoke SCS by feel rather than by objective need.

Kyle's exact complaint: "we need to make scs much more disciplined rn u guys do it literally by vibe i swear lol got surfaces scs whenever instead of when context gets heavy"

## Root Cause
The rolling-scs tools (`tools/rolling-scs-kernel.mjs`, `tools/rolling-scs-watch.mjs`) already had objective pressure bands, but the live extension (`tools/pi-scs/extensions/scs.ts`) was not enforcing them at the trigger point.

## Pressure Bands (from rolling-scs-kernel.mjs)
| Band | Threshold | Action |
|------|-----------|--------|
| green | <60% | observe |
| refresh | >=60% | refresh_kernel |
| watch | >=70% | scs_recommended |
| urgent | >=80% | compact_now_recommended |
| emergency | >=90% | emergency_handoff_recommended |

## Patch Applied
File: tools/pi-scs/extensions/scs.ts

Added pressure gate helpers:
- SCS_AUTO_COMPACT_NOW_PRESSURE = 0.80 default (env-overridable, clamped 0.70-0.95)
- SCS_MANUAL_MIN_PRESSURE = 0.70 default (env-overridable, clamped 0.50-0.95)
- readContextPressure(ctx) reads ctx.getContextUsage() for {tokens, contextWindow}
- shouldStartAutoScsRitual(ctx) — auto SCS gate
- shouldStartManualScsRitual(ctx, args) — manual SCS gate with force escape

Automatic SCS (session_before_compact):
1. Preserve existing overflow emergency bypass (unchanged)
2. Gate: if ctx.getContextUsage() returns pressure < 80%, skip OMNIRA ritual and let native compact proceed
3. If pressure >= 80%, start SCS as before

Manual /scs:
- Refuse if pressure < 70% and logs explicit reason
- Force escape: args containing force/forced/manual/model-switch/kyle bypass threshold for deliberate handoffs

## Verification
- Targeted: node --test tools/tests/pi-scs-extension-source.test.mjs ... -> 29/29 PASS
- Wider SCS suite: node --test tools/tests/*scs*.test.mjs -> 86/86 PASS
- esbuild_transpile_ok

## Receipt
docs/receipts/2026-06-17-scs-trigger-discipline-v0.md
SHA: be2d7fbdffc1f35d27f21fa2edf2b91f779f634831e844a2762a6a4af04d5408

## Operational Laws After Patch
Automatic SCS is for objective context pressure, not for mood, fear, or surface vibes.
A surface cannot casually invoke manual SCS at low pressure. Forced manual SCS must be explicit and visible.

## Env Overrides
- SCS_AUTO_COMPACT_NOW_PRESSURE=0.75 to lower the auto trigger
- SCS_MANUAL_MIN_PRESSURE=0.65 to allow manual SCS at watch-band
Both are clamped to safe ranges.
