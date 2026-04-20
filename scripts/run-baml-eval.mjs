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

function stripLeadingSectionNumber(heading) {
  return heading.replace(/^\d+(?:\.\d+)*\.?\s+/, "").trim();
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

function extractNonEmptyNormalizedLines(text) {
  return text
    .split(/\r?\n/)
    .map((line) => normalizeLine(line))
    .filter((line) => line.length > 0);
}

function linesAppearInOrder(needleLines, haystackLines) {
  let needleIndex = 0;

  for (const line of haystackLines) {
    if (needleIndex >= needleLines.length) {
      break;
    }
    if (line === needleLines[needleIndex]) {
      needleIndex += 1;
    }
  }

  return needleIndex === needleLines.length;
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
  const existingFoundationPath = packetFiles.existing_foundation
    ? path.join(evalsDir, packetFiles.existing_foundation)
    : null;

  const packet = {
    packet_name: evalEntry.eval_name,
    task_prompt: evalEntry.prompt,
    raw_notes: rawNotesPath ? await loadText(rawNotesPath) : evalEntry.prompt,
    expected_criteria: expectedCriteriaPath
      ? await loadText(expectedCriteriaPath)
      : (evalEntry.expected_output ?? ""),
  };

  if (packetType === "SpecEvalPacket") {
    packet.existing_spec = existingSpecPath ? await loadText(existingSpecPath) : null;
  }

  if (packetType === "FoundationEvalPacket") {
    packet.existing_foundation = existingFoundationPath
      ? await loadText(existingFoundationPath)
      : null;
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

function extractFoundationSectionBodies(candidateDocument) {
  const lines = candidateDocument.split(/\r?\n/);
  const sections = [];

  for (const [index, rawLine] of lines.entries()) {
    const match = rawLine.match(/^\s*##\s+(.+?)\s*$/);
    if (match) {
      sections.push({
        title: normalizeLine(match[1]),
        index,
      });
    }
  }

  const bodies = new Map();
  for (let index = 0; index < sections.length; index += 1) {
    const current = sections[index];
    const next = sections[index + 1];
    const start = current.index + 1;
    const end = next ? next.index : lines.length;
    bodies.set(current.title, lines.slice(start, end).join("\n").trim());
  }

  return {
    lines,
    sections,
    bodies,
  };
}

function extractMarkdownBullets(sectionBody) {
  const bullets = [];
  let current = null;

  for (const rawLine of sectionBody.split(/\r?\n/)) {
    if (/^\s*-\s+/.test(rawLine)) {
      if (current) {
        bullets.push(current);
      }
      current = normalizeLine(rawLine.replace(/^\s*-\s+/, ""));
      continue;
    }

    const line = normalizeLine(rawLine);
    if (!current || line.length === 0) {
      continue;
    }

    current = `${current} ${line}`.trim();
  }

  if (current) {
    bullets.push(current);
  }

  return bullets;
}

function validateFoundationDocument(candidateDocument, templateText) {
  const requiredSections = extractFoundationTemplateSections(templateText);
  const disallowedHeadings = extractFoundationDisallowedHeadings(templateText);
  const { lines, sections, bodies } = extractFoundationSectionBodies(candidateDocument);
  const titleLine = lines.find((line) => normalizeLine(line).length > 0) ?? "";
  const hasMarkdownTitle = /^\s*#\s+.+\s+Foundation\s*$/.test(titleLine);
  const lineMap = new Map();

  for (const { title, index } of sections) {
    const line = normalizeLine(title);
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
    const sectionBody = bodies.get(current.section) ?? "";
    if (!sectionBody) {
      emptySections.push(current.section);
    }
  }

  const presentDisallowedSections = [...disallowedHeadings].filter((section) =>
    (lineMap.get(section) ?? []).length > 0,
  );
  const strategicBetsBody = bodies.get("Strategic Bets") ?? "";
  const openQuestionsBody = bodies.get("Open Questions") ?? "";
  const openQuestionBullets = extractMarkdownBullets(openQuestionsBody);
  const openQuestionsLookOpen =
    openQuestionBullets.length > 0 &&
    openQuestionBullets.every((line) => line.endsWith("?"));
  const strategicBetLines = extractMarkdownBullets(strategicBetsBody);
  const strategicBetsBodyHasDirectionalPreamble = /\b(observed directional bets|public signals)\b/i.test(
    strategicBetsBody,
  );
  const hedgedStrategicBets =
    strategicBetLines.length === 0 ||
    strategicBetLines.every((line) =>
      /^Bet:/i.test(line)
        ? strategicBetsBodyHasDirectionalPreamble
        : /\b(appears?|suggests?|signals?|signaling|indicates?|indicating|directional bet|directional bets|observed bet|observed bets|a bet that|bet that|bet on)\b/i.test(
            line,
          ),
    );

  return [
    createCheck(
      "title_heading_present",
      hasMarkdownTitle,
      hasMarkdownTitle
        ? "Detected the required markdown title heading."
        : "Missing required title heading like `# <Primitive Name> Foundation`.",
    ),
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
      "strategic_bets_use_directional_language",
      hedgedStrategicBets,
      hedgedStrategicBets
        ? "Strategic Bets are framed as directional bets or observed signals."
        : "One or more Strategic Bets bullets read as settled conclusions instead of directional bets or observed signals.",
    ),
    createCheck(
      "open_questions_remain_questions",
      openQuestionsLookOpen,
      openQuestionsLookOpen
        ? "Open Questions are written as explicit unanswered questions."
        : "Open Questions should be bullet questions that remain open and usually end with `?`.",
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

function validateFoundationUpdateDocument(
  candidateDocument,
  existingFoundationText,
  templateText,
  validationContract,
) {
  const baseChecks = validateFoundationDocument(candidateDocument, templateText);
  const existingLines = extractNonEmptyNormalizedLines(existingFoundationText);
  const candidateLines = extractNonEmptyNormalizedLines(candidateDocument);
  const normalizedCandidate = normalizeLine(candidateDocument);
  const preservesExistingContent = linesAppearInOrder(existingLines, candidateLines);
  const requiredPatternChecks = (validationContract.required_patterns ?? []).map((patternCheck) => {
    const expression = new RegExp(patternCheck.pattern, patternCheck.flags ?? "i");
    const passed = expression.test(normalizedCandidate);

    return createCheck(
      patternCheck.id,
      passed,
      passed ? patternCheck.details_pass : patternCheck.details_fail,
    );
  });

  return [
    ...baseChecks,
    createCheck(
      "existing_content_preserved_in_order",
      preservesExistingContent,
      preservesExistingContent
        ? "All non-empty lines from the existing foundation appear in order in the candidate."
        : "One or more non-empty lines from the existing foundation were removed or reordered.",
    ),
    ...requiredPatternChecks,
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
    (section) =>
      !lineExists(
        lines,
        (line) => stripLeadingSectionNumber(line).toLowerCase() === section.toLowerCase(),
      ),
  );

  const hasStatusLine = lines.some((line) => /^\s*Status:\s+\S+/.test(line));
  const hasPurposeLine = lines.some((line) => /^\s*Purpose:\s+\S+/.test(line));
  const hasProblemStatement = lineExists(lines, (line) => line === "1. Problem Statement");
  const hasGoalSubsections =
    lineExists(lines, (line) => line === "2.1 Goals") &&
    lineExists(lines, (line) => line === "2.2 Non-Goals");
  const hasImportantBoundaryBlock = /(^|\n)Important boundary:\s*\n/m.test(candidateDocument);
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
      "status_line_present",
      hasStatusLine,
      hasStatusLine
        ? "Status line is present."
        : "Status line is missing or malformed.",
    ),
    createCheck(
      "purpose_line_present",
      hasPurposeLine,
      hasPurposeLine
        ? "Purpose line is present."
        : "Purpose line is missing or malformed.",
    ),
    createCheck(
      "problem_statement_present",
      hasProblemStatement,
      hasProblemStatement
        ? "Problem Statement major section is present."
        : "Problem Statement major section is missing.",
    ),
    createCheck(
      "goals_subsections_present",
      hasGoalSubsections,
      hasGoalSubsections
        ? "Detected `2.1 Goals` and `2.2 Non-Goals` subsections."
        : "Missing one or both of the required goals subsections: `2.1 Goals`, `2.2 Non-Goals`.",
    ),
    createCheck(
      "important_boundary_block_present",
      hasImportantBoundaryBlock,
      hasImportantBoundaryBlock
        ? "Detected an `Important boundary:` block inside the document."
        : "Did not detect the required `Important boundary:` block.",
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

function validateSpecUpdateDocument(candidateDocument, existingSpecText) {
  const existingLines = extractNonEmptyNormalizedLines(existingSpecText);
  const candidateLines = extractNonEmptyNormalizedLines(candidateDocument);
  const preservesExistingContent = linesAppearInOrder(existingLines, candidateLines);
  const hasOffsetStoreComponent = /^\s*4\.\s+`Offset Store`/m.test(candidateDocument);
  const hasCrossRegionNonGoal =
    /(^|\n)-\s+(Cross-region log replication\.|Replicating logs across regions\.)/mi.test(
      candidateDocument,
    );

  return [
    createCheck(
      "existing_content_preserved_in_order",
      preservesExistingContent,
      preservesExistingContent
        ? "All non-empty lines from the existing spec appear in order in the candidate."
        : "One or more non-empty lines from the existing spec were removed or reordered.",
    ),
    createCheck(
      "offset_store_component_present",
      hasOffsetStoreComponent,
      hasOffsetStoreComponent
        ? "Detected numbered component `4. `Offset Store``."
        : "Did not detect numbered component `4. `Offset Store``.",
    ),
    createCheck(
      "cross_region_nongoal_present",
      hasCrossRegionNonGoal,
      hasCrossRegionNonGoal
        ? "Detected the requested cross-region replication non-goal."
        : "Did not detect the requested cross-region replication non-goal.",
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

  const templatePath = validationContract.template_file
    ? path.join(skillRoot, validationContract.template_file)
    : null;
  const languagePath = validationContract.language_file
    ? path.join(skillRoot, validationContract.language_file)
    : null;
  const existingSpecPath = validationContract.existing_spec_file
    ? path.join(skillRoot, validationContract.existing_spec_file)
    : null;
  const existingFoundationPath = validationContract.existing_foundation_file
    ? path.join(skillRoot, validationContract.existing_foundation_file)
    : null;
  const [templateText, languageText, existingSpecText, existingFoundationText] = await Promise.all([
    validationContract.template_file ? loadText(templatePath) : Promise.resolve(""),
    languagePath ? loadText(languagePath) : Promise.resolve(""),
    existingSpecPath ? loadText(existingSpecPath) : Promise.resolve(""),
    existingFoundationPath ? loadText(existingFoundationPath) : Promise.resolve(""),
  ]);

  let checks;
  switch (validationContract.validator) {
    case "foundation-v1":
      checks = validateFoundationDocument(candidateDocument, templateText, languageText);
      break;
    case "foundation-update-v1":
      checks = validateFoundationUpdateDocument(
        candidateDocument,
        existingFoundationText,
        templateText,
        validationContract,
      );
      break;
    case "spec-v1":
      checks = validateSpecDocument(candidateDocument, templateText, languageText);
      break;
    case "spec-update-v1":
      checks = validateSpecUpdateDocument(candidateDocument, existingSpecText, languageText);
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

function extractEvalMetadata(evalEntry) {
  const fields = [
    "scenario_type",
    "input_shape",
    "ambiguity_level",
    "domain_profile",
    "primary_risks",
  ];

  return Object.fromEntries(
    fields
      .filter((field) => evalEntry[field] !== undefined)
      .map((field) => [field, evalEntry[field]]),
  );
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
  const validationContract = evalEntry.validation_contract ?? manifest.validation_contract ?? null;

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

  const benchmark = {
    ...buildBenchmark(skillName, evalEntry.eval_name, trialResults),
    eval_metadata: extractEvalMetadata(evalEntry),
  };
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
