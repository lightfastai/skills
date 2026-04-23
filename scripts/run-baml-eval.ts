import { rm } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { resolveCandidateDocumentPath } from "./evals/artifacts.ts";
import {
  ensureFreshClient,
  importGeneratedClient,
} from "./evals/baml.ts";
import { parseArgs } from "./evals/cli.ts";
import {
  buildEvalPacket,
  getEvalEntriesBySelector,
  loadEvalManifest,
} from "./evals/manifest.ts";
import { getGitMetadata } from "./evals/git.ts";
import { normalizeCompiledBriefForRender } from "./evals/normalization.ts";
import { getEvalProfilePreset } from "./evals/profiles.ts";
import { createReporterSet } from "./evals/reporters.ts";
import {
  buildBenchmark,
  buildComparisonReport,
  buildSuiteSummary,
} from "./evals/reports.ts";
import { fail, loadText } from "./evals/runtime.ts";
import { worstStatus } from "./evals/status.ts";
import { runDeterministicChecks } from "./evals/validators/index.ts";
import {
  buildVariantPlan,
  materializeVariantSkillRoot,
  parseVariantSpec,
  sameStringArray,
  slugifyVariantLabel,
} from "./evals/variants.ts";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..");

async function runSingleTrial({
  evalEntry,
  evalsDir,
  candidateGenerated,
  judgeGenerated,
  runner,
  skillName,
  skillRoot,
  validationContract,
}) {
  const { b: candidateClient } = candidateGenerated;
  const { b: judgeClient } = judgeGenerated;
  const packet = await buildEvalPacket(evalEntry, evalsDir, runner.packet_type);
  const compileFnName = runner.compile_brief_function;
  const renderFnName = runner.render_document_function;
  const evaluateFnName = runner.evaluate_document_function;

  if (
    typeof candidateClient[compileFnName] !== "function" ||
    typeof candidateClient[renderFnName] !== "function"
  ) {
    fail(
      `Generated client is missing one or more compile/render runner functions for '${path.basename(skillRoot)}'.`,
    );
  }

  if (typeof judgeClient[evaluateFnName] !== "function") {
    fail(
      `Judge client is missing evaluate runner function '${evaluateFnName}' for '${path.basename(skillRoot)}'.`,
    );
  }

  const timing: Record<string, number> = {};
  const startedAt = Date.now();

  const compileStartedAt = Date.now();
  const compiledBrief = await candidateClient[compileFnName](packet);
  timing.compile_ms = Date.now() - compileStartedAt;

  const { brief, normalization } = normalizeCompiledBriefForRender({
    skillName,
    packetType: runner.packet_type,
    brief: compiledBrief,
    packet,
  });

  if (runner.packet_type === "SpecEvalPacket") {
    brief.update_request = packet.task_prompt;
    if (packet.existing_spec) {
      brief.existing_spec = packet.existing_spec;
    }
  }

  if (runner.packet_type === "FoundationEvalPacket") {
    brief.update_request = packet.task_prompt;
    if (packet.existing_foundation) {
      brief.existing_foundation = packet.existing_foundation;
    }
  }

  const renderStartedAt = Date.now();
  const candidateDocument = await candidateClient[renderFnName](brief);
  timing.render_ms = Date.now() - renderStartedAt;

  const deterministicStartedAt = Date.now();
  const deterministic_checks = await runDeterministicChecks(
    skillRoot,
    validationContract,
    candidateDocument,
    packet,
  );
  timing.deterministic_ms = Date.now() - deterministicStartedAt;

  const evaluateStartedAt = Date.now();
  const report = await judgeClient[evaluateFnName](packet, candidateDocument);
  timing.evaluate_ms = Date.now() - evaluateStartedAt;
  timing.total_ms = Date.now() - startedAt;

  const combined_status =
    deterministic_checks.enabled && !deterministic_checks.overall_pass
      ? worstStatus([report.overall_status, "Fail"])
      : report.overall_status;

  return {
    packet,
    brief,
    candidateDocument,
    report,
    deterministic_checks,
    normalization,
    timing,
    summary: {
      llm_status: report.overall_status,
      combined_status,
      deterministic_pass: deterministic_checks.overall_pass,
    },
  };
}

