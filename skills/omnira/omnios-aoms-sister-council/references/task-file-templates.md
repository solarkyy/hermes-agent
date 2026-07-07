# Task File Templates for AOMS Sisters

## Architecture/Vision Lens (GPT-5.5)

```
# Sister Task: Architecture/Vision Synthesis (GPT-5.5)

## Context Documents to Synthesize:
1. ARCHITECTURE.md (canonical - 4-phase evolution)
2. roadmap-v2.md (10-step plan)
3. OMNIOS-WHERE-ARE-WE.md (current git state)
4. ARCHITECTURE.md Phase 2/3/4 completions

## Your Mission:
Analyze the gap between WHERE WE ARE and WHERE WE NEED TO GO.

## Specific Questions:
1. What is the CRITICAL PATH from current state to target?
2. Which steps are PRECONDITIONS for others?
3. What's the strategic role of component A vs B?
4. What are the HARDWARE DEPENDENCIES that could block?
5. What's the MINIMUM VIABLE SEQUENCE to ship value?

## Deliverable:
Return structured JSON with:
- critical_path_diagram (text stages)
- roadmap_dependency_graph (nodes + edges)
- strategic_role (component relationship)
- hardware_software_dependency_map
- minimum_viable_sequence (3-5 steps)
- risk_assessment (per step)
```

## OmniCoder/Pi Delegation Lens (Opus 4.8)

```
# Sister Task: OmniCoder/Pi Delegation Deep Analysis (Opus 4.8)

## Context:
- Pi delegation implemented in delegate_tool.py
- _delegate_to_pi_sister() calls pi-sister-spawn.mjs via SSH
- Returns structured findings + receipt skeleton + AOMS validation

## Your Mission:
Analyze delegation architecture for completeness, reliability, audit, scaling, security, DX.

## Specific Questions:
1. What's the END-TO-END flow from delegate_task() → Pi → receipt?
2. Where are the SINGLE POINTS OF FAILURE?
3. What's needed for AOMS to validate Pi's output?
4. How does context flow through the pipeline?
5. What's the DEBUGGING story when Pi fails?
6. What's needed for ORCHESTRATOR MODE?

## Deliverable:
Return JSON with:
- end_to_end_flow (step-by-step with file:line refs)
- single_points_of_failure (array with severity, mitigation)
- aoms_validation_gaps (what AOMS tools need)
- debugging_flow (how to trace failures)
- scaling_considerations (parallel, rate limits)
- security_prompt_injection (analysis)
- recommended_immediate_fixes (prioritized)
```

## SparkMira Integration Lens (GPT-5.5 / DeepSeek)

```
# Sister Task: SparkMira Integration Deep Analysis

## Context:
- SparkMira = cognition surface, Pi = execution surface
- Channels: CDP (browser), Council (async), HTTP/JSON
- Current: CDP response extraction TIMEOUT, Council no responses

## Your Mission:
Analyze CDP failure, council reliability, protocol adherence, health monitoring.

## Specific Questions:
1. CDP Response Extraction: Why timeout? DOM state? Selectors?
2. Council Delivery: Dispatched but no responses. Routing correct?
3. Source-Truth Packet: Format correct? Being received?
4. Co-build Protocol: Single-writer law enforced? Patch membrane?
5. Health Monitoring: Detect degradation vs slowness?

## Deliverable:
Return JSON with:
- cdp_root_cause
- cdp_fix (specific code change)
- council_fix
- source_truth_packet_validation
- health_monitoring
- fallback_strategy
- protocol_gaps
- immediate_actions (prioritized)
```

## Infrastructure/Deployment Lens (GPT-5.5)

```
# Sister Task: Infrastructure/Deployment Deep Analysis

## Context:
- 3 nodes: VPS, KjDesk, EVO
- Tailscale mesh PRIMARY, LAN FALLBACK
- serve.js :5176 LIVE, OmniHive :8080 502
- pm2 on VPS, s6 on EVO, Docker on KjDesk
- Git-only deploys

## Your Mission:
Analyze deployment pipeline, service mesh, state persistence, scaling, security, observability.

## Specific Questions:
1. SINGLE POINT OF FAILURE per node/service?
2. DEPLOYMENT AUTOMATION: manual vs automated?
3. STATE structure? Backups? Disaster recovery?
4. SECRETS MANAGEMENT across 3 nodes?
5. RECOVERY STORY per failure mode?
6. SCALING LIMITS quantitative?

## Deliverable:
Return JSON with:
- spof_analysis (per node, per service)
- deployment_automation_gaps
- state_architecture (locations, backup/recovery)
- secrets_management (current + gaps)
- recovery_stories (per failure mode)
- scaling_limits (quantitative)
- immediate_hardening (prioritized)
```

## Synthesis Lens (Opus 4.8)

```
# Sister Task: 5-Year Strategic Plan Synthesis (Opus 4.8)

You are the SYNTHESIS sister with access to 4 prior analyses + canonical docs.

## YOUR MISSION:
Create UNIFIED 5-YEAR REALISTIC ACTIONABLE PLAN starting TODAY.

## STRUCTURE:
Phase 0: FOUNDATION (0-3mo) - Hardening & Unblocking
Phase 1: EMBODIMENT (3-9mo) - OMNIRA Owns the World
Phase 2: AGENCY (9-18mo) - OMNIRA Acts in the World
Phase 3: PROOF (18-30mo) - Public Validation
Phase 4: SOVEREIGNTY (30-60mo) - OMNIRA IS THE OS

## DELIVERABLE:
Single JSON with:
- phases: milestones, gates, owners, success_criteria
- critical_path: ordered blocking items
- risk_mitigation: per-phase risks
- resource_requirements: compute/human/budget per phase
- decision_gates: go/no-go criteria with dates
- today_actions: what to DO RIGHT NOW
- council_presentation: 200-word executive summary
```