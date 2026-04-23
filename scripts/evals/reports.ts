import path from "node:path";
import { extractEvalMetadata } from "./manifest.ts";
import { summarizeEvalProfile } from "./profiles.ts";
import { compareStatuses, summarizeNumeric, worstStatus } from "./status.ts";

export function buildBenchmark(skillName, evalEntry, trials) {
  const judgeStatuses = trials.map((trial) => trial.report.overall_status);
  const combinedStatuses = trials.map((trial) => trial.summary.combined_status);
  const deterministicPassCount = trials.filter(
    (trial) => trial.deterministic_checks.overall_pass,
  ).length;

  const checkStats = new Map();
  for (const trial of trials) {
    for (const check of trial.deterministic_checks.checks) {
      if (!checkStats.has(check.id)) {
        checkStats.set(check.id, {
          id: check.id,
          passed: 0,
          total: 0,
          last_details: "",
        });
      }
      const stat = checkStats.get(check.id);
      stat.total += 1;
      if (check.passed) {
        stat.passed += 1;
      }
      stat.last_details = check.details;
    }
  }

  return {
    skill_name: skillName,
    eval_name: evalEntry.eval_name,
    eval_metadata: extractEvalMetadata(evalEntry),
    trial_count: trials.length,
    judge_status_counts: {
      Pass: judgeStatuses.filter((status) => status === "Pass").length,
      Partial: judgeStatuses.filter((status) => status === "Partial").length,
      Fail: judgeStatuses.filter((status) => status === "Fail").length,
    },
    combined_status_counts: {
      Pass: combinedStatuses.filter((status) => status === "Pass").length,
      Partial: combinedStatuses.filter((status) => status === "Partial").length,
      Fail: combinedStatuses.filter((status) => status === "Fail").length,
    },
    benchmark_summary: {
      llm_worst_status: worstStatus(judgeStatuses),
      combined_worst_status: worstStatus(combinedStatuses),
      deterministic_pass_rate: Number((deterministicPassCount / trials.length).toFixed(2)),
    },
    trial_summaries: trials.map((trial, index) => ({
      trial: index + 1,
      llm_status: trial.report.overall_status,
      combined_status: trial.summary.combined_status,
      deterministic_pass: trial.deterministic_checks.overall_pass,
      failed_deterministic_checks: trial.deterministic_checks.checks
        .filter((check) => !check.passed)
        .map((check) => check.id),
      timing_ms: trial.timing.total_ms,
    })),
    timing_ms: {
      compile: summarizeNumeric(trials.map((trial) => trial.timing.compile_ms)),
      render: summarizeNumeric(trials.map((trial) => trial.timing.render_ms)),
      deterministic: summarizeNumeric(trials.map((trial) => trial.timing.deterministic_ms)),
      evaluate: summarizeNumeric(trials.map((trial) => trial.timing.evaluate_ms)),
      total: summarizeNumeric(trials.map((trial) => trial.timing.total_ms)),
    },
    deterministic_checks: [...checkStats.values()].map((stat) => ({
      id: stat.id,
      pass_rate: Number((stat.passed / stat.total).toFixed(2)),
      passed_trials: stat.passed,
      total_trials: stat.total,
      last_details: stat.last_details,
    })),
  };
}

function compareBenchmarks(left, right) {
  const leftSummary = left.benchmark_summary;
  const rightSummary = right.benchmark_summary;

  const combinedOrder = compareStatuses(
    leftSummary.combined_worst_status,
    rightSummary.combined_worst_status,
  );
  if (combinedOrder !== 0) {
    return combinedOrder;
  }

  const llmOrder = compareStatuses(leftSummary.llm_worst_status, rightSummary.llm_worst_status);
  if (llmOrder !== 0) {
    return llmOrder;
  }

  return rightSummary.deterministic_pass_rate - leftSummary.deterministic_pass_rate;
}

