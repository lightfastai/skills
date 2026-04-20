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
  await runCommand("npx", ["baml-cli", "generate", "--from", bamlSrc], repoRoot);
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
    await runCommand("npx", ["tsc", "--project", tsconfigPath], repoRoot);
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

async function main() {
  const skillName = process.argv[2];
  const selector = process.argv[3];

  if (!skillName) {
    fail("Usage: node ./scripts/run-baml-eval.mjs <foundation-creator|spec-creator> [eval-id-or-name]");
  }

  const skillRoot = path.join(repoRoot, "skills", skillName);
  const evalsDir = path.join(skillRoot, "evals");
  const manifestPath = path.join(evalsDir, "evals.json");
  const manifest = await loadJson(manifestPath);
  const evalEntry = getEvalBySelector(manifest.evals, selector);
  const runner = manifest.runner_contract;

  if (!runner || runner.type !== "baml_pipeline") {
    fail(`Skill '${skillName}' does not declare a supported runner_contract.`);
  }

  if (!process.env.AI_GATEWAY_API_KEY) {
    fail("AI_GATEWAY_API_KEY is required to execute BAML evals.");
  }

  await ensureFreshClient(skillRoot);
  const generated = await importGeneratedClient(skillRoot);
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
    fail(`Generated client is missing one or more runner functions for '${skillName}'.`);
  }

  const brief = await b[compileFnName](packet);
  const candidateDocument = await b[renderFnName](brief);
  const report = await b[evaluateFnName](packet, candidateDocument);

  const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
  const runDir = path.join(skillRoot, "evals", "runs", `${timestamp}-${evalEntry.eval_name}`);
  await writeRunArtifacts(runDir, {
    "packet.json": packet,
    "brief.json": brief,
    "candidate.md": candidateDocument,
    "report.json": report,
  });

  console.log(`Run complete: ${runDir}`);
  console.log(`Overall status: ${report.overall_status}`);
}

main().catch((error) => {
  console.error(error instanceof Error ? error.message : String(error));
  process.exit(1);
});
