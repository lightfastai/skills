import { mkdir, readFile, rm, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { spawn } from "node:child_process";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..");

function fail(message) {
  console.error(message);
  process.exit(1);
}

const STATUS_RANK = {
  Pass: 0,
  Partial: 1,
  Fail: 2,
};

function normalizeLine(line) {
  return line.trim().replace(/\s+/g, " ");
}

function normalizeHeading(line) {
  return normalizeLine(line)
    .replace(/^#+\s*/, "")
    .replace(/\s+/g, " ")
    .trim();
}

function summarizeNumeric(values) {
  if (values.length === 0) {
    return {
      mean: 0,
      min: 0,
      max: 0,
    };
  }

  const total = values.reduce((sum, value) => sum + value, 0);
  return {
    mean: Math.round(total / values.length),
    min: Math.min(...values),
    max: Math.max(...values),
  };
}

function worstStatus(statuses) {
  return statuses.reduce((worst, current) => {
    if (!worst) {
      return current;
    }
    return STATUS_RANK[current] > STATUS_RANK[worst] ? current : worst;
  }, null);
}

function hasPronounDrift(document) {
  return /\b(we|our|ours|us|you|your|yours)\b/i.test(document);
}

function hasUppercaseObligationKeyword(document) {
  return /\b(MUST|SHOULD|MAY)\b/.test(document);
}

function runCommand(command, args, cwd) {
  return new Promise((resolve, reject) => {
    const child = spawn(command, args, {
      cwd,
      stdio: "inherit",
      env: process.env,
      shell: false,
    });

    child.on("error", reject);
    child.on("exit", (code) => {
      if (code === 0) {
        resolve();
      } else {
        reject(new Error(`${command} ${args.join(" ")} exited with code ${code}`));
      }
    });
  });
}

async function loadJson(filePath) {
  return JSON.parse(await readFile(filePath, "utf8"));
}

async function loadText(filePath) {
  return readFile(filePath, "utf8");
}

function parseArgs(argv) {
  const positionals = [];
  let trials = 1;

  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];

    if (arg === "--trials") {
      const next = argv[index + 1];
      if (!next) {
        fail("Missing value after --trials.");
      }
      trials = Number.parseInt(next, 10);
      if (!Number.isInteger(trials) || trials < 1) {
        fail("--trials must be a positive integer.");
      }
      index += 1;
      continue;
    }

    positionals.push(arg);
  }

  return {
    skillName: positionals[0],
    selector: positionals[1],
    trials,
  };
}

function getEvalBySelector(evals, selector) {
  if (!selector) {
    if (evals.length === 1) {
      return evals[0];
    }
    fail("Multiple evals exist. Pass an eval id or name.");
  }

  const numeric = Number(selector);
  if (!Number.isNaN(numeric)) {
    const byId = evals.find((entry) => entry.id === numeric);
    if (byId) {
      return byId;
    }
  }

  const byName = evals.find((entry) => entry.eval_name === selector);
  if (byName) {
    return byName;
  }

  fail(`Eval '${selector}' not found.`);
}

async function generateClient(skillRoot) {
  const bamlSrc = path.join(skillRoot, "baml_src");
  await runCommand("bunx", ["baml-cli", "generate", "--from", bamlSrc], repoRoot);
}

async function importGeneratedClient(skillRoot) {
  const clientPath = path.join(skillRoot, "baml_client_dist", "index.js");
  return import(pathToFileURL(clientPath).href);
}

async function buildPacket(evalEntry, evalsDir, packetType) {
  const packetFiles = evalEntry.packet_files ?? {};
  const rawNotesPath = packetFiles.raw_notes
    ? path.join(evalsDir, packetFiles.raw_notes)
    : null;
  const expectedCriteriaPath = packetFiles.expected_criteria
    ? path.join(evalsDir, packetFiles.expected_criteria)
    : null;
  const existingSpecPath = packetFiles.existing_spec
    ? path.join(evalsDir, packetFiles.existing_spec)
    : null;

  const packet = {
    packet_name: evalEntry.eval_name,
    task_prompt: evalEntry.prompt,
    raw_notes: rawNotesPath ? await loadText(rawNotesPath) : "",
    expected_criteria: expectedCriteriaPath ? await loadText(expectedCriteriaPath) : "",
  };

  if (packetType === "SpecEvalPacket") {
    packet.existing_spec = existingSpecPath ? await loadText(existingSpecPath) : null;
  }

  return packet;
}

