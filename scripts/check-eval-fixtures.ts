import path from "node:path";
import { fileURLToPath } from "node:url";
import {
  checkSkillEvalContracts,
  formatStaticCheckResult,
} from "./evals/static-checks.ts";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..");

const args = process.argv.slice(2);
const requireSmoke = !args.includes("--allow-no-smoke");
const skillArgs = args.filter((arg) => arg !== "--allow-no-smoke");
const skills = skillArgs.length > 0 ? skillArgs : ["foundation-creator", "spec-creator"];

const results = await Promise.all(
  skills.map((skillNameOrPath) =>
    checkSkillEvalContracts({
      repoRoot,
      skillNameOrPath,
      requireSmoke,
    }),
  ),
);

for (const result of results) {
  console.log(formatStaticCheckResult(result).join("\n"));
}

if (results.some((result) => result.issues.length > 0)) {
  process.exit(1);
}
