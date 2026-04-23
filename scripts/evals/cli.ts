import { fail } from "./runtime.ts";

export function parseArgs(argv) {
  const positionals = [];
  let trials = 1;
  let compare = [];
  let evalProfile = "fast";
  let runAll = false;

  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];

    if (arg === "--all") {
      runAll = true;
      continue;
    }

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

    if (arg === "--compare") {
      const next = argv[index + 1];
      if (!next) {
        fail("Missing value after --compare.");
      }
      compare = next
        .split(",")
        .map((value) => value.trim())
        .filter((value) => value.length > 0);
      index += 1;
      continue;
    }

    if (arg === "--eval-profile") {
      const next = argv[index + 1];
      if (!next) {
        fail("Missing value after --eval-profile.");
      }
      evalProfile = next.trim();
      if (evalProfile.length === 0) {
        fail("--eval-profile must not be empty.");
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
    compare,
    evalProfile,
    runAll,
  };
}