function buildTrialArtifacts(trialResult) {
  return {
    "packet.json": trialResult.packet,
    "brief.json": trialResult.brief,
    "candidate.md": trialResult.candidateDocument,
    "report.json": trialResult.report,
    "deterministic_checks.json": trialResult.deterministic_checks,
    "normalization.json": trialResult.normalization,
    "timing.json": trialResult.timing,
    "summary.json": trialResult.summary,
  };
}

function printNonPassDetails(suiteResults, suiteDir) {
  const nonPassResults = suiteResults.filter(
    (result) => result.current_summary.combined_worst_status !== "Pass",
  );

  if (nonPassResults.length === 0) {
    return;
  }

  console.log("Non-pass details:");
  for (const result of nonPassResults) {
    const summary = result.current_summary;
    const artifactPath = suiteDir
      ? path.relative(suiteDir, result.run_dir).split(path.sep).join("/")
      : result.run_dir;

    console.log(
      `- ${result.eval_name}: LLM ${summary.llm_worst_status}, Combined ${summary.combined_worst_status}, Deterministic pass rate ${summary.deterministic_pass_rate}, artifacts ${artifactPath}`,
    );

    if (result.error) {
      console.log(`  error: ${result.error}`);
    }

    const failedChecks = summary.failed_deterministic_checks ?? [];
    if (failedChecks.length > 0) {
      console.log(`  failed deterministic checks: ${failedChecks.join(", ")}`);
    }

    const openIssues = summary.llm_open_issues ?? [];
    if (openIssues.length > 0) {
      console.log(`  LLM open issues: ${openIssues.join(" | ")}`);
    }
  }
}

async function runDeterministicOnlyTrial({
  candidateDocumentPath,
  evalEntry,
  evalsDir,
  runner,
  skillRoot,
  validationContract,
}) {
  const startedAt = Date.now();
  const packet = await buildEvalPacket(evalEntry, evalsDir, runner.packet_type);
  const candidateDocument = await loadText(candidateDocumentPath);

  const deterministicStartedAt = Date.now();
  const deterministic_checks = await runDeterministicChecks(
    skillRoot,
    validationContract,
    candidateDocument,
    packet,
  );

  const deterministicStatus = deterministic_checks.overall_pass ? "Pass" : "Fail";
  const timing = {
    compile_ms: 0,
    render_ms: 0,
    deterministic_ms: Date.now() - deterministicStartedAt,
    evaluate_ms: 0,
    total_ms: Date.now() - startedAt,
  };

  return {
    packet,
    brief: null,
    candidateDocument,
    report: {
      judge_skipped: true,
      overall_status: deterministicStatus,
      summary:
        "LLM judge skipped because this run used --deterministic-only against an existing candidate.md artifact.",
    },
    deterministic_checks,
    normalization: null,
    timing,
    summary: {
      llm_status: deterministicStatus,
      combined_status: deterministicStatus,
      deterministic_pass: deterministic_checks.overall_pass,
      judge_skipped: true,
    },
  };
}

async function runVariantTrials({
  artifactDir,
  candidateGenerated,
  capabilityId,
  evalEntry,
  evalsDir,
  judgeGenerated,
  reporters,
  runner,
  skillName,
  skillRoot,
  trials,
  validationContract,
  variant,
}) {
  const trialResults = [];

  for (let trialIndex = 0; trialIndex < trials; trialIndex += 1) {
    const trialResult = await runSingleTrial({
      evalEntry,
      evalsDir,
      candidateGenerated,
      judgeGenerated,
      runner,
      skillName,
      skillRoot,
      validationContract,
    });
    trialResults.push(trialResult);

    await reporters.onTrialComplete({
      artifactDir,
      evalEntry,
      trialArtifacts: buildTrialArtifacts(trialResult),
      trialIndex,
      trialResult,
      trials,
      variant,
    });
  }

  const benchmark = {
    ...buildBenchmark(skillName, evalEntry, trialResults, capabilityId),
    variant,
  };

  await reporters.onBenchmarkComplete({
    artifactDir,
    benchmark,
    evalEntry,
    trialResults,
    variant,
  });

  return {
    benchmark,
    trialResults,
  };
}

