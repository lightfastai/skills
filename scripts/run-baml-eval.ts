import { mkdir, rm, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
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
import { normalizeCompiledBriefForRender } from "./evals/normalization.ts";
import { getEvalProfilePreset } from "./evals/profiles.ts";
import {
  buildBenchmark,
  buildComparisonReport,
  buildSuiteSummary,
} from "./evals/reports.ts";
import { fail } from "./evals/runtime.ts";
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

async function writeRunArtifacts(runDir, artifacts) {
  await mkdir(runDir, { recursive: true });
  for (const [name, value] of Object.entries(artifacts)) {
    const filePath = path.join(runDir, name);
    const content = typeof value === "string" ? value : JSON.stringify(value, null, 2);
    await writeFile(filePath, content, "utf8");
  }
}

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

  const timing = {};
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

async function runVariantTrials({
  artifactDir,
  candidateGenerated,
  evalEntry,
  evalsDir,
  judgeGenerated,
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

    const trialArtifacts = {
      "packet.json": trialResult.packet,
      "brief.json": trialResult.brief,
      "candidate.md": trialResult.candidateDocument,
      "report.json": trialResult.report,
      "deterministic_checks.json": trialResult.deterministic_checks,
      "normalization.json": trialResult.normalization,
      "timing.json": trialResult.timing,
      "summary.json": trialResult.summary,
    };

    if (trials === 1) {
      await writeRunArtifacts(artifactDir, trialArtifacts);
    } else {
      await writeRunArtifacts(path.join(artifactDir, `trial-${trialIndex + 1}`), trialArtifacts);
    }
  }

  const benchmark = {
    ...buildBenchmark(skillName, evalEntry, trialResults),
    variant,
  };

  await writeRunArtifacts(artifactDir, {
    "benchmark.json": benchmark,
  });

  return {
    benchmark,
    trialResults,
  };
}

async function runEvalEntry({
  cleanupRoots,
  compareMode,
  evalEntry,
  evalProfile,
  evalsDir,
  judgeGenerated,
  judgePrepared,
  manifestValidationContract,
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
      evalEntry,
      evalsDir,
      judgeGenerated,
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
    const comparison = buildComparisonReport(skillName, evalEntry, variantResults, evalProfile);
    await writeRunArtifacts(runDir, {
      "comparison.json": comparison,
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
  } = parseArgs(process.argv.slice(2));

  if (!skillName) {
    fail(
      "Usage: bun run ./scripts/run-baml-eval.ts <foundation-creator|spec-creator> [eval-id-or-name] [--all] [--trials N] [--compare previous,profile:no-skill] [--eval-profile fast|gate|prod|cross]",
    );
  }

  const skillRoot = path.join(repoRoot, "skills", skillName);
  const evalsDir = path.join(skillRoot, "evals");
  const manifest = await loadEvalManifest(evalsDir, skillName);
  const evalEntries = getEvalEntriesBySelector(manifest.evals, selector, runAll);
  const variants = buildVariantPlan(compare);
  const compareMode = compare.length > 0 || variants.length > 1;
  const evalProfile = getEvalProfilePreset(evalProfileName);
  const runner = manifest.runner_contract;
  const manifestValidationContract = manifest.validation_contract ?? null;

  if (!process.env.AI_GATEWAY_API_KEY) {
    fail("AI_GATEWAY_API_KEY is required to execute BAML evals.");
  }

  const cleanupRoots = [];
  const judgePrepared = await materializeVariantSkillRoot(
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
  const judgeGenerated = await importGeneratedClient(judgePrepared.skillRoot);
  const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
  const suiteDir = runAll
    ? path.join(skillRoot, "evals", "runs", `${timestamp}-suite`)
    : null;

  try {
    const suiteResults = [];

    for (const [index, evalEntry] of evalEntries.entries()) {
      if (runAll) {
        console.log(`\n=== ${index + 1}/${evalEntries.length}: ${evalEntry.eval_name} ===`);
      }

      const runDir = runAll
        ? path.join(suiteDir, evalEntry.eval_name)
        : path.join(skillRoot, "evals", "runs", `${timestamp}-${evalEntry.eval_name}`);

      try {
        const evalResult = await runEvalEntry({
          cleanupRoots,
          compareMode,
          evalEntry,
          evalProfile,
          evalsDir,
          judgeGenerated,
          judgePrepared,
          manifestValidationContract,
          runDir,
          runner,
          skillName,
          skillRoot,
          trials,
          variants,
        });

        suiteResults.push(evalResult);
      } catch (error) {
        if (!runAll) {
          throw error;
        }

        const message = error instanceof Error ? error.message : String(error);
        console.error(`Eval failed: ${evalEntry.eval_name}`);
        console.error(message);

        await writeRunArtifacts(runDir, {
          "error.json": {
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
          },
        });
      }
    }

    if (runAll) {
      const suiteSummary = buildSuiteSummary({
        skillName,
        evalProfile,
        trials,
        compareMode,
        suiteResults,
        suiteDir,
      });

      await writeRunArtifacts(suiteDir, {
        "suite.json": suiteSummary,
      });

      console.log(`\nSuite complete: ${suiteDir}`);
      console.log(`Evals: ${suiteResults.length}`);
      console.log(`Non-pass evals: ${suiteSummary.non_pass_count}`);

      if (suiteSummary.non_pass_count > 0) {
        process.exitCode = 1;
      }
    }
  } finally {
    await Promise.all(
      cleanupRoots.map((cleanupRoot) => rm(cleanupRoot, { recursive: true, force: true })),
    );
  }
}

main().catch((error) => {
  console.error(error instanceof Error ? error.message : String(error));
  process.exit(1);
});
