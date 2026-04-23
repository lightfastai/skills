import { execFile } from "node:child_process";
import { promisify } from "node:util";

const execFileAsync = promisify(execFile);

async function gitOutput(repoRoot, args) {
  const { stdout } = await execFileAsync("git", args, { cwd: repoRoot });
  return stdout.trim();
}

export async function getGitMetadata(repoRoot) {
  try {
    const [sha, shortSha, branch, status] = await Promise.all([
      gitOutput(repoRoot, ["rev-parse", "HEAD"]),
      gitOutput(repoRoot, ["rev-parse", "--short", "HEAD"]),
      gitOutput(repoRoot, ["rev-parse", "--abbrev-ref", "HEAD"]),
      gitOutput(repoRoot, ["status", "--short"]),
    ]);

    return {
      sha,
      short_sha: shortSha,
      branch,
      is_dirty: status.length > 0,
    };
  } catch {
    return {
      sha: "unknown",
      short_sha: "unknown",
      branch: "unknown",
      is_dirty: null,
    };
  }
}