export function buildComparisonReport(skillName, evalEntry, variantResults, evalProfile) {
  const currentVariant = variantResults.find(
    (variantResult) => variantResult.variant.key === "current",
  );
  const rankedVariants = [...variantResults]
    .sort((left, right) => compareBenchmarks(left.benchmark, right.benchmark))
    .map((variantResult, index) => ({
      rank: index + 1,
      label: variantResult.variant.label,
      combined_worst_status: variantResult.benchmark.benchmark_summary.combined_worst_status,
      llm_worst_status: variantResult.benchmark.benchmark_summary.llm_worst_status,
      deterministic_pass_rate: variantResult.benchmark.benchmark_summary.deterministic_pass_rate,
    }));

  const currentVsBaselines = currentVariant
    ? variantResults
        .filter((variantResult) => variantResult.variant.key !== "current")
        .map((variantResult) => ({
          label: variantResult.variant.label,
          combined_worst_status_relative_to_current:
            compareStatuses(
              variantResult.benchmark.benchmark_summary.combined_worst_status,
              currentVariant.benchmark.benchmark_summary.combined_worst_status,
            ) < 0
              ? "better"
              : compareStatuses(
                    variantResult.benchmark.benchmark_summary.combined_worst_status,
                    currentVariant.benchmark.benchmark_summary.combined_worst_status,
                  ) > 0
                ? "worse"
                : "same",
          llm_worst_status_relative_to_current:
            compareStatuses(
              variantResult.benchmark.benchmark_summary.llm_worst_status,
              currentVariant.benchmark.benchmark_summary.llm_worst_status,
            ) < 0
              ? "better"
              : compareStatuses(
                    variantResult.benchmark.benchmark_summary.llm_worst_status,
                    currentVariant.benchmark.benchmark_summary.llm_worst_status,
                  ) > 0
                ? "worse"
                : "same",
          deterministic_pass_rate_delta: Number(
            (
              variantResult.benchmark.benchmark_summary.deterministic_pass_rate -
              currentVariant.benchmark.benchmark_summary.deterministic_pass_rate
            ).toFixed(2),
          ),
        }))
    : [];

  return {
    skill_name: skillName,
    eval_name: evalEntry.eval_name,
    trial_count: variantResults[0]?.benchmark.trial_count ?? 0,
    judge_variant: "current",
    eval_profile: summarizeEvalProfile(evalProfile),
    eval_metadata: extractEvalMetadata(evalEntry),
    variants: variantResults.map((variantResult) => ({
      label: variantResult.variant.label,
      source: variantResult.variant.source,
      run_subdir: variantResult.run_subdir,
      benchmark_summary: variantResult.benchmark.benchmark_summary,
      judge_status_counts: variantResult.benchmark.judge_status_counts,
      combined_status_counts: variantResult.benchmark.combined_status_counts,
      timing_ms: variantResult.benchmark.timing_ms,
    })),
    ranking: rankedVariants,
    current_vs_baselines: currentVsBaselines,
  };
}

export function buildSuiteSummary({
  skillName,
  evalProfile,
  trials,
  compareMode,
  suiteResults,
  suiteDir,
}) {
  const failingResults = suiteResults.filter(
    (result) => result.current_summary.combined_worst_status !== "Pass",
  );

  return {
    skill_name: skillName,
    eval_profile: summarizeEvalProfile(evalProfile),
    trial_count: trials,
    compare_mode: compareMode,
    eval_count: suiteResults.length,
    pass_count: suiteResults.length - failingResults.length,
    non_pass_count: failingResults.length,
    results: suiteResults.map((result) => ({
      eval_name: result.eval_name,
      run_dir: path.relative(suiteDir, result.run_dir).split(path.sep).join("/"),
      llm_worst_status: result.current_summary.llm_worst_status,
      combined_worst_status: result.current_summary.combined_worst_status,
      deterministic_pass_rate: result.current_summary.deterministic_pass_rate,
      error: result.error ?? null,
    })),
  };
}
