import { readdir, readFile, stat } from "node:fs/promises";
import path from "node:path";

const allowedPacketFileKeys = new Set([
  "raw_notes",
  "expected_criteria",
  "existing_spec",
  "existing_foundation",
]);

const allowedValidators = new Set([
  "foundation-v1",
  "foundation-update-v1",
  "spec-v1",
  "spec-update-v1",
]);

const contractFileFields = [
  "template_file",
  "language_file",
  "existing_spec_file",
  "existing_foundation_file",
];

const patternFields = [
  "allowed_removed_patterns",
  "forbidden_patterns",
  "required_patterns",
];

function issue(issues, scope, message) {
  issues.push({ scope, message });
}

async function isFile(filePath) {
  try {
    return (await stat(filePath)).isFile();
  } catch {
    return false;
  }
}

async function readJson(filePath, issues, scope) {
  try {
    return JSON.parse(await readFile(filePath, "utf8"));
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    issue(issues, scope, `Could not read JSON: ${message}`);
    return null;
  }
}

function resolveRelativeFile(baseDir, relativePath, issues, scope) {
  if (typeof relativePath !== "string" || relativePath.trim().length === 0) {
    issue(issues, scope, "File path must be a non-empty string.");
    return null;
  }

  if (path.isAbsolute(relativePath)) {
    issue(issues, scope, `File path must be relative, got '${relativePath}'.`);
    return null;
  }

  const resolved = path.resolve(baseDir, relativePath);
  const relative = path.relative(baseDir, resolved);
  if (relative.startsWith("..") || path.isAbsolute(relative)) {
    issue(issues, scope, `File path escapes its base directory: '${relativePath}'.`);
    return null;
  }

  return resolved;
}

async function checkRelativeFile(baseDir, relativePath, issues, scope) {
  const resolved = resolveRelativeFile(baseDir, relativePath, issues, scope);
  if (!resolved) {
    return;
  }

  if (!(await isFile(resolved))) {
    issue(issues, scope, `Referenced file does not exist: '${relativePath}'.`);
  }
}

function checkNonEmptyString(value, issues, scope, field) {
  if (typeof value !== "string" || value.trim().length === 0) {
    issue(issues, scope, `'${field}' must be a non-empty string.`);
  }
}

function checkStringArray(value, issues, scope, field) {
  if (value === undefined) {
    return;
  }
  if (!Array.isArray(value) || value.some((entry) => typeof entry !== "string")) {
    issue(issues, scope, `'${field}' must be an array of strings when present.`);
  }
}

function checkPatternSpec(patternSpec, issues, scope) {
  if (typeof patternSpec === "string") {
    try {
      new RegExp(patternSpec, "i");
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      issue(issues, scope, `Invalid regex pattern '${patternSpec}': ${message}`);
    }
    return;
  }

  if (!patternSpec || typeof patternSpec !== "object") {
    issue(issues, scope, "Pattern spec must be a string or object.");
    return;
  }

  if (typeof patternSpec.id !== "string" && patternSpec.id !== undefined) {
    issue(issues, scope, "Pattern spec 'id' must be a string when present.");
  }

  if (typeof patternSpec.section_title !== "string" && patternSpec.section_title !== undefined) {
    issue(issues, scope, "Pattern spec 'section_title' must be a string when present.");
  }

  if (typeof patternSpec.pattern !== "string" || patternSpec.pattern.length === 0) {
    issue(issues, scope, "Pattern spec object must declare a non-empty 'pattern'.");
    return;
  }

  try {
    new RegExp(patternSpec.pattern, patternSpec.flags ?? "i");
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    issue(issues, scope, `Invalid regex pattern '${patternSpec.pattern}': ${message}`);
  }
}

