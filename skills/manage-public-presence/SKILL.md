---
name: manage-public-presence
description: Use when a person or organization needs to audit, resume, correct, deploy, reindex, or monitor its controlled public identity across websites, source hosts, package registries, search consoles, social profiles, communities, directories, and AI retrieval systems.
---

# Manage Public Presence

Manage the public sources that shape how search engines, AI systems, developers, customers, and journalists understand a person or organization. Call that person or organization the **principal** throughout this skill.

## Operating principles

- Work only on surfaces the principal owns, administers, or can legitimately request updates for.
- Select an existing editorial source as canonical. Do not create a second positioning contract unless the user explicitly requests one.
- Keep distinct principals isolated. Where applicable, give each principal a dedicated provider project, OAuth client, and 1Password Environment. A shared provider account or organization may contain those resources, but do not collapse their credential scopes or reuse one principal's credentials for another.
- Prefer supported APIs and CLIs. Use Computer Use with the default browser for authenticated UI-only operations.
- Never use private endpoints, captured cookies, internal GraphQL calls, or undocumented browser APIs.
- Keep credentials in provider or system credential stores. Never request passwords, recovery codes, session cookies, or raw private keys in chat.
- Treat account emails and usernames, tenant and project IDs, private property identifiers, unpublished domains, internal URLs, provider receipts, and similar operational metadata as sensitive even when they are not authentication secrets. Minimize, mask, and avoid persisting them unless the user explicitly needs the exact value.
- Return control for login, MFA, CAPTCHA, consent, new permissions, legal terms, billing, or irreversible actions.
- Do not create repository scripts, tests, workflows, ledgers, or verification files unless the user asks for persistent infrastructure.
- Treat package and project descriptions as product-specific. They need not repeat the company description verbatim.
- Treat indexing as notification, not control. No provider guarantees recrawl, indexing, ranking, or model convergence.

## Choose the operating mode

Infer the narrowest mode that satisfies the request:

- **Audit:** Read-only inventory, source comparison, capability map, and findings.
- **Setup:** Establish supported credentials, permissions, verified properties, or trusted publishers. Pause at human authentication steps.
- **Remediate:** Correct controlled sources after the canonical direction is approved.
- **Reindex:** Notify search systems only after production verification succeeds.
- **Monitor:** Recheck controlled sources and retrieval systems on a fixed cadence.

Do not turn an Audit request into external writes. Remediate, Reindex, and Setup requests authorize only their named surfaces.

## Resume the control plane

On every fresh run, recover live state before proposing setup. Missing chat history is not evidence that a resource is missing.

1. Resolve the principal slug in this order: explicit user-provided slug, existing selected or linked resource, official source-host identity, then registrable domain. Normalize only when no established slug exists: lowercase; replace spaces, underscores, and dots with single hyphens; trim leading and trailing hyphens.
2. Inventory existing provider resources and authenticated identities with supported read-only APIs or CLIs.
3. Look for a dedicated project and 1Password Environment named `<principal-slug>-public-presence`; also inspect the currently selected or linked resources before searching more broadly. A globally unique immutable provider ID may have a suffix even when its display name follows the convention.
4. Re-read completed administrative state from each provider: verified properties, enabled APIs, roles, archived repositories, package deprecations, submitted sitemaps, and current profile values.
5. Reuse matching resources. An expired or revoked credential does not make its parent project, property, or application unusable: try supported reauthentication or consent first. Create or replace a credential or parent resource only when Setup is authorized and live discovery proves that exact target is absent or cannot be recovered through its supported flow.

Use these conventions:

- developer-facing resource IDs and display names: lowercase kebab-case;
- environment variables: uppercase snake case;
- secrets: the principal's existing 1Password Environment, injected at runtime through the official integration;
- non-secret IDs, status, and receipts: keep them ephemeral and report only what is needed to identify the result; prefer a display label and a short masked suffix over a full identifier.

Do not duplicate 1Password-managed secrets into macOS Keychain, repository files, dotenv files, scripts, or chat. Do not print secret values while testing injection or persist access tokens. Treat task-created OAuth exports, callback captures, helper files, FIFOs, and local Environment mounts as transient; remove them after durable storage and sanitized provider verification succeed. Do not remove user-created credential material without explicit authorization. A provider remains the source of truth for mutable status; the skill is an operating model, not a historical ledger.

For a resumption handoff, report sanitized control-plane labels, masked identifier suffixes only when needed, verified-property status without exposing private property identifiers, credential variable names without values, completed provider state, and the approval gate. Mask account identities unless the user explicitly needs the exact identity to disambiguate access. This is a sanitized snapshot, not a new maintenance artifact.

## Workflow

### 1. Establish the authority

Identify:

- the principal and domains in scope;
- the existing canonical editorial page or document;
- the approved headline, short description, audience, product direction, and claims to retire;
- the repository, production project, package namespace, and official accounts;
- the user’s completion threshold.

If the canonical direction is undergoing a substantive rewrite, complete read-only inventory and access setup, but delay propagation and indexing.

An explicit user approval of the canonical content is the editorial gate. A successful production deployment containing that approved revision is the propagation gate. Until both gates pass, do not submit even an unchanged sitemap as part of the rewrite campaign.

### 2. Inventory controlled surfaces

Search laterally and inspect:

- production site metadata, structured data, sitemap, robots policy, and machine-readable discovery pages;
- source-host organization, repositories, topics, profile repositories, releases, and social-preview assets;
- package registry pages, current releases, deprecated versions, owners, provenance, and mirrors;
- search-console properties, submitted sitemaps, indexed state, removals, and quotas;
- social profiles, company pages, community servers, verified directories, and developer profiles;
- citations returned by search and AI retrieval systems.

