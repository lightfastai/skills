import path from "node:path";
import { fail, loadJson, loadText } from "./runtime.ts";

export async function loadEvalManifest(evalsDir, skillName) {
  const manifestPath = path.join(evalsDir, "evals.json");
  const manifest = await loadJson(manifestPath);

  if (!manifest.runner_contract || manifest.runner_contract.type !== "baml_pipeline") {
    fail(`Skill '${skillName}' does not declare a supported runner_contract.`);
  }

  if (!Array.isArray(manifest.evals)) {
    fail(`Eval manifest for '${skillName}' must declare an evals array.`);
  }

  return manifest;
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

export function getEvalEntriesBySelector(evals, selector, runAll) {
  if (runAll) {
    if (selector) {
      fail("Pass either --all or an eval id/name, not both.");
    }
    return evals;
  }

  return [getEvalBySelector(evals, selector)];
}

export async function buildEvalPacket(evalEntry, evalsDir, packetType) {
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

export function extractEvalMetadata(evalEntry) {
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