async function checkValidationContract(contract, skillRoot, issues, scope) {
  if (!contract) {
    return;
  }

  if (typeof contract !== "object") {
    issue(issues, scope, "Validation contract must be an object.");
    return;
  }

  if (contract.type !== "reference_document_checks") {
    issue(issues, scope, "Validation contract type must be 'reference_document_checks'.");
  }

  if (!allowedValidators.has(contract.validator)) {
    issue(
      issues,
      scope,
      `Unknown validator '${contract.validator}'. Supported validators: ${[...allowedValidators].join(", ")}.`,
    );
  }

  if (contract.validator === "spec-update-v1" && !contract.existing_spec_file) {
    issue(issues, scope, "spec-update-v1 requires 'existing_spec_file'.");
  }

  if (contract.validator === "foundation-update-v1" && !contract.existing_foundation_file) {
    issue(issues, scope, "foundation-update-v1 requires 'existing_foundation_file'.");
  }

  for (const field of contractFileFields) {
    if (contract[field] !== undefined) {
      await checkRelativeFile(skillRoot, contract[field], issues, `${scope}.${field}`);
    }
  }

  for (const field of patternFields) {
    if (contract[field] === undefined) {
      continue;
    }
    if (!Array.isArray(contract[field])) {
      issue(issues, scope, `'${field}' must be an array when present.`);
      continue;
    }
    contract[field].forEach((patternSpec, index) =>
      checkPatternSpec(patternSpec, issues, `${scope}.${field}[${index}]`),
    );
  }

  for (const field of ["replaceable_sections", "preserve_sections"]) {
    if (contract[field] !== undefined && !Array.isArray(contract[field])) {
      issue(issues, scope, `'${field}' must be an array when present.`);
    }
  }
}

async function readBamlSourceFiles(directory, issues, scope) {
  const files = [];

  async function walk(currentDir) {
    let entries;
    try {
      entries = await readdir(currentDir, { withFileTypes: true });
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      issue(issues, scope, `Could not read BAML source directory: ${message}`);
      return;
    }

    for (const entry of entries) {
      const entryPath = path.join(currentDir, entry.name);
      if (entry.isDirectory()) {
        await walk(entryPath);
        continue;
      }
      if (entry.isFile() && entry.name.endsWith(".baml")) {
        files.push(entryPath);
      }
    }
  }

  await walk(directory);
  return files;
}

async function checkRunnerFunctions(skillRoot, runnerContract, issues, scope) {
  const bamlSrcDir = path.join(skillRoot, "baml_src");
  const bamlFiles = await readBamlSourceFiles(bamlSrcDir, issues, `${scope}.baml_src`);
  if (bamlFiles.length === 0) {
    issue(issues, scope, "No BAML source files found under baml_src.");
    return;
  }

  const bamlSource = (await Promise.all(bamlFiles.map((file) => readFile(file, "utf8")))).join(
    "\n",
  );
  const fields = [
    "compile_brief_function",
    "render_document_function",
    "evaluate_document_function",
  ];

  for (const field of fields) {
    const functionName = runnerContract[field];
    if (typeof functionName !== "string") {
      continue;
    }

    const declaration = new RegExp(`\\bfunction\\s+${functionName}\\s*\\(`);
    if (!declaration.test(bamlSource)) {
      issue(
        issues,
        scope,
        `Runner function '${functionName}' from '${field}' was not found in baml_src.`,
      );
    }
  }
}

async function checkEvalEntry(evalEntry, context) {
  const { evalsDir, manifestValidationContract, seenEvalIds, seenEvalNames, skillRoot } = context;
  const issues = context.issues;
  const scope = `${context.skillName}.evals[${context.index}]`;

  if (!Number.isInteger(evalEntry.id)) {
    issue(issues, scope, "'id' must be an integer.");
  } else if (seenEvalIds.has(evalEntry.id)) {
    issue(issues, scope, `Duplicate eval id '${evalEntry.id}'.`);
  } else {
    seenEvalIds.add(evalEntry.id);
  }

  checkNonEmptyString(evalEntry.eval_name, issues, scope, "eval_name");
  if (typeof evalEntry.eval_name === "string") {
    if (seenEvalNames.has(evalEntry.eval_name)) {
      issue(issues, scope, `Duplicate eval_name '${evalEntry.eval_name}'.`);
    } else {
      seenEvalNames.add(evalEntry.eval_name);
    }
    if (!/^[a-z0-9][a-z0-9-]*$/.test(evalEntry.eval_name)) {
      issue(issues, scope, "'eval_name' should be a lowercase slug.");
    }
  }

  checkNonEmptyString(evalEntry.prompt, issues, scope, "prompt");
  if (
    typeof evalEntry.expected_output !== "string" &&
    typeof evalEntry.expected_file !== "string" &&
    typeof evalEntry.packet_files?.expected_criteria !== "string"
  ) {
    issue(
      issues,
      scope,
      "Eval should declare expected_output, expected_file, or packet_files.expected_criteria.",
    );
  }

  checkStringArray(evalEntry.files, issues, scope, "files");
  if (Array.isArray(evalEntry.files)) {
    for (const [fileIndex, filePath] of evalEntry.files.entries()) {
      await checkRelativeFile(evalsDir, filePath, issues, `${scope}.files[${fileIndex}]`);
    }
  }

  if (typeof evalEntry.expected_file === "string") {
    await checkRelativeFile(evalsDir, evalEntry.expected_file, issues, `${scope}.expected_file`);
  }

  const packetFiles = evalEntry.packet_files ?? {};
  if (packetFiles && typeof packetFiles !== "object") {
    issue(issues, scope, "'packet_files' must be an object when present.");
  } else {
    for (const [key, filePath] of Object.entries(packetFiles)) {
      if (!allowedPacketFileKeys.has(key)) {
        issue(
          issues,
          scope,
          `Unknown packet_files key '${key}'. Supported keys: ${[...allowedPacketFileKeys].join(", ")}.`,
        );
      }
      await checkRelativeFile(evalsDir, filePath, issues, `${scope}.packet_files.${key}`);
    }
  }

  const validationContract = evalEntry.validation_contract ?? manifestValidationContract;
  await checkValidationContract(validationContract, skillRoot, issues, `${scope}.validation_contract`);
}

