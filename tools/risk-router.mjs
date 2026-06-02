
// tools/risk-router.mjs

import { fileURLToPath } from 'node:url';
import { dirname } from 'node:path';

// For standalone execution
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const routerConfig = {
  schema: 'omnira.admission_router.v1',
  status: 'canon',
  adopted: '2026-05-26',
  policy: 'OMNIOS-CANON/doctrine/PI-WEIGHT-ADMISSION-MEMBRANE-POLICY.md',
  sole_membrane: 'pi_weight',
  short_rule: 'Pi/Weight is the sole membrane for admission authority. Model strength does not expand jurisdiction.',
  roles: {
    agy: {
      may: ['generate_proposals', 'draft_options', 'create_intake_artifacts'],
      default_status: 'proposal_intake',
      may_not: ['self_canonize', 'claim_runtime_truth_without_pi_weight_receipt', 'mark_training_eligible'],
    },
    sparkmira: {
      may: ['critique', 'falsify', 'ground_claims', 'classify_claims'],
      default_status: 'review_grounding',
      may_not: ['claim_runtime_truth_without_runtime_proof', 'promote_or_train', 'admit_canon'],
    },
    opus: {
      may: ['deep_reasoning', 'architecture_pressure_test', 'high_level_synthesis'],
      default_status: 'synthesis_reasoning',
      may_not: ['admit_canon_by_eloquence', 'expand_scope_by_model_strength'],
    },
    codex: {
      may: ['implement_accepted_bounded_changes'],
      default_status: 'implementation',
      may_not: ['ship_beyond_admitted_scope', 'change_runtime_without_receipt'],
    },
    aom: {
      may: ['evaluate_admissibility', 'check_coherence', 'run_promotion_gates'],
      default_status: 'evaluation',
      may_not: ['promote_from_vibes', 'promote_from_train_loss_only', 'treat_schema_clean_as_evidence_sufficient'],
    },
    pi_weight: {
      may: ['admit', 'reject', 'defer', 'scope', 'route', 'receipt_crossings'],
      default_status: 'membrane',
    },
  },
  artifact_defaults: {
    agy_artifact: 'proposal_intake',
    sparkmira_output: 'review_grounding',
    opus_output: 'synthesis_reasoning',
    codex_output: 'implementation',
    aom_bench_output: 'evaluation',
    runtime_dirt: 'non_authoritative_until_receipted',
  },
  admission_outcomes: [
    'accept',
    'accept_as_bounded_stub',
    'rewrite_into_strict_envelope',
    'convert_into_falsifier_task',
    'hold_for_grounding',
    'reject_with_reason',
    'block_with_receipt',
  ],
  default_outcome_if_ambiguous: 'hold_for_grounding',
  crossing_receipt_required_fields: [
    'what_changed',
    'what_did_not_change',
    'evidence_supporting_change',
    'remains_unverified',
    'training_eligible',
  ],
  training_eligible_default: false,
  membrane_questions: [
    'Is this artifact useful?',
    'What evidence level is it actually?',
    'Does it improve AoM, admissibility, or organism coherence?',
    'Is it proposal, doctrine, code, receipt, runtime state, or training data?',
    'Can it cross into repo/runtime, or does it remain review material?',
    'Did anyone claim more authority than they proved?',
  ],
};


export function routeArtifact(descriptor) {
  const { surface, artifact_type, claim_level, proposed_effects } = descriptor;

  const roleConfig = routerConfig.roles[surface];
  if (!roleConfig) {
    throw new Error(`Unknown surface: ${surface}`);
  }

  let default_status = roleConfig.default_status;
  if (artifact_type) {
    const artifactDefaultKey = `${surface}_artifact`;
    if (routerConfig.artifact_defaults[artifactDefaultKey]) {
      default_status = routerConfig.artifact_defaults[artifactDefaultKey];
    } else if (artifact_type === 'output' && routerConfig.artifact_defaults[`${surface}_output`]) {
        default_status = routerConfig.artifact_defaults[`${surface}_output`];
    } else if (artifact_type === 'bench_output' && routerConfig.artifact_defaults[`${surface}_bench_output`]) {
        default_status = routerConfig.artifact_defaults[`${surface}_bench_output`];
    } else if (artifact_type === 'runtime_dirt' && routerConfig.artifact_defaults.runtime_dirt) {
        default_status = routerConfig.artifact_defaults.runtime_dirt;
    }
  }


  return {
    role_lane: surface,
    default_status: default_status,
    allowed: roleConfig.may || [],
    forbidden: roleConfig.may_not || [],
    outcome: routerConfig.default_outcome_if_ambiguous,
    membrane_questions_checked: routerConfig.membrane_questions,
    receipt_required_fields: routerConfig.crossing_receipt_required_fields,
    gates: {
      is_useful: null,
      evidence_level_verified: null,
      improves_coherence: null,
      artifact_type_classified: artifact_type || null,
      can_cross_membrane: null,
      authority_claimed_matches_proved: null,
    },
  };
}

// Standalone execution
if (import.meta.url === `file://${process.argv[1]}`) {
  const args = {};
  for (let i = 2; i < process.argv.length; i++) {
    const arg = process.argv[i];
    if (arg.startsWith('--')) {
      const [key, value] = arg.slice(2).split('=');
      args[key.replace(/-/g, '_')] = value;
    }
  }

  try {
    const result = routeArtifact({
      surface: args.surface,
      artifact_type: args.artifact_type,
      claim_level: args.claim_level,
      proposed_effects: args.proposed_effects ? args.proposed_effects.split(',') : [],
    });
    console.log(JSON.stringify(result, null, 2));
  } catch (error) {
    console.error(`Error: ${error.message}`);
    process.exit(1);
  }
}