async function ensureFreshClient(skillRoot) {
  const clientDir = path.join(skillRoot, "baml_client");
  const distDir = path.join(skillRoot, "baml_client_dist");
  const tsconfigPath = path.join(skillRoot, ".tmp-baml-client-tsconfig.json");
  await rm(clientDir, { recursive: true, force: true });
  await rm(distDir, { recursive: true, force: true });
  await generateClient(skillRoot);
  await writeFile(
    tsconfigPath,
    JSON.stringify(
      {
        compilerOptions: {
          module: "NodeNext",
          moduleResolution: "NodeNext",
          target: "ES2022",
          declaration: false,
          sourceMap: false,
          skipLibCheck: true,
          outDir: distDir,
          rootDir: clientDir,
        },
        include: [path.join(clientDir, "*.ts")],
      },
      null,
      2,
    ),
    "utf8",
  );
  try {
    await runCommand("bunx", ["tsc", "--project", tsconfigPath], repoRoot);
  } finally {
    await rm(tsconfigPath, { force: true });
  }
}

async function writeRunArtifacts(runDir, artifacts) {
  await mkdir(runDir, { recursive: true });
  for (const [name, value] of Object.entries(artifacts)) {
    const filePath = path.join(runDir, name);
    const content = typeof value === "string" ? value : JSON.stringify(value, null, 2);
    await writeFile(filePath, content, "utf8");
  }
}

function createCheck(id, passed, details) {
  return { id, passed, details };
}

function extractFoundationTemplateSections(templateText) {
  const sections = [];
  const lines = templateText.split(/\r?\n/);

  for (const rawLine of lines) {
    const line = normalizeLine(rawLine);
    if (line === "## Disallowed Sections") {
      break;
    }
    if (line.startsWith("## ")) {
      sections.push(line.slice(3).trim());
    }
  }

  return sections;
}

function extractFoundationDisallowedHeadings(templateText) {
  const disallowed = new Set();
  const lines = templateText.split(/\r?\n/);
  let inDisallowedSection = false;

  for (const rawLine of lines) {
    const line = normalizeLine(rawLine);
    if (line === "## Disallowed Sections") {
      inDisallowedSection = true;
      continue;
    }
    if (!inDisallowedSection) {
      continue;
    }
    const match = line.match(/^- `(.+)`$/);
    if (match) {
      disallowed.add(match[1]);
    }
  }

  return disallowed;
}

function validateFoundationDocument(candidateDocument, templateText) {
  const requiredSections = extractFoundationTemplateSections(templateText);
  const disallowedHeadings = extractFoundationDisallowedHeadings(templateText);
  const lines = candidateDocument.split(/\r?\n/);
  const lineMap = new Map();

  for (const [index, rawLine] of lines.entries()) {
    const line = normalizeHeading(rawLine);
    if (!line) {
      continue;
    }
    if (!lineMap.has(line)) {
      lineMap.set(line, []);
    }
    lineMap.get(line).push(index);
  }

  const missingSections = [];
  const duplicateSections = [];
  const positions = [];

  for (const section of requiredSections) {
    const matches = lineMap.get(section) ?? [];
    if (matches.length === 0) {
      missingSections.push(section);
      continue;
    }
    if (matches.length > 1) {
      duplicateSections.push(section);
    }
    positions.push({
      section,
      index: matches[0],
    });
  }

  const orderIsCorrect = positions.every((entry, index) => {
    if (index === 0) {
      return true;
    }
    return entry.index > positions[index - 1].index;
  });

  const emptySections = [];
  for (let index = 0; index < positions.length; index += 1) {
    const current = positions[index];
    const next = positions[index + 1];
    const start = current.index + 1;
    const end = next ? next.index : lines.length;
    const sectionBody = lines.slice(start, end).join("\n").trim();
    if (!sectionBody) {
      emptySections.push(current.section);
    }
  }

  const presentDisallowedSections = [...disallowedHeadings].filter((section) =>
    (lineMap.get(section) ?? []).length > 0,
  );

  return [
    createCheck(
      "required_sections_present_once",
      missingSections.length === 0 && duplicateSections.length === 0,
      missingSections.length === 0 && duplicateSections.length === 0
        ? `All required sections from template are present exactly once: ${requiredSections.join(", ")}.`
        : `Missing: ${missingSections.join(", ") || "none"}. Duplicate: ${duplicateSections.join(", ") || "none"}.`,
    ),
    createCheck(
      "required_sections_in_template_order",
      missingSections.length === 0 && orderIsCorrect,
      missingSections.length > 0
        ? "Section order check skipped because one or more required sections are missing."
        : orderIsCorrect
          ? "Required sections follow the template order."
          : "Required sections are present but not in template order.",
    ),
    createCheck(
      "required_sections_nonempty",
      emptySections.length === 0,
      emptySections.length === 0
        ? "Every required section has non-empty content."
        : `Empty sections: ${emptySections.join(", ")}.`,
    ),
    createCheck(
      "no_disallowed_sections",
      presentDisallowedSections.length === 0,
      presentDisallowedSections.length === 0
        ? "No disallowed downstream-planning sections were detected."
        : `Disallowed sections present: ${presentDisallowedSections.join(", ")}.`,
    ),
    createCheck(
      "no_first_or_second_person",
      !hasPronounDrift(candidateDocument),
      !hasPronounDrift(candidateDocument)
        ? "No obvious first-person or second-person pronouns detected."
        : "Detected first-person or second-person pronouns that violate the language guide.",
    ),
  ];
}