Classify each surface:

- `API_WRITE`: supported read and write interface;
- `API_READ`: supported inspection but browser-only or unsupported writes;
- `BROWSER`: authenticated UI is the supported control;
- `UNCONTROLLED`: observe or request correction only;
- `UNKNOWN`: verify current official documentation before acting.

Read [references/providers.md](references/providers.md) when a listed provider is in scope.

### 3. Check readiness

Run non-secret authentication checks before asking the user to log in. Examples include `gh auth status`, `vercel whoami`, and `npm whoami`.

For every provider, report:

- authenticated identity as a masked label unless the exact identity is required to resolve ambiguity, without exposing tokens;
- required organization or property role;
- available read and write operations;
- missing setup;
- whether Computer Use is required;
- the exact human checkpoint.

Prefer short-lived credentials, OAuth, workload identity, or trusted publishing over long-lived tokens. Use least privilege.

When an existing 1Password Environment is part of the control plane:

- list variable names and confirm required names without revealing values;
- preserve existing variable names and report the provider-to-variable mapping; do not create aliases merely to enforce a new naming preference;
- inject variables only into the provider command or verification subprocess;
- verify the provider through a sanitized identity, property, or status response;
- if a refresh response rotates a refresh token, update it directly in 1Password before the next request, then reverify access without printing either token or the raw response;
- remove redundant credential copies only when the user has authorized that exact cleanup and after injection and provider access both succeed.

### 4. Audit the live state

Compare meaning, not blind string equality.

Mark each surface:

- `CURRENT`: accurately reflects the approved direction;
- `PROJECT_SPECIFIC`: accurately describes its project without redefining the company;
- `NEUTRAL`: does not make a conflicting claim;
- `STALE`: presents retired positioning as current;
- `INACCESSIBLE`: cannot be verified with available access.

Record URLs, states, and concise evidence in the task response by default. Do not reproduce stale language more than necessary.

### 5. Remediate in dependency order

Use this order:

1. canonical editorial source;
2. site metadata, structured data, discovery files, sitemap, and retired URL behavior;
3. repository and package source metadata;
4. preview deployment and verification;
5. production deployment and verification;
6. source-host, registry, social, community, and directory profiles;
7. indexing and removal notifications;
8. retrieval checks.

After every external write, read the surface again and verify the saved state.

Do not:

- rewrite history to erase old positioning;
- unpublish packages when deprecation is sufficient;
- delete repositories, accounts, properties, or profiles without explicit authorization;
- change legal entity, founding, employee, location, or regulatory fields without evidence;
- publish a package solely to force a company slogan onto a project-specific page unless the live release is materially misleading.

### 6. Verify production before reindexing

Confirm:

- current URLs return `200`;
- permanently retired URLs return `410` or a genuine `404`;
- arbitrary unknown URLs return a genuine non-indexable `404`, not indexable fallback HTML with `200`;
- retired URLs are absent from the sitemap and internal links;
- the intended scheme and host variants resolve to one canonical production host without competing canonical ownership;
- preview and other non-production hosts are durably `noindex` and do not claim canonical ownership;
- declared crawl and social assets, such as robots policy, sitemap, machine-readable discovery files, and social-preview images, return their expected status, content type, and content without authentication redirects or server errors;
- canonical URLs, metadata, social metadata, structured-data identifiers, and rendered copy are mutually consistent;
- the production deployment corresponds to the approved source revision.

Stop reindexing if any production check fails.

### 7. Notify indexers

Use supported controls:

- submit or resubmit sitemaps through APIs where available;
- submit materially changed URLs where a supported endpoint exists;
- request removals only for verified obsolete URLs;
- use browser-based priority indexing or removal tools when no supported API exists;
- avoid general indexing APIs whose eligibility does not match the content type.

Recheck provider status after submission and capture the returned status or receipt.
After an interruption, inspect existing provider status or receipts before retrying so notifications remain idempotent.

### 8. Test retrieval convergence

Use stable, neutral questions in fresh sessions across relevant search and AI systems. Include:

- who or what the principal is;
- what it builds;
- who it serves;
- its current direction;
- whether a retired category is still primary.

Classify answers:

- `CURRENT`;
- `MIXED`;
- `STALE`;
- `UNKNOWN`.

Trace every stale answer to its cited sources. Correct a controlled cited source; request correction from an uncontrolled source; otherwise classify it as cache or model lag. Do not distort canonical copy to chase uncited model output.

Run checks after submission and at sensible later intervals such as Days 3, 7, 14, and 28.

### 9. Close or continue

Close only when:

- reviewed controlled sources are current, project-specific, or neutral;
- production checks pass;
- applicable sitemap, URL, and removal requests were accepted;
- no stale retrieval result cites a controlled stale source across consecutive checks.

Report uncontrolled caches and model-only lag separately.

## Browser policy

When a supported operation requires a web interface:

1. Use Computer Use to operate the default browser.
2. Navigate to the official provider domain.
3. Inspect the current value before editing.
4. Prepare the smallest necessary change.
5. Pause for login, MFA, CAPTCHA, consent, billing, legal terms, or unclear destructive confirmation.
6. Save only after the target and new value are verified.
7. Reopen or refresh the public surface to confirm the result.

Do not name or depend on a specific browser product.

## Response contract

Lead with the outcome. Include:

- canonical source and approval state;
- readiness by provider;
- controlled-surface findings;
- completed and blocked actions;
- index submission status;
- remaining browser checkpoints;
- next monitoring date or completion criteria.

Keep secrets, raw tokens, full account and provider identifiers, private property details, unpublished URLs, stale snippets, and unnecessary operational logs out of the response.