async function runDeterministicOnlyEntry({
  candidateSourcePath,
  capabilityId,
  evalEntry,
  evalProfile,
  evalsDir,
  manifestValidationContract,
  reporters,
  runDir,
  runner,
  skillName,
  skillRoot,
}) {
  const validationContract = evalEntry.validation_contract ?? manifestValidationContract ?? null;
  const variant = parseVariantSpec("current");
  const candidateDocumentPath = await resolveCandidateDocumentPath(
    candidateSourcePath,
    evalEntry.eval_name,
  );
  const trialResult = await runDeterministicOnlyTrial({
    candidateDocumentPath,
    evalEntry,
    evalsDir,
    runner,
    skillRoot,
    validationContract,
  });

  await reporters.onTrialComplete({
    artifactDir: runDir,
    evalEntry,
    trialArtifacts: {
      ...buildTrialArtifacts(trialResult),
      "source_candidate_path.txt": candidateDocumentPath,
    },
    trialIndex: 0,
    trialResult,
    trials: 1,
    variant,
  });

  const benchmark = {
    ...buildBenchmark(skillName, evalEntry, [trialResult], capabilityId),
    variant,
    deterministic_only: true,
    source_candidate_path: candidateDocumentPath,
  };

  await reporters.onBenchmarkComplete({
    artifactDir: runDir,
    benchmark,
    evalEntry,
    trialResults: [trialResult],
    variant,
  });

  console.log(`Deterministic-only run complete: ${runDir}`);
  console.log(
    `Eval profile: ${evalProfile.name} (validators only; model calls skipped)`,
  );
  console.log(`Combined status: ${benchmark.benchmark_summary.combined_worst_status}`);

  return {
    eval_name: evalEntry.eval_name,
    run_dir: runDir,
    current_summary: benchmark.benchmark_summary,
  };
}

async function runEvalEntry({
  capabilityId,
  cleanupRoots,
  compareMode,
  evalEntry,
  evalProfile,
  evalsDir,
  judgeGenerated,
  judgePrepared,
  manifestValidationContract,
  reporters,
  runDir,
  runner,
  skillName,
  skillRoot,
  trials,
  variants,
}) {
  const validationContract = evalEntry.validation_contract ?? manifestValidationContract ?? null;
  const variantResults = [];

  for (const variant of variants) {
    const currentVariantMatchesJudge =
      variant.kind === "current" &&
      sameStringArray(evalProfile.candidateOverlayProfiles, evalProfile.judgeOverlayProfiles);

    let preparedVariant = judgePrepared;
    let candidateGenerated = judgeGenerated;

    if (!currentVariantMatchesJudge) {
      preparedVariant = await materializeVariantSkillRoot(
        skillName,
        skillRoot,
        variant,
        evalProfile.candidateOverlayProfiles,
        repoRoot,
      );
      if (preparedVariant.cleanupRoot) {
        cleanupRoots.push(preparedVariant.cleanupRoot);
      }

      await ensureFreshClient(preparedVariant.skillRoot, repoRoot);
      candidateGenerated = await importGeneratedClient(preparedVariant.skillRoot);
    }

    const artifactDir = compareMode
      ? path.join(runDir, "variants", slugifyVariantLabel(variant.label))
      : runDir;

    const variantRun = await runVariantTrials({
      artifactDir,
      candidateGenerated,
      capabilityId,
      evalEntry,
      evalsDir,
      judgeGenerated,
      reporters,
      runner,
      skillName,
      skillRoot,
      trials,
      validationContract,
      variant,
    });

    variantResults.push({
      variant,
      benchmark: variantRun.benchmark,
      run_subdir: path.relative(runDir, artifactDir).split(path.sep).join("/"),
    });
  }

  const currentVariant =
    variantResults.find((variantResult) => variantResult.variant.key === "current") ??
    variantResults[0];

  if (compareMode) {
    const comparison = buildComparisonReport(
      skillName,
      evalEntry,
      variantResults,
      evalProfile,
      capabilityId,
    );
    await reporters.onComparisonComplete({
      runDir,
      comparison,
      evalEntry,
      variantResults,
    });

    console.log(`Run complete: ${runDir}`);
    console.log(
      `Eval profile: ${evalProfile.name} (candidate ${evalProfile.candidateModel}, judge ${evalProfile.judgeModel})`,
    );
    console.log(`Trials per variant: ${trials}`);
    for (const variantResult of variantResults) {
      console.log(
        `${variantResult.variant.label}: LLM ${variantResult.benchmark.benchmark_summary.llm_worst_status}, Combined ${variantResult.benchmark.benchmark_summary.combined_worst_status}, Deterministic ${variantResult.benchmark.benchmark_summary.deterministic_pass_rate}`,
      );
    }

    return {
      eval_name: evalEntry.eval_name,
      run_dir: runDir,
      current_summary: currentVariant.benchmark.benchmark_summary,
      comparison,
      variants: variantResults.map((variantResult) => ({
        label: variantResult.variant.label,
        run_subdir: variantResult.run_subdir,
        benchmark_summary: variantResult.benchmark.benchmark_summary,
      })),
    };
  }

  const benchmark = currentVariant.benchmark;
  console.log(`Run complete: ${runDir}`);
  console.log(
    `Eval profile: ${evalProfile.name} (candidate ${evalProfile.candidateModel}, judge ${evalProfile.judgeModel})`,
  );
  console.log(`Trials: ${trials}`);
  console.log(`LLM worst status: ${benchmark.benchmark_summary.llm_worst_status}`);
  console.log(`Combined worst status: ${benchmark.benchmark_summary.combined_worst_status}`);

  return {
    eval_name: evalEntry.eval_name,
    run_dir: runDir,
    current_summary: benchmark.benchmark_summary,
  };
}