function extractSpecMajorSections(templateText) {
  const sections = [];
  const lines = templateText.split(/\r?\n/);

  for (const rawLine of lines) {
    const line = normalizeLine(rawLine);
    const match = line.match(/^## \d+\.\s+(.+)$/);
    if (match) {
      sections.push(match[1]);
    }
  }

  return sections;
}

function lineExists(lines, matcher) {
  return lines.some((line) => matcher(normalizeHeading(line)));
}

function validateSpecDocument(candidateDocument, templateText) {
  const requiredSections = extractSpecMajorSections(templateText);
  const lines = candidateDocument.split(/\r?\n/);
  const missingSections = requiredSections.filter(
    (section) => !lineExists(lines, (line) => line.toLowerCase() === section.toLowerCase()),
  );

  const hasPurpose = lineExists(lines, (line) => line === "Purpose");
  const hasProblemStatement = lineExists(
    lines,
    (line) => line.toLowerCase() === "problem statement",
  );
  const hasNumberedComponents = /^\d+\.\s+`[^`]+`/m.test(candidateDocument);
  const hasFieldFormatting = /- `[^`]+` \([^)]+\)/.test(candidateDocument);

  return [
    createCheck(
      "core_sections_present",
      missingSections.length === 0,
      missingSections.length === 0
        ? `All major template sections are present: ${requiredSections.join(", ")}.`
        : `Missing major sections: ${missingSections.join(", ")}.`,
    ),
    createCheck(
      "purpose_heading_present",
      hasPurpose,
      hasPurpose
        ? "Purpose heading is present."
        : "Purpose heading is missing.",
    ),
    createCheck(
      "problem_statement_present",
      hasProblemStatement,
      hasProblemStatement
        ? "Problem Statement heading is present."
        : "Problem Statement heading is missing.",
    ),
    createCheck(
      "component_list_uses_numbering",
      hasNumberedComponents,
      hasNumberedComponents
        ? "Detected numbered component entries in the spec."
        : "Did not detect numbered component entries like `1. `Component Name``.",
    ),
    createCheck(
      "domain_fields_use_template_shape",
      hasFieldFormatting,
      hasFieldFormatting
        ? "Detected domain-field lines using the `` `field_name` (type) `` format."
        : "Did not detect any domain-field lines using the template field format.",
    ),
    createCheck(
      "no_first_or_second_person",
      !hasPronounDrift(candidateDocument),
      !hasPronounDrift(candidateDocument)
        ? "No obvious first-person or second-person pronouns detected."
        : "Detected first-person or second-person pronouns that violate the language guide.",
    ),
    createCheck(
      "obligation_keywords_lowercase",
      !hasUppercaseObligationKeyword(candidateDocument),
      !hasUppercaseObligationKeyword(candidateDocument)
        ? "No uppercase obligation keywords detected."
        : "Detected uppercase MUST/SHOULD/MAY, which violates the language guide.",
    ),
  ];
}

async function runDeterministicChecks(skillRoot, validationContract, candidateDocument) {
  if (!validationContract || validationContract.type !== "reference_document_checks") {
    return {
      enabled: false,
      overall_pass: true,
      checks: [],
    };
  }

  const templatePath = path.join(skillRoot, validationContract.template_file);
  const languagePath = path.join(skillRoot, validationContract.language_file);
  const [templateText, languageText] = await Promise.all([
    loadText(templatePath),
    loadText(languagePath),
  ]);

  let checks;
  switch (validationContract.validator) {
    case "foundation-v1":
      checks = validateFoundationDocument(candidateDocument, templateText, languageText);
      break;
    case "spec-v1":
      checks = validateSpecDocument(candidateDocument, templateText, languageText);
      break;
    default:
      fail(`Unknown validation contract '${validationContract.validator}'.`);
  }

  return {
    enabled: true,
    validator: validationContract.validator,
    overall_pass: checks.every((check) => check.passed),
    checks,
  };
}

