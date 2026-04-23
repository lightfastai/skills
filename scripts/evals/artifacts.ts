import { mkdir, stat, writeFile } from "node:fs/promises";
import path from "node:path";

export async function writeArtifacts(runDir, artifacts) {
  await mkdir(runDir, { recursive: true });
  for (const [name, value] of Object.entries(artifacts)) {
    const filePath = path.join(runDir, name);
    const content = typeof value === "string" ? value : JSON.stringify(value, null, 2);
    await writeFile(filePath, content, "utf8");
  }
}

async function isFile(filePath) {
  try {
    return (await stat(filePath)).isFile();
  } catch {
    return false;
  }
}

async function isDirectory(filePath) {
  try {
    return (await stat(filePath)).isDirectory();
  } catch {
    return false;
  }
}

export async function resolveCandidateDocumentPath(sourcePath, evalName) {
  const resolved = path.resolve(sourcePath);
  if (await isFile(resolved)) {
    return resolved;
  }

  if (!(await isDirectory(resolved))) {
    throw new Error(`Deterministic-only candidate source does not exist: ${sourcePath}`);
  }

  const candidates = [
    path.join(resolved, "candidate.md"),
    path.join(resolved, evalName, "candidate.md"),
    path.join(resolved, "variants", "current", "candidate.md"),
    path.join(resolved, evalName, "variants", "current", "candidate.md"),
  ];

  for (const candidatePath of candidates) {
    if (await isFile(candidatePath)) {
      return candidatePath;
    }
  }

  throw new Error(
    `Could not find candidate.md for '${evalName}' under ${sourcePath}. ` +
      "Pass a candidate.md file, a run directory, or a suite directory.",
  );
}
