type JsonObject = Record<string, unknown>;

type BraintrustExperiment = {
  id: string;
  name: string;
  project_id?: string;
  created?: string;
  commit?: string | null;
  tags?: string[] | null;
  metadata?: JsonObject | null;
};

type BraintrustRow = {
  id?: string;
  input?: JsonObject | null;
  scores?: JsonObject | null;
  metadata?: JsonObject | null;
  metrics?: JsonObject | null;
};

type Filters = {
  capability?: string;
  skill?: string;
  profile?: string;
  suite?: string;
};

type Options = Filters & {
  apiUrl: string;
  command: string;
  experiment?: string;
  json: boolean;
  limit: number;
  org?: string;
  project: string;
};

const DEFAULT_PROJECT = "lightfast-skills";
const DEFAULT_API_URL = "https://api.braintrust.dev";

function fail(message: string): never {
  console.error(message);
  process.exit(1);
}

function usage(): never {
  fail(`Usage:
  bun run braintrust:list -- [--limit N] [--capability ID] [--skill NAME] [--profile NAME] [--suite MODE] [--json]
  bun run braintrust:latest -- [--capability ID] [--skill NAME] [--profile NAME] [--suite MODE] [--json]
  bun run braintrust:show -- <experiment-id|experiment-name|latest> [--limit N] [--json]

Environment:
  BRAINTRUST_API_KEY is required.
  BRAINTRUST_PROJECT defaults to '${DEFAULT_PROJECT}'.
  BRAINTRUST_API_URL defaults to '${DEFAULT_API_URL}'.`);
}

function parseArgs(argv: string[]): Options {
  const args = [...argv];
  const command = args.shift() ?? "list";
  const options: Options = {
    apiUrl: process.env.BRAINTRUST_API_URL ?? DEFAULT_API_URL,
    command,
    json: false,
    limit: command === "show" || command === "latest" ? 1000 : 10,
    org: process.env.BRAINTRUST_ORG ?? process.env.BRAINTRUST_ORG_NAME,
    project:
      process.env.BRAINTRUST_PROJECT ??
      process.env.BRAINTRUST_DEFAULT_PROJECT ??
      DEFAULT_PROJECT,
  };

  while (args.length > 0) {
    const arg = args.shift();
    if (!arg) {
      continue;
    }

    switch (arg) {
      case "--json":
        options.json = true;
        break;
      case "--project":
        options.project = requireValue(arg, args.shift());
        break;
      case "--api-url":
        options.apiUrl = requireValue(arg, args.shift());
        break;
      case "--org":
        options.org = requireValue(arg, args.shift());
        break;
      case "--limit":
        options.limit = parsePositiveInteger(requireValue(arg, args.shift()), arg);
        break;
      case "--capability":
        options.capability = requireValue(arg, args.shift());
        break;
      case "--skill":
        options.skill = requireValue(arg, args.shift());
        break;
      case "--profile":
        options.profile = requireValue(arg, args.shift());
        break;
      case "--suite":
        options.suite = requireValue(arg, args.shift());
        break;
      default:
        if (arg.startsWith("--")) {
          usage();
        }
        if (options.experiment) {
          usage();
        }
        options.experiment = arg;
    }
  }

  return options;
}

function requireValue(flag: string, value?: string): string {
  if (!value || value.startsWith("--")) {
    fail(`${flag} requires a value.`);
  }
  return value;
}

function parsePositiveInteger(value: string, flag: string): number {
  const parsed = Number.parseInt(value, 10);
  if (!Number.isInteger(parsed) || parsed <= 0) {
    fail(`${flag} must be a positive integer.`);
  }
  return parsed;
}

function getApiKey(): string {
  const apiKey = process.env.BRAINTRUST_API_KEY;
  if (!apiKey) {
    fail("BRAINTRUST_API_KEY is required.");
  }
  return apiKey;
}

async function braintrustFetch(
  options: Options,
  path: string,
  init: RequestInit = {},
): Promise<unknown> {
  const apiUrl = options.apiUrl.replace(/\/+$/, "");
  const response = await fetch(`${apiUrl}${path}`, {
    ...init,
    headers: {
      Authorization: `Bearer ${getApiKey()}`,
      "Content-Type": "application/json",
      ...(init.headers ?? {}),
    },
  });

  if (!response.ok) {
    fail(`Braintrust API error ${response.status}: ${await response.text()}`);
  }

  return await response.json();
}