export async function checkSkillEvalContracts({
  repoRoot,
  skillNameOrPath,
  requireSmoke = true,
}) {
  const looksLikePath =
    skillNameOrPath.includes(path.sep) ||
    skillNameOrPath.startsWith(".") ||
    path.isAbsolute(skillNameOrPath);
  const skillRoot = looksLikePath
    ? path.resolve(repoRoot, skillNameOrPath)
    : path.join(repoRoot, "skills", skillNameOrPath);
  const skillName = path.basename(skillRoot);
  const evalsDir = path.join(skillRoot, "evals");
  const manifestPath = path.join(evalsDir, "evals.json");
  const issues = [];

  const manifest = await readJson(manifestPath, issues, skillName);
  if (!manifest) {
    return {
      skill_name: skillName,
      eval_count: 0,
      smoke_count: 0,
      issues,
    };
  }

  if (manifest.skill_name !== skillName) {
    issue(
      issues,
      skillName,
      `Manifest skill_name '${manifest.skill_name}' does not match directory '${skillName}'.`,
    );
  }

  checkNonEmptyString(manifest.capability_id, issues, skillName, "capability_id");

  const runnerContract = manifest.runner_contract;
  if (!runnerContract || typeof runnerContract !== "object") {
    issue(issues, skillName, "Manifest must declare a runner_contract object.");
  } else {
    if (runnerContract.type !== "baml_pipeline") {
      issue(issues, skillName, "runner_contract.type must be 'baml_pipeline'.");
    }
    for (const field of [
      "packet_type",
      "compile_brief_function",
      "render_document_function",
      "evaluate_document_function",
    ]) {
      checkNonEmptyString(runnerContract[field], issues, `${skillName}.runner_contract`, field);
    }
    await checkRunnerFunctions(skillRoot, runnerContract, issues, `${skillName}.runner_contract`);
  }

  await checkValidationContract(
    manifest.validation_contract,
    skillRoot,
    issues,
    `${skillName}.validation_contract`,
  );

  if (!Array.isArray(manifest.evals) || manifest.evals.length === 0) {
    issue(issues, skillName, "Manifest must declare a non-empty evals array.");
    return {
      skill_name: skillName,
      eval_count: 0,
      smoke_count: 0,
      issues,
    };
  }

  const smokeCount = manifest.evals.filter((entry) => entry.smoke === true).length;
  if (requireSmoke && smokeCount === 0) {
    issue(issues, skillName, "At least one eval must be marked with smoke: true.");
  }

  const seenEvalIds = new Set();
  const seenEvalNames = new Set();
  for (const [index, evalEntry] of manifest.evals.entries()) {
    await checkEvalEntry(evalEntry, {
      evalsDir,
      index,
      issues,
      manifestValidationContract: manifest.validation_contract,
      seenEvalIds,
      seenEvalNames,
      skillName,
      skillRoot,
    });
  }

  return {
    skill_name: skillName,
    eval_count: manifest.evals.length,
    smoke_count: smokeCount,
    issues,
  };
}

export function formatStaticCheckResult(result) {
  if (result.issues.length === 0) {
    return [
      `OK ${result.skill_name}: ${result.eval_count} evals, ${result.smoke_count} smoke evals.`,
    ];
  }

  return [
    `FAIL ${result.skill_name}: ${result.issues.length} issue(s).`,
    ...result.issues.map((entry) => `- ${entry.scope}: ${entry.message}`),
  ];
}
