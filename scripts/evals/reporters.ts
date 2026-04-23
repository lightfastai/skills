import path from "node:path";
import { writeArtifacts } from "./artifacts.ts";
import { extractEvalMetadata } from "./manifest.ts";
import { fail } from "./runtime.ts";

function uniqueReporterNames(names) {
  const requested = names.length > 0 ? names : ["local"];
  const normalized = requested.map((name) => name.trim()).filter(Boolean);
  if (!normalized.includes("local")) {
    normalized.unshift("local");
  }
  return [...new Set(normalized)];
}

function statusScore(status) {
  switch (status) {
    case "Pass":
      return 1;
    case "Partial":
      return 0.5;
    case "Fail":
      return 0;
    default:
      return null;
  }
}

function slugSegment(value) {
  return String(value)
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

function compactTimestamp(isoTimestamp) {
  const date = new Date(isoTimestamp);
  if (Number.isNaN(date.getTime())) {
    return slugSegment(isoTimestamp).slice(0, 20) || "unknown-time";
  }

  const yyyy = String(date.getUTCFullYear());
  const mm = String(date.getUTCMonth() + 1).padStart(2, "0");
  const dd = String(date.getUTCDate()).padStart(2, "0");
  const hh = String(date.getUTCHours()).padStart(2, "0");
  const min = String(date.getUTCMinutes()).padStart(2, "0");
  return `${yyyy}${mm}${dd}-${hh}${min}`;
}

function buildExperimentName(context) {
  if (process.env.BRAINTRUST_EXPERIMENT) {
    return process.env.BRAINTRUST_EXPERIMENT;
  }

  const capability = slugSegment(context.capabilityId);
  const mode = context.compareMode ? "compare" : context.suiteMode;
  const runKind = context.deterministicOnly ? "deterministic" : "model";
  const timestamp = compactTimestamp(context.startedAtIso);
  const shortSha = slugSegment(context.git?.short_sha ?? "unknown");

  return [capability, mode, context.evalProfile.name, runKind, timestamp, shortSha].join(".");
}

function createLocalJsonReporter() {
  return {
    name: "local",
    async onTrialComplete({ artifactDir, trialArtifacts, trialIndex, trials }) {
      const trialDir =
        trials === 1 ? artifactDir : path.join(artifactDir, `trial-${trialIndex + 1}`);
      await writeArtifacts(trialDir, trialArtifacts);
    },
    async onBenchmarkComplete({ artifactDir, benchmark }) {
      await writeArtifacts(artifactDir, {
        "benchmark.json": benchmark,
      });
    },
    async onComparisonComplete({ runDir, comparison }) {
      await writeArtifacts(runDir, {
        "comparison.json": comparison,
      });
    },
    async onSuiteComplete({ suiteDir, suiteSummary }) {
      await writeArtifacts(suiteDir, {
        "suite.json": suiteSummary,
      });
    },
    async onError({ runDir, errorArtifact }) {
      await writeArtifacts(runDir, {
        "error.json": errorArtifact,
      });
    },
  };
}

async function createBraintrustReporter(context) {
  if (!process.env.BRAINTRUST_API_KEY) {
    fail("BRAINTRUST_API_KEY is required when using --reporter braintrust.");
  }

  const { init } = await import("braintrust");
  const project = process.env.BRAINTRUST_PROJECT ?? "lightfast-skills";
  const experiment = buildExperimentName(context);
  const tags = [
    "skills-eval",
    context.capabilityId,
    context.skillName,
    context.suiteMode,
    context.evalProfile.name,
    context.deterministicOnly ? "deterministic-only" : "model-backed",
  ];

  const braintrustExperiment = init({
    project,
    experiment,
    apiKey: process.env.BRAINTRUST_API_KEY,
    orgName: process.env.BRAINTRUST_ORG || undefined,
    metadata: {
      capability_id: context.capabilityId,
      skill_name: context.skillName,
      eval_profile: context.evalProfile,
      started_at: context.startedAtIso,
      suite_mode: context.suiteMode,
      run_suite: context.runSuite,
      smoke: context.runSmoke,
      deterministic_only: context.deterministicOnly,
      compare_mode: context.compareMode,
      git: context.git,
    },
    tags,
  });
  let finalizedSummary = null;

  async function finalizeExperiment() {
    if (finalizedSummary) {
      return finalizedSummary;
    }

    await braintrustExperiment.flush();
    const summary = await braintrustExperiment.summarize();
    finalizedSummary = {
      project,
      experiment,
      experiment_name: summary.experimentName ?? experiment,
      experiment_url: summary.experimentUrl ?? null,
    };

    console.log(
      `Braintrust experiment: ${finalizedSummary.experiment_url ?? finalizedSummary.experiment_name}`,
    );

    return finalizedSummary;
  }

  return {
    name: "braintrust",
    async onTrialComplete({ evalEntry, trialResult, trialIndex, trials, variant, artifactDir }) {
      braintrustExperiment.log({
        id: `${evalEntry.eval_name}:${variant.label}:trial-${trialIndex + 1}`,
        input: {
          skill_name: context.skillName,
          capability_id: context.capabilityId,
          eval_name: evalEntry.eval_name,
          eval_id: evalEntry.id,
          prompt: evalEntry.prompt,
          packet: trialResult.packet,
          variant: variant.label,
          trial: trialIndex + 1,
          trial_count: trials,
        },
        output: {
          candidate_document: trialResult.candidateDocument,
        },
        expected: {
          criteria: trialResult.packet.expected_criteria,
          expected_output: evalEntry.expected_output ?? null,
        },
        scores: {
          llm_status: statusScore(trialResult.summary.llm_status),
          combined_status: statusScore(trialResult.summary.combined_status),
          deterministic_pass: trialResult.deterministic_checks.overall_pass ? 1 : 0,
        },
        metadata: {
          eval_metadata: extractEvalMetadata(evalEntry),
          capability_id: context.capabilityId,
          skill_name: context.skillName,
          eval_profile: context.evalProfile,
          suite_mode: context.suiteMode,
          run_kind: context.deterministicOnly ? "deterministic" : "model",
          git: context.git,
          artifact_dir: artifactDir,
          brief: trialResult.brief,
          report: trialResult.report,
          deterministic_checks: trialResult.deterministic_checks,
          normalization: trialResult.normalization,
          summary: trialResult.summary,
          judge_skipped: Boolean(trialResult.report?.judge_skipped),
        },
        metrics: trialResult.timing,
        tags,
      });
    },
    async onSuiteComplete() {
      return await finalizeExperiment();
    },
    async close() {
      await finalizeExperiment();
    },
  };
}

export async function createReporterSet(names, context) {
  const reporterNames = uniqueReporterNames(names);
  const reporters = [];

  for (const name of reporterNames) {
    switch (name) {
      case "local":
        reporters.push(createLocalJsonReporter());
        break;
      case "braintrust":
        reporters.push(await createBraintrustReporter(context));
        break;
      default:
        fail(`Unknown reporter '${name}'. Supported reporters: local, braintrust.`);
    }
  }

  async function emit(hook, payload) {
    for (const reporter of reporters) {
      if (typeof reporter[hook] === "function") {
        await reporter[hook](payload);
      }
    }
  }

  return {
    names: reporterNames,
    async onTrialComplete(payload) {
      await emit("onTrialComplete", payload);
    },
    async onBenchmarkComplete(payload) {
      await emit("onBenchmarkComplete", payload);
    },
    async onComparisonComplete(payload) {
      await emit("onComparisonComplete", payload);
    },
    async onSuiteComplete(payload) {
      const reporterSummaries = {};

      for (const reporter of reporters.filter((reporter) => reporter.name !== "local")) {
        if (typeof reporter.onSuiteComplete === "function") {
          const reporterSummary = await reporter.onSuiteComplete(payload);
          if (reporterSummary) {
            reporterSummaries[reporter.name] = reporterSummary;
          }
        }
      }

      const localPayload =
        Object.keys(reporterSummaries).length > 0
          ? {
              ...payload,
              suiteSummary: {
                ...payload.suiteSummary,
                reporters: reporterSummaries,
              },
            }
          : payload;

      for (const reporter of reporters.filter((reporter) => reporter.name === "local")) {
        if (typeof reporter.onSuiteComplete === "function") {
          await reporter.onSuiteComplete(localPayload);
        }
      }
    },
    async onError(payload) {
      await emit("onError", payload);
    },
    async close() {
      for (const reporter of reporters) {
        if (typeof reporter.close === "function") {
          await reporter.close();
        }
      }
    },
  };
}