function metadataOf(experiment: BraintrustExperiment): JsonObject {
  return experiment.metadata ?? {};
}

function nestedObject(value: unknown): JsonObject {
  return value && typeof value === "object" && !Array.isArray(value)
    ? (value as JsonObject)
    : {};
}

function stringValue(value: unknown): string | null {
  return typeof value === "string" ? value : null;
}

function booleanValue(value: unknown): boolean | null {
  return typeof value === "boolean" ? value : null;
}

function numberValue(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function arrayValue(value: unknown): unknown[] {
  return Array.isArray(value) ? value : [];
}

function statusFromScore(score: unknown): string | null {
  if (score === 1) {
    return "Pass";
  }
  if (score === 0.5) {
    return "Partial";
  }
  if (score === 0) {
    return "Fail";
  }
  return null;
}

function filterExperiment(experiment: BraintrustExperiment, filters: Filters): boolean {
  const metadata = metadataOf(experiment);
  const tags = experiment.tags ?? [];
  const evalProfile = nestedObject(metadata.eval_profile);

  return (
    (!filters.capability ||
      metadata.capability_id === filters.capability ||
      tags.includes(filters.capability)) &&
    (!filters.skill || metadata.skill_name === filters.skill || tags.includes(filters.skill)) &&
    (!filters.profile ||
      evalProfile.name === filters.profile ||
      tags.includes(filters.profile)) &&
    (!filters.suite || metadata.suite_mode === filters.suite || tags.includes(filters.suite))
  );
}

async function listExperiments(options: Options, requestedLimit = options.limit) {
  const params = new URLSearchParams({
    limit: String(Math.max(requestedLimit * 5, 50)),
    project_name: options.project,
  });

  if (options.org) {
    params.set("org_name", options.org);
  }

  const response = (await braintrustFetch(
    options,
    `/v1/experiment?${params}`,
  )) as { objects?: BraintrustExperiment[] };

  return (response.objects ?? [])
    .filter((experiment) => filterExperiment(experiment, options))
    .slice(0, requestedLimit);
}

async function resolveExperiment(options: Options): Promise<BraintrustExperiment> {
  const selector = options.experiment ?? "latest";

  if (selector === "latest") {
    const [latest] = await listExperiments(options, 1);
    if (!latest) {
      fail("No matching Braintrust experiments found.");
    }
    return latest;
  }

  const params = new URLSearchParams({
    limit: "10",
    project_name: options.project,
  });

  if (options.org) {
    params.set("org_name", options.org);
  }

  if (isUuid(selector)) {
    params.append("ids", selector);
  } else {
    params.set("experiment_name", selector);
  }

  const response = (await braintrustFetch(
    options,
    `/v1/experiment?${params}`,
  )) as { objects?: BraintrustExperiment[] };
  const [experiment] = response.objects ?? [];

  if (!experiment) {
    fail(`Braintrust experiment not found: ${selector}`);
  }

  return experiment;
}

function isUuid(value: string): boolean {
  return /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(
    value,
  );
}

function btqlString(value: string): string {
  return `'${value.replaceAll("'", "''")}'`;
}

async function fetchExperimentRows(options: Options, experimentId: string) {
  const query = `
    SELECT id, input, scores, metadata, metrics
    FROM experiment(${btqlString(experimentId)})
    LIMIT ${options.limit}
  `;

  const response = (await braintrustFetch(options, "/btql", {
    method: "POST",
    body: JSON.stringify({ query, fmt: "json" }),
  })) as { data?: BraintrustRow[] };

  return response.data ?? [];
}

function summarizeRow(row: BraintrustRow) {
  const input = nestedObject(row.input);
  const scores = nestedObject(row.scores);
  const metadata = nestedObject(row.metadata);
  const metrics = nestedObject(row.metrics);
  const summary = nestedObject(metadata.summary);
  const report = nestedObject(metadata.report);
  const deterministicChecks = nestedObject(metadata.deterministic_checks);
  const checks = arrayValue(deterministicChecks.checks).map(nestedObject);
  const failedChecks = checks
    .filter((check) => check.passed === false)
    .map((check) => stringValue(check.id))
    .filter((id): id is string => Boolean(id));
  const openIssues = arrayValue(report.open_issues)
    .map((issue) => String(issue))
    .filter(Boolean);

  return {
    id: row.id ?? null,
    eval_name: stringValue(input.eval_name) ?? "unknown-eval",
    variant: stringValue(input.variant) ?? "current",
    trial: numberValue(input.trial) ?? null,
    llm_status:
      stringValue(summary.llm_status) ??
      stringValue(report.overall_status) ??
      statusFromScore(scores.llm_status) ??
      "Unknown",
    combined_status:
      stringValue(summary.combined_status) ??
      statusFromScore(scores.combined_status) ??
      "Unknown",
    deterministic_pass:
      booleanValue(summary.deterministic_pass) ??
      (scores.deterministic_pass === 1 ? true : scores.deterministic_pass === 0 ? false : null),
    failed_checks: failedChecks,
    open_issues: openIssues,
    total_ms: numberValue(metrics.total_ms),
    artifact_dir: stringValue(metadata.artifact_dir),
  };
}

function buildExperimentSummary(experiment: BraintrustExperiment, rows: BraintrustRow[]) {
  const rowSummaries = rows.map(summarizeRow);
  const combinedStatusCounts = countStatuses(rowSummaries.map((row) => row.combined_status));
  const llmStatusCounts = countStatuses(rowSummaries.map((row) => row.llm_status));
  const totalMs = rowSummaries
    .map((row) => row.total_ms)
    .filter((value): value is number => value !== null);

  return {
    experiment,
    rows: rowSummaries,
    summary: {
      row_count: rowSummaries.length,
      llm_status_counts: llmStatusCounts,
      combined_status_counts: combinedStatusCounts,
      deterministic_failures: rowSummaries
        .filter((row) => row.failed_checks.length > 0)
        .map((row) => ({
          eval_name: row.eval_name,
          trial: row.trial,
          failed_checks: row.failed_checks,
        })),
      open_issues: rowSummaries
        .filter((row) => row.open_issues.length > 0)
        .map((row) => ({
          eval_name: row.eval_name,
          trial: row.trial,
          open_issues: row.open_issues,
        })),
      timing_ms:
        totalMs.length === 0
          ? null
          : {
              min: Math.min(...totalMs),
              max: Math.max(...totalMs),
              avg: Math.round(totalMs.reduce((sum, value) => sum + value, 0) / totalMs.length),
            },
    },
  };
}

function countStatuses(statuses: string[]) {
  return {
    Pass: statuses.filter((status) => status === "Pass").length,
    Partial: statuses.filter((status) => status === "Partial").length,
    Fail: statuses.filter((status) => status === "Fail").length,
    Unknown: statuses.filter((status) => !["Pass", "Partial", "Fail"].includes(status)).length,
  };
}

function printExperimentList(experiments: BraintrustExperiment[]) {
  if (experiments.length === 0) {
    console.log("No matching Braintrust experiments found.");
    return;
  }

  const rows = experiments.map((experiment) => {
    const metadata = metadataOf(experiment);
    const profile = nestedObject(metadata.eval_profile);
    const git = nestedObject(metadata.git);

    return {
      created: formatDate(experiment.created),
      capability: String(metadata.capability_id ?? ""),
      suite: String(metadata.suite_mode ?? ""),
      profile: String(profile.name ?? ""),
      sha: String(git.short_sha ?? experiment.commit ?? ""),
      name: experiment.name,
      id: experiment.id,
    };
  });

  printTable(rows, ["created", "capability", "suite", "profile", "sha", "name"]);
}

function printExperimentSummary(summary: ReturnType<typeof buildExperimentSummary>) {
  const experiment = summary.experiment;
  const metadata = metadataOf(experiment);
  const profile = nestedObject(metadata.eval_profile);
  const git = nestedObject(metadata.git);

  console.log(`Experiment: ${experiment.name}`);
  console.log(`ID: ${experiment.id}`);
  console.log(`Created: ${formatDate(experiment.created)}`);
  console.log(
    `Run: ${metadata.skill_name ?? "unknown-skill"} / ${metadata.capability_id ?? "unknown-capability"} / ${metadata.suite_mode ?? "unknown-suite"} / ${profile.name ?? "unknown-profile"}`,
  );
  console.log(`Commit: ${git.short_sha ?? experiment.commit ?? "unknown"}`);
  console.log(`Rows: ${summary.summary.row_count}`);
  console.log(
    `Combined: Pass ${summary.summary.combined_status_counts.Pass}, Partial ${summary.summary.combined_status_counts.Partial}, Fail ${summary.summary.combined_status_counts.Fail}, Unknown ${summary.summary.combined_status_counts.Unknown}`,
  );
  console.log(
    `LLM: Pass ${summary.summary.llm_status_counts.Pass}, Partial ${summary.summary.llm_status_counts.Partial}, Fail ${summary.summary.llm_status_counts.Fail}, Unknown ${summary.summary.llm_status_counts.Unknown}`,
  );

  if (summary.summary.timing_ms) {
    console.log(
      `Timing total ms: avg ${summary.summary.timing_ms.avg}, min ${summary.summary.timing_ms.min}, max ${summary.summary.timing_ms.max}`,
    );
  }

  if (summary.summary.deterministic_failures.length > 0) {
    console.log("");
    console.log("Deterministic failures:");
    for (const failure of summary.summary.deterministic_failures) {
      console.log(
        `- ${failure.eval_name}${failure.trial ? ` trial ${failure.trial}` : ""}: ${failure.failed_checks.join(", ")}`,
      );
    }
  }

  if (summary.summary.open_issues.length > 0) {
    console.log("");
    console.log("LLM open issues:");
    for (const issueGroup of summary.summary.open_issues) {
      console.log(
        `- ${issueGroup.eval_name}${issueGroup.trial ? ` trial ${issueGroup.trial}` : ""}: ${issueGroup.open_issues.join(" | ")}`,
      );
    }
  }

  console.log("");
  printTable(
    summary.rows.map((row) => ({
      combined: row.combined_status,
      llm: row.llm_status,
      deterministic: row.deterministic_pass === null ? "?" : row.deterministic_pass ? "yes" : "no",
      total_ms: row.total_ms === null ? "" : String(row.total_ms),
      eval: row.eval_name,
      trial: row.trial === null ? "" : String(row.trial),
    })),
    ["combined", "llm", "deterministic", "total_ms", "trial", "eval"],
  );
}

function formatDate(value?: string): string {
  if (!value) {
    return "";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toISOString().replace("T", " ").replace(/\.\d+Z$/, "Z");
}

function printTable(rows: JsonObject[], columns: string[]) {
  const widths = new Map(
    columns.map((column) => [
      column,
      Math.max(
        column.length,
        ...rows.map((row) => String(row[column] ?? "").length),
      ),
    ]),
  );
  const formatRow = (row: JsonObject) =>
    columns.map((column) => String(row[column] ?? "").padEnd(widths.get(column) ?? 0)).join("  ");

  console.log(formatRow(Object.fromEntries(columns.map((column) => [column, column]))));
  console.log(columns.map((column) => "-".repeat(widths.get(column) ?? 0)).join("  "));
  for (const row of rows) {
    console.log(formatRow(row));
  }
}

async function main() {
  const options = parseArgs(process.argv.slice(2));

  switch (options.command) {
    case "list": {
      const experiments = await listExperiments(options);
      if (options.json) {
        console.log(JSON.stringify(experiments, null, 2));
      } else {
        printExperimentList(experiments);
      }
      break;
    }
    case "latest":
    case "show": {
      const experiment = await resolveExperiment(options);
      const rows = await fetchExperimentRows(options, experiment.id);
      const summary = buildExperimentSummary(experiment, rows);
      if (options.json) {
        console.log(JSON.stringify(summary, null, 2));
      } else {
        printExperimentSummary(summary);
      }
      break;
    }
    default:
      usage();
  }
}

main().catch((error) => {
  console.error(error instanceof Error ? error.message : String(error));
  process.exit(1);
});