async function runSingleTrial({
  evalEntry,
  evalsDir,
  generated,
  runner,
  skillRoot,
  validationContract,
}) {
  const { b } = generated;
  const packet = await buildPacket(evalEntry, evalsDir, runner.packet_type);
  const compileFnName = runner.compile_brief_function;
  const renderFnName = runner.render_document_function;
  const evaluateFnName = runner.evaluate_document_function;

  if (
    typeof b[compileFnName] !== "function" ||
    typeof b[renderFnName] !== "function" ||
    typeof b[evaluateFnName] !== "function"
  ) {
    fail(`Generated client is missing one or more runner functions for '${path.basename(skillRoot)}'.`);
  }

  const timing = {};
  const startedAt = Date.now();

  const compileStartedAt = Date.now();
  const brief = await b[compileFnName](packet);
  timing.compile_ms = Date.now() - compileStartedAt;

  const renderStartedAt = Date.now();
  const candidateDocument = await b[renderFnName](brief);
  timing.render_ms = Date.now() - renderStartedAt;

  const deterministicStartedAt = Date.now();
  const deterministic_checks = await runDeterministicChecks(
    skillRoot,
    validationContract,
    candidateDocument,
  );
  timing.deterministic_ms = Date.now() - deterministicStartedAt;

  const evaluateStartedAt = Date.now();
  const report = await b[evaluateFnName](packet, candidateDocument);
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
    timing,
    summary: {
      llm_status: report.overall_status,
      combined_status,
      deterministic_pass: deterministic_checks.overall_pass,
    },
  };
}

function buildBenchmark(skillName, evalName, trials) {
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
    eval_name: evalName,
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

async function main() {
  const { skillName, selector, trials } = parseArgs(process.argv.slice(2));

  if (!skillName) {
    fail(
      "Usage: bun run ./scripts/run-baml-eval.mjs <foundation-creator|spec-creator> [eval-id-or-name] [--trials N]",
    );
  }

  const skillRoot = path.join(repoRoot, "skills", skillName);
  const evalsDir = path.join(skillRoot, "evals");
  const manifestPath = path.join(evalsDir, "evals.json");
  const manifest = await loadJson(manifestPath);
  const evalEntry = getEvalBySelector(manifest.evals, selector);
  const runner = manifest.runner_contract;
  const validationContract = manifest.validation_contract ?? null;

  if (!runner || runner.type !== "baml_pipeline") {
    fail(`Skill '${skillName}' does not declare a supported runner_contract.`);
  }

  if (!process.env.AI_GATEWAY_API_KEY) {
    fail("AI_GATEWAY_API_KEY is required to execute BAML evals.");
  }

  await ensureFreshClient(skillRoot);
  const generated = await importGeneratedClient(skillRoot);
  const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
  const runDir = path.join(skillRoot, "evals", "runs", `${timestamp}-${evalEntry.eval_name}`);
  const trialResults = [];

  for (let trialIndex = 0; trialIndex < trials; trialIndex += 1) {
    const trialResult = await runSingleTrial({
      evalEntry,
      evalsDir,
      generated,
      runner,
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
      "timing.json": trialResult.timing,
      "summary.json": trialResult.summary,
    };

    if (trials === 1) {
      await writeRunArtifacts(runDir, trialArtifacts);
    } else {
      await writeRunArtifacts(path.join(runDir, `trial-${trialIndex + 1}`), trialArtifacts);
    }
  }

  const benchmark = buildBenchmark(skillName, evalEntry.eval_name, trialResults);
  await writeRunArtifacts(runDir, {
    "benchmark.json": benchmark,
  });

  console.log(`Run complete: ${runDir}`);
  console.log(`Trials: ${trialResults.length}`);
  console.log(`LLM worst status: ${benchmark.benchmark_summary.llm_worst_status}`);
  console.log(`Combined worst status: ${benchmark.benchmark_summary.combined_worst_status}`);
}

main().catch((error) => {
  console.error(error instanceof Error ? error.message : String(error));
  process.exit(1);
});
