import { access, cp, mkdtemp, symlink } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { fail, runCommand } from "./runtime.ts";

function dedupeStrings(values) {
  const deduped = [];
  const seen = new Set();

  for (const value of values) {
    if (seen.has(value)) {
      continue;
    }
    seen.add(value);
    deduped.push(value);
  }

  return deduped;
}

export function sameStringArray(left, right) {
  if (left.length !== right.length) {
    return false;
  }

  return left.every((value, index) => value === right[index]);
}

function shellEscape(value) {
  return `'${String(value).replace(/'/g, `'\\''`)}'`;
}

export function slugifyVariantLabel(label) {
  return label
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "") || "variant";
}

export function parseVariantSpec(rawValue) {
  const value = rawValue.trim();

  if (value === "current") {
    return {
      key: "current",
      label: "current",
      kind: "current",
      source: {
        type: "working_tree",
      },
    };
  }

  if (value === "previous") {
    return {
      key: "previous",
      label: "previous",
      kind: "git",
      ref: "HEAD~1",
      source: {
        type: "git",
        ref: "HEAD~1",
      },
    };
  }

  if (value === "no-skill") {
    return {
      key: "profile:no-skill",
      label: "profile:no-skill",
      kind: "profile",
      profileName: "no-skill",
      source: {
        type: "profile",
        name: "no-skill",
      },
    };
  }

  if (value.startsWith("profile:")) {
    const profileName = value.slice("profile:".length).trim();
    if (profileName.length === 0) {
      fail("Profile comparison variant is missing a name.");
    }
    return {
      key: `profile:${profileName}`,
      label: `profile:${profileName}`,
      kind: "profile",
      profileName,
      source: {
        type: "profile",
        name: profileName,
      },
    };
  }

  if (value.startsWith("git:")) {
    const ref = value.slice("git:".length).trim();
    if (ref.length === 0) {
      fail("Git comparison variant is missing a ref.");
    }
    return {
      key: `git:${ref}`,
      label: `git:${ref}`,
      kind: "git",
      ref,
      source: {
        type: "git",
        ref,
      },
    };
  }

  fail(
    `Unknown comparison variant '${rawValue}'. Use current, previous, no-skill, profile:<name>, or git:<ref>.`,
  );
}

export function buildVariantPlan(compareSpecs) {
  if (compareSpecs.length === 0) {
    return [parseVariantSpec("current")];
  }

  const variants = [parseVariantSpec("current"), ...compareSpecs.map(parseVariantSpec)];
  const deduped = [];
  const seen = new Set();

  for (const variant of variants) {
    if (seen.has(variant.key)) {
      continue;
    }
    seen.add(variant.key);
    deduped.push(variant);
  }

  return deduped;
}

function shouldCopySkillPath(relativePath) {
  const normalizedPath = relativePath.split(path.sep).join("/");

  if (normalizedPath.length === 0) {
    return true;
  }

  return !(
    normalizedPath === "baml_client" ||
    normalizedPath.startsWith("baml_client/") ||
    normalizedPath === "baml_client_dist" ||
    normalizedPath.startsWith("baml_client_dist/") ||
    normalizedPath === "evals/runs" ||
    normalizedPath.startsWith("evals/runs/")
  );
}

async function cloneSkillRoot(sourceSkillRoot, destinationSkillRoot) {
  await cp(sourceSkillRoot, destinationSkillRoot, {
    recursive: true,
    force: true,
    filter: (sourcePath) => shouldCopySkillPath(path.relative(sourceSkillRoot, sourcePath)),
  });
}

async function linkWorkspaceNodeModules(workspaceRoot, repoRoot) {
  const workspaceNodeModulesPath = path.join(workspaceRoot, "node_modules");

  try {
    await symlink(path.join(repoRoot, "node_modules"), workspaceNodeModulesPath, "dir");
  } catch (error) {
    if (error?.code !== "EEXIST") {
      throw error;
    }
  }
}

async function materializeGitSkillRoot(skillName, ref, workspaceRoot, repoRoot) {
  const repoRelativeSkillPath = path.posix.join("skills", skillName);
  const archiveCommand = [
    "git archive --format=tar",
    shellEscape(ref),
    shellEscape(repoRelativeSkillPath),
    "| tar -x -C",
    shellEscape(workspaceRoot),
  ].join(" ");

  await runCommand("bash", ["-lc", archiveCommand], repoRoot);
  return path.join(workspaceRoot, "skills", skillName);
}

async function resolveProfileRoot(baseSkillRoot, profileName) {
  const profileRoot = path.join(baseSkillRoot, "eval_profiles", profileName);

  try {
    await access(profileRoot);
  } catch {
    fail(`Skill profile '${profileName}' not found at ${profileRoot}.`);
  }

  return profileRoot;
}

async function applyOverlayProfiles(skillRoot, baseSkillRoot, overlayProfileNames) {
  for (const profileName of overlayProfileNames) {
    const profileRoot = await resolveProfileRoot(baseSkillRoot, profileName);
    await cp(profileRoot, skillRoot, {
      recursive: true,
      force: true,
    });
  }
}

export async function materializeVariantSkillRoot(
  skillName,
  baseSkillRoot,
  variant,
  overlayProfileNames = [],
  repoRoot,
) {
  const dedupedOverlayProfiles = dedupeStrings(overlayProfileNames);
  const needsWorkspace = variant.kind !== "current" || dedupedOverlayProfiles.length > 0;

  if (!needsWorkspace) {
    return {
      skillRoot: baseSkillRoot,
      cleanupRoot: null,
    };
  }

  const workspaceRoot = await mkdtemp(
    path.join(os.tmpdir(), `lightfast-skill-eval-${slugifyVariantLabel(variant.label)}-`),
  );
  await linkWorkspaceNodeModules(workspaceRoot, repoRoot);
  let skillRoot = path.join(workspaceRoot, "skills", skillName);

  if (variant.kind === "current") {
    await cloneSkillRoot(baseSkillRoot, skillRoot);
    await applyOverlayProfiles(skillRoot, baseSkillRoot, dedupedOverlayProfiles);
    return {
      skillRoot,
      cleanupRoot: workspaceRoot,
    };
  }

  if (variant.kind === "git") {
    skillRoot = await materializeGitSkillRoot(skillName, variant.ref, workspaceRoot, repoRoot);
    await applyOverlayProfiles(skillRoot, baseSkillRoot, dedupedOverlayProfiles);
    return {
      skillRoot,
      cleanupRoot: workspaceRoot,
    };
  }

  if (variant.kind === "profile") {
    const profileRoot = await resolveProfileRoot(baseSkillRoot, variant.profileName);
    await cloneSkillRoot(baseSkillRoot, skillRoot);
    await cp(profileRoot, skillRoot, {
      recursive: true,
      force: true,
    });
    await applyOverlayProfiles(skillRoot, baseSkillRoot, dedupedOverlayProfiles);

    return {
      skillRoot,
      cleanupRoot: workspaceRoot,
    };
  }

  fail(`Unsupported variant kind '${variant.kind}'.`);
}
