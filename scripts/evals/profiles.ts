import { fail } from "./runtime.ts";

const EVAL_PROFILE_PRESETS = {
  fast: {
    name: "fast",
    description: "Fast inner-loop runs with GPT-5.4 mini for candidate and judge.",
    candidateModel: "openai/gpt-5.4-mini",
    judgeModel: "openai/gpt-5.4-mini",
    candidateOverlayProfiles: ["model-openai-gpt-5.4-mini"],
    judgeOverlayProfiles: ["model-openai-gpt-5.4-mini"],
  },
  gate: {
    name: "gate",
    description: "Candidate on GPT-5.4 mini, judged by GPT-5.4.",
    candidateModel: "openai/gpt-5.4-mini",
    judgeModel: "openai/gpt-5.4",
    candidateOverlayProfiles: ["model-openai-gpt-5.4-mini"],
    judgeOverlayProfiles: ["model-openai-gpt-5.4"],
  },
  prod: {
    name: "prod",
    description: "Production authoring default as candidate, judged by GPT-5.4.",
    candidateModel: "skill-default",
    judgeModel: "openai/gpt-5.4",
    candidateOverlayProfiles: [],
    judgeOverlayProfiles: ["model-openai-gpt-5.4"],
  },
  cross: {
    name: "cross",
    description: "Candidate on GPT-5.4 mini, judged by Claude Opus 4.7 through AI Gateway.",
    candidateModel: "openai/gpt-5.4-mini",
    judgeModel: "anthropic/claude-opus-4-7",
    candidateOverlayProfiles: ["model-openai-gpt-5.4-mini"],
    judgeOverlayProfiles: ["model-anthropic-claude-opus-4-7"],
  },
};

function dedupeStrings(values) {
  const deduped = [];
  const seen = new Set();

  for (const value of values) {
    if (seen.has(value)) {
      continue;
    }
    seen.add(value);
    deduped.push(value);
  }

  return deduped;
}

export function getEvalProfilePreset(rawValue) {
  const value = rawValue?.trim() || "fast";
  const preset = EVAL_PROFILE_PRESETS[value];

  if (!preset) {
    fail(
      `Unknown eval profile '${rawValue}'. Use one of: ${Object.keys(EVAL_PROFILE_PRESETS).join(", ")}.`,
    );
  }

  return {
    ...preset,
    candidateOverlayProfiles: dedupeStrings(preset.candidateOverlayProfiles ?? []),
    judgeOverlayProfiles: dedupeStrings(preset.judgeOverlayProfiles ?? []),
  };
}

export function summarizeEvalProfile(evalProfile) {
  return {
    name: evalProfile.name,
    description: evalProfile.description,
    candidate_model: evalProfile.candidateModel,
    judge_model: evalProfile.judgeModel,
    candidate_overlay_profiles: evalProfile.candidateOverlayProfiles,
    judge_overlay_profiles: evalProfile.judgeOverlayProfiles,
  };
}
