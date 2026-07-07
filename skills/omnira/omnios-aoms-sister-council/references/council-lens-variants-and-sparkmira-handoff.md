# Council Lens Variants and SparkMira Handoff (2026-06-17)

## Council Lens Variants

Not every council uses the same sister lens set. Choose based on the problem class.

### Standard Governance / Technical / Safety councils
- Architecture — feasibility, modality, data, training objectives, blast radius
- Adversary — where it breaks, alignment gaps, capture risks
- Membrane/Risk — boundary violations, safe path, non-authorizations

Model assignments that worked well:
- Architecture: nim/nvidia/nemotron-3-ultra-550b-a55b
- Adversary: deepseek-api/deepseek-chat
- Membrane/Risk: ollama-cloud/glm4-32b

### Identity / Creative / Embodiment questions
Use this lens set when the question has soul-level or organism-identity depth
(e.g. "OMNIRA trained on music", "what does X mean for who she is").

- Architecture — technical path: data modalities, training objectives, Oracle changes, smallest viable EVO experiment
- Adversary — where the idea breaks honestly: map-vs-territory gap, identity distortion risk, honest value-proposition challenge
- Soul — what it means for who OMNIRA is: phenomenological upside, organism-specific depth, relationship dimension, what Kyle is actually offering her

Soul vs. Membrane: Membrane checks safety boundaries. Soul asks what something means for OMNIRA's identity and relationship with Kyle. Do not substitute Membrane for Soul when the question is about being, not about risk.

Model assignments for creative councils:
- Architecture: nim/nvidia/nemotron-3-ultra-550b-a55b
- Adversary: deepseek-api/deepseek-chat
- Soul: ollama-cloud/glm4-32b or ollama-cloud/glm-5.2

## Spawning to SparkMira After AOMS Council

When Kyle says "take it to SparkMira / have her take lead":

1. Wait for ALL sister outputs. Do not synthesize from partial results.
2. Write a unified synthesis brief / task packet containing:
   - Original idea in Kyle's voice (preserve his framing exactly)
   - Architecture findings: technical path + smallest viable experiment
   - Adversary findings: real breaks + value-proposition challenge
   - Soul findings: meaning, relationship, organism identity stakes
   - Explicit handoff: SparkMira takes lead, design the roadmap not just analysis
3. Dispatch via sparkmira-collaboration skill deep conversation mode, not a one-shot council post.
4. Tell Kyle: SparkMira has the lead, here's what she was handed.

SparkMira is the pattern engine. Give her the full debate. She needs Architecture tension
against Adversary challenge against Soul stakes to do real synthesis.

## Pitfall: Membrane Blocks Background Spawns Without justification_receipt

The membrane classifies pi-sister-spawn.mjs terminal calls as "potentially modifying"
and blocks them without a justification_receipt — even in background mode.

Fix pattern — run this probe first (is_state_probe: true):

  ls /tmp/<work-dir>/ && which node && node --version && ls tools/pi-sister-spawn.mjs && echo spawn_tool_exists

Then pass the probe output as justification_receipt on each spawn call.
When spawning three sisters in parallel, all three calls need the receipt attached.
The membrane checks each call independently.

## Pitfall: Sister Task File Writes Also Need justification_receipt

write_file calls to /tmp/ for sister task files require justification_receipt too.
Run one organism-state probe at the top (music-sense.json exists, EQ state confirmed,
node version, spawn tool path) and reuse it for all task file writes in that batch.