async function main() {
  const {
    skillName,
    selector,
    trials,
    compare,
    evalProfile: evalProfileName,
    runAll,
    runSmoke,
    deterministicOnlyPath,
    reporters: reporterNames,
  } = parseArgs(process.argv.slice(2));

  if (!skillName) {
    fail(
      "Usage: bun run ./scripts/run-baml-eval.ts <foundation-creator|spec-creator> [eval-id-or-name] [--all|--smoke] [--trials N] [--compare previous,profile:no-skill] [--eval-profile fast|gate|prod|cross] [--deterministic-only path] [--reporter local,braintrust]",
    );
  }

  const deterministicOnly = Boolean(deterministicOnlyPath);
  if (deterministicOnly && compare.length > 0) {
    fail("--deterministic-only does not support --compare.");
  }
  if (deterministicOnly && trials !== 1) {
    fail("--deterministic-only validates one existing candidate artifact per eval; omit --trials.");
  }

  const skillRoot = path.join(repoRoot, "skills", skillName);
  const evalsDir = path.join(skillRoot, "evals");
  const manifest = await loadEvalManifest(evalsDir, skillName);
  const capabilityId = manifest.capability_id ?? skillName;
  const evalEntries = getEvalEntriesBySelector(manifest.evals, selector, runAll, runSmoke);
  const variants = deterministicOnly ? [parseVariantSpec("current")] : buildVariantPlan(compare);
  const compareMode = !deterministicOnly && (compare.length > 0 || variants.length > 1);
  const evalProfile = getEvalProfilePreset(evalProfileName);
  const runner = manifest.runner_contract;
  const manifestValidationContract = manifest.validation_contract ?? null;

  if (!deterministicOnly && !process.env.AI_GATEWAY_API_KEY) {
    fail("AI_GATEWAY_API_KEY is required to execute BAML evals.");
  }

  const startedAt = new Date();
  const startedAtIso = startedAt.toISOString();
  const timestamp = startedAtIso.replace(/[:.]/g, "-");
  const git = await getGitMetadata(repoRoot);
  const runSuite = runAll || runSmoke;
  const suiteMode = runAll ? "all" : runSmoke ? "smoke" : "single";
  const suiteDir = runSuite
    ? path.join(
        skillRoot,
        "evals",
        "runs",
        `${timestamp}-${runSmoke ? "smoke" : "suite"}`,
      )
    : null;
  const reporters = await createReporterSet(reporterNames, {
    skillName,
    capabilityId,
    evalProfile,
    timestamp,
    startedAtIso,
    suiteMode,
    runSuite,
    runSmoke,
    deterministicOnly,
    compareMode,
    git,
  });
  const cleanupRoots = [];

  let judgePrepared = null;
  let judgeGenerated = null;
  if (!deterministicOnly) {
    judgePrepared = await materializeVariantSkillRoot(
      skillName,
      skillRoot,
      parseVariantSpec("current"),
      evalProfile.judgeOverlayProfiles,
      repoRoot,
    );
    if (judgePrepared.cleanupRoot) {
      cleanupRoots.push(judgePrepared.cleanupRoot);
    }

    await ensureFreshClient(judgePrepared.skillRoot, repoRoot);
    judgeGenerated = await importGeneratedClient(judgePrepared.skillRoot);
  }

  try {
    const suiteResults = [];

    for (const [index, evalEntry] of evalEntries.entries()) {
      if (runSuite) {
        console.log(`\n=== ${index + 1}/${evalEntries.length}: ${evalEntry.eval_name} ===`);
      }

      const runDir = runSuite
        ? path.join(suiteDir, evalEntry.eval_name)
        : path.join(skillRoot, "evals", "runs", `${timestamp}-${evalEntry.eval_name}`);

      try {
        const evalResult = deterministicOnly
          ? await runDeterministicOnlyEntry({
              candidateSourcePath: deterministicOnlyPath,
              capabilityId,
              evalEntry,
              evalProfile,
              evalsDir,
              manifestValidationContract,
              reporters,
              runDir,
              runner,
              skillName,
              skillRoot,
            })
          : await runEvalEntry({
              capabilityId,
              cleanupRoots,
              compareMode,
              evalEntry,
              evalProfile,
              evalsDir,
              judgeGenerated,
              judgePrepared,
              manifestValidationContract,
              reporters,
              runDir,
              runner,
              skillName,
              skillRoot,
              trials,
              variants,
            });

        suiteResults.push(evalResult);
        if (!runSuite && evalResult.current_summary.combined_worst_status !== "Pass") {
          printNonPassDetails([evalResult], null);
          process.exitCode = 1;
        }
      } catch (error) {
        if (!runSuite) {
          throw error;
        }

        const message = error instanceof Error ? error.message : String(error);
        console.error(`Eval failed: ${evalEntry.eval_name}`);
        console.error(message);

        await reporters.onError({
          runDir,
          errorArtifact: {
            eval_name: evalEntry.eval_name,
            message,
          },
        });

        suiteResults.push({
          eval_name: evalEntry.eval_name,
          run_dir: runDir,
          error: message,
          current_summary: {
            llm_worst_status: "Fail",
            combined_worst_status: "Fail",
            deterministic_pass_rate: 0,
            failed_deterministic_checks: [],
            llm_open_issues: [],
          },
        });
      }
    }

    if (runSuite) {
      const suiteSummary = buildSuiteSummary({
        skillName,
        capabilityId,
        evalProfile,
        trials,
        compareMode,
        deterministicOnly,
        suiteMode,
        suiteResults,
        suiteDir,
      });

      await reporters.onSuiteComplete({
        suiteDir,
        suiteSummary,
      });

      console.log(`\nSuite complete: ${suiteDir}`);
      console.log(`Evals: ${suiteResults.length}`);
      console.log(`Non-pass evals: ${suiteSummary.non_pass_count}`);
      printNonPassDetails(suiteResults, suiteDir);

      if (suiteSummary.non_pass_count > 0) {
        process.exitCode = 1;
      }
    }
  } finally {
    try {
      await reporters.close();
    } finally {
      await Promise.all(
        cleanupRoots.map((cleanupRoot) => rm(cleanupRoot, { recursive: true, force: true })),
      );
    }
  }
}

main().catch((error) => {
  console.error(error instanceof Error ? error.message : String(error));
  process.exit(1);
});
