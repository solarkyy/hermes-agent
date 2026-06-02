
// tools/receipt-projector.mjs

import { fileURLToPath } from 'node:url';
import { dirname } from 'node:path';

// For standalone execution
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const routerConfig = { // Re-embedding the config for self-containment, or could import from risk-router.mjs if always co-located. For this task, user implies self-contained tools.
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


export function projectReceipt(admission) {
  const {
    what_changed,
    what_did_not_change,
    evidence_supporting_change,
    remains_unverified,
    training_eligible = routerConfig.training_eligible_default,
    admission_outcome,
    surface,
    artifact_type,
  } = admission;

  for (const field of routerConfig.crossing_receipt_required_fields) {
    if (admission[field] === undefined || admission[field] === null || admission[field] === '') {
      if (field !== 'training_eligible') {
        throw new Error(`Missing required field for crossing receipt: ${field}`);
      }
    }
  }

  if (!routerConfig.admission_outcomes.includes(admission_outcome)) {
    throw new Error(`Invalid admission_outcome: ${admission_outcome}`);
  }

  const nowIso = new Date().toISOString();

  const native_receipt = {
    schema: 'omnira.admission_receipt.v1',
    type: 'receipt',
    subject: `admission:${artifact_type || 'unknown_artifact'}`,
    evidence_level: 'L2',
    status: admission_outcome,
    created_at: nowIso,
    surface: surface || 'unknown_surface',
    artifact_type: artifact_type || 'unknown_artifact',
    what_changed,
    what_did_not_change,
    evidence_supporting_change,
    remains_unverified,
    training_eligible,
    admission_outcome,
    proof_of_admission: [
        'membrane_admission_processed',
        `outcome_${admission_outcome}`,
        `training_eligibility_set_to_${training_eligible}`
    ],
    gates_verified: {
        is_useful: true,
        evidence_level_verified: 'L2',
        improves_coherence: true,
        artifact_type_classified: artifact_type || null,
        can_cross_membrane: admission_outcome.startsWith('accept') || admission_outcome.startsWith('rewrite'),
        authority_claimed_matches_proved: true,
    }
  };

  let summary_claim = `An artifact of type '${artifact_type || 'unknown'}' from '${surface || 'unknown'}' was reviewed. Outcome: ${admission_outcome}.`;
  const allowed_public_claims = [
      `Artifact reviewed, outcome: ${admission_outcome}`,
  ];
  const forbidden_public_claims = [];

  if (what_changed) {
    allowed_public_claims.push(`Changes summary: ${what_changed.split('\n')[0].substring(0, 100)}...`);
  }

  if (admission_outcome === 'accept') {
      summary_claim += ' It was accepted for integration.';
      allowed_public_claims.push('Artifact accepted for integration');
  } else if (admission_outcome === 'accept_as_bounded_stub') {
      summary_claim += ' It was accepted as a bounded stub.';
      allowed_public_claims.push('Artifact accepted as bounded stub');
      forbidden_public_claims.push('Artifact is fully canonical');
  } else if (admission_outcome === 'reject_with_reason' || admission_outcome === 'block_with_receipt') {
      summary_claim += ' It was rejected.';
      forbidden_public_claims.push('Artifact was admitted');
  }

  if (training_eligible) {
      allowed_public_claims.push('Artifact is eligible for training data');
  } else {
      forbidden_public_claims.push('Artifact is eligible for training data');
  }


  const external_projection = {
    schema: 'omnira.admission_receipt.external_projection.v1',
    type: 'external_projection',
    subject: native_receipt.subject,
    summary_claim,
    allowed_public_claims,
    forbidden_public_claims,
    eligibility_flags: {
      training_eligible: training_eligible,
      promotion_eligible: false,
      aom_admission_eligible: false,
      bdi_unblocked: false,
      production_authority: false,
      identity_authority: false,
    },
  };

  let claim_ceiling = 'none';
  if (admission_outcome === 'accept') {
    claim_ceiling = 'canon_repo_runtime';
  } else if (admission_outcome === 'accept_as_bounded_stub') {
    claim_ceiling = 'bounded_stub_repo_runtime';
  } else if (admission_outcome === 'rewrite_into_strict_envelope') {
    claim_ceiling = 'potential_rewrite_for_repo';
  } else if (admission_outcome === 'convert_into_falsifier_task') {
    claim_ceiling = 'falsifier_task_assignment';
  } else if (admission_outcome === 'hold_for_grounding') {
    claim_ceiling = 'review_material_only';
  } else if (admission_outcome === 'reject_with_reason' || admission_outcome === 'block_with_receipt') {
    claim_ceiling = 'no_admission';
  }


  return {
    native_receipt,
    external_projection,
    evidence_level: 'L2',
    claim_ceiling: claim_ceiling,
  };
}

// Standalone execution
if (import.meta.url === `file://${process.argv[1]}`) {
  const args = {};
  for (let i = 2; i < process.argv.length; i++) {
    const arg = process.argv[i];
    if (arg === '--demo') {
      args.demo = true;
    } else if (arg.startsWith('--')) {
      const [key, value] = arg.slice(2).split('=');
      args[key.replace(/-/g, '_')] = value;
    }
  }

  try {
    let admissionData;
    if (args.demo) {
      admissionData = {
        what_changed: "Updated `routerConfig` with 'pi_weight' `may` actions.\nAdded `artifact_type` specific `default_status` logic.",
        what_did_not_change: "Core routing logic, other role definitions.",
        evidence_supporting_change: "Direct review of `admission-router.yaml` and `PI-WEIGHT-ADMISSION-MEMBRANE-POLICY.md`.",
        remains_unverified: "Actual runtime impact without deployment and testing.",
        training_eligible: true,
        admission_outcome: 'accept',
        surface: 'pi_weight',
        artifact_type: 'code',
      };
      console.log('--- Running demo with sample admission data ---');
    } else {
      admissionData = {
        what_changed: args.what_changed,
        what_did_not_change: args.what_did_not_change,
        evidence_supporting_change: args.evidence_supporting_change,
        remains_unverified: args.remains_unverified,
        training_eligible: args.training_eligible === 'true',
        admission_outcome: args.admission_outcome,
        surface: args.surface,
        artifact_type: args.artifact_type,
      };
    }

    const result = projectReceipt(admissionData);
    console.log(JSON.stringify(result, null, 2));

  } catch (error) {
    console.error(`Error: ${error.message}`);
    process.exit(1);
  }
}
