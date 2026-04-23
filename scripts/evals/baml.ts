import { rm, writeFile } from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";
import { runCommand } from "./runtime.ts";

async function generateClient(skillRoot, repoRoot) {
  const bamlSrc = path.join(skillRoot, "baml_src");
  await runCommand(
    "node",
    [
      path.join(repoRoot, "node_modules", "@boundaryml", "baml", "cli.js"),
      "generate",
      "--from",
      bamlSrc,
    ],
    repoRoot,
  );
}

export async function importGeneratedClient(skillRoot) {
  const clientPath = path.join(skillRoot, "baml_client_dist", "index.js");
  return import(pathToFileURL(clientPath).href);
}

export async function ensureFreshClient(skillRoot, repoRoot) {
  const clientDir = path.join(skillRoot, "baml_client");
  const distDir = path.join(skillRoot, "baml_client_dist");
  const tsconfigPath = path.join(skillRoot, ".tmp-baml-client-tsconfig.json");
  await rm(clientDir, { recursive: true, force: true });
  await rm(distDir, { recursive: true, force: true });
  await generateClient(skillRoot, repoRoot);
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
    await runCommand(
      "node",
      [path.join(repoRoot, "node_modules", "typescript", "bin", "tsc"), "--project", tsconfigPath],
      repoRoot,
    );
  } finally {
    await rm(tsconfigPath, { force: true });
  }
}
