# Provider capability reference

Use this reference to plan access and select supported interfaces. Verify current official documentation before writes because provider capabilities and access tiers change.

## Capability matrix

| Surface | Supported automation | Browser or human boundary | Preferred setup |
|---|---|---|---|
| 1Password Environment | Environment and variable inventory, runtime injection, variable updates | Account sign-in, device trust, MFA, consent | Official 1Password integration and CLI; one `<principal-slug>-public-presence` Environment per principal |
| Website and deployment platform | Build, preview, deploy, inspect, logs, aliases, domains, HTTP verification | Billing, account recovery, some domain ownership challenges | Provider CLI or REST API with least-privilege token |
| Git source host | Organization and repository metadata, topics, profile repository content, releases, workflows | Account security, some organization policy changes | Official CLI, REST/GraphQL API, or app installation |
| npm registry | Read metadata, publish, stage, deprecate, dist-tags, owners, access, provenance, trusted publishers | Login, MFA, staged approval, account recovery | Trusted publishing through OIDC; interactive CLI for admin actions |
| Google Search Console | Properties, search analytics, sitemap submit/list/delete, indexed-version inspection | Live inspection, ordinary-page Request Indexing, temporary removals | OAuth 2.0 with Search Console scopes and property access |
| Bing Webmaster | Site data, sitemap submission, URL submission and batches, quotas, URL information | Initial verification, consent, ambiguous removal cases | OAuth 2.0 preferred; API key where appropriate |
| IndexNow | Added, updated, and deleted URL notifications | Domain key must be hosted and maintained | Use only when the user accepts the persistent verification key |
| LinkedIn company page | Organization data, content, roles, and analytics after approval | Developer-product vetting, admin consent, unsupported page fields | Vetted Community Management application; browser fallback |
| X profile | Supported public reads and content APIs | Treat profile bio and website edits as browser-managed unless a current official write endpoint is verified | OAuth for supported APIs; browser for profile settings |
| Discord community | Guild settings including description with appropriate bot permission | Bot installation and permission grant | Bot token with `MANAGE_GUILD`, stored securely |
| Package mirrors and directories | Usually public reads | Refresh and correction controls vary; many have none | Use owner refresh controls when available |
| Search and AI retrieval | Automated queries may help monitor | Consumer UI behavior may differ from API behavior; no direct knowledge correction | Use APIs for repeatable monitoring and browser checks for consumer parity |

## Provider notes

### 1Password

- Discover and reuse the existing `<principal-slug>-public-presence` Environment before creating one.
- Keep each principal in a separate Environment even when one 1Password account contains multiple Environments.
- Treat variable names as non-secret metadata. Environment IDs are not authentication secrets, but they are sensitive operational metadata: mask or omit them by default. Treat every variable value as secret.
- Use the official 1Password MCP integration for Environment inventory and updates.
- Use `op run --environment <environment-id> -- <command>` for runtime injection when the installed CLI supports Environments.
- Keep OAuth client IDs, client secrets, and refresh tokens in the Environment. Do not mirror them to Keychain or dotenv files.
- A sanitized verification command may report variable presence and status. Mask account identities, Environment IDs, and private property URLs unless an exact value is required to resolve ambiguity. Never report raw values or token responses.
- After verification, remove task-created OAuth exports, callback captures, helper files, FIFOs, and local Environment mounts. Do not remove user-created material without explicit authorization.

Official references:

- https://developer.1password.com/docs/environments/
- https://developer.1password.com/docs/cli/secrets-environment-variables/

### GitHub

- Check readiness with `gh auth status`.
- Use `gh api` or official REST/GraphQL endpoints for organization and repository metadata.
- Treat an organization profile README as repository content.
- Verify organization-owner or repository-admin permission before writes.

Official references:

- https://docs.github.com/en/rest/orgs/orgs
- https://docs.github.com/en/rest/repos/repos
- https://docs.github.com/en/rest/using-the-rest-api/getting-started-with-the-rest-api?tool=cli

### Vercel

- Check readiness with `vercel whoami`.
- Use the CLI or REST API for deployment, logs, aliases, domains, and project state.
- Prefer the existing Git integration and pull-request flow when present.

Official references:

- https://vercel.com/docs/cli
- https://vercel.com/docs/deployments
- https://vercel.com/docs/rest-api

### npm

- Check local readiness with `npm whoami`.
- Inspect without authentication using `npm view`.
- Prefer OIDC trusted publishing over long-lived write tokens.
- Published version metadata is immutable in practice; update README and manifest metadata through a new release.
- Deprecate obsolete versions rather than unpublishing them.
- Expect MFA or proof-of-presence for sensitive administration.

Official references:

- https://docs.npmjs.com/trusted-publishers/
- https://docs.npmjs.com/cli/v11/commands/npm-trust/
- https://docs.npmjs.com/cli/v11/commands/npm-publish/
- https://docs.npmjs.com/deprecating-and-undeprecating-packages-or-package-versions/
- https://api-docs.npmjs.com/

### Google Search Console

- Reuse one dedicated Google Cloud project per principal whose display name is `<principal-slug>-public-presence` to enable the API and create OAuth credentials. Do not share a project or OAuth client across principals; a common Cloud organization may contain their separate projects.
- Keep the editable display name in lowercase kebab-case. Prefer the same base for a new project ID, but accept provider-added uniqueness suffixes. Rename only the display name; a project ID cannot be changed in place.
- Store OAuth credentials and refresh tokens in the matching 1Password Environment and inject them at runtime.
- Before writes, verify that the authenticated identity, returned property, and access level match the intended principal.
- If a refresh response returns a replacement refresh token, update 1Password before the next request and reverify access without printing the raw token response.
- Use `https://www.googleapis.com/auth/webmasters.readonly` for audits and `https://www.googleapis.com/auth/webmasters` for sitemap writes.
- The URL Inspection API reports Google’s indexed version; it does not perform a live test or request indexing.
- Use the browser for ordinary-page Request Indexing and temporary removals.
- Do not use Google’s Indexing API unless the pages meet its documented structured-data eligibility.

Official references:

- https://developers.google.com/webmaster-tools/v1/api_reference_index
- https://developers.google.com/webmaster-tools/v1/how-tos/authorizing
- https://developers.google.com/webmaster-tools/v1/urlInspection.index/inspect
- https://support.google.com/webmasters/answer/9012289
- https://support.google.com/webmasters/answer/9689846
- https://developers.google.com/search/apis/indexing-api/v3/quickstart

### Bing Webmaster and IndexNow

- Prefer OAuth 2.0 for delegated access.
- Store the OAuth client ID, client secret, and refresh token in the matching 1Password Environment and inject them at runtime.
- Before writes, verify that the authenticated identity and returned site match the intended principal.
- Use Bing Webmaster’s documented authorization server, including `https://www.bing.com/webmasters/oauth/token`; do not substitute a generic Microsoft identity token endpoint.
- After refresh, validate access with a sanitized `GetUserSites` result. If Bing returns a different refresh token, update 1Password directly before the next refresh and never print either token.
- Support sitemap and URL submission through the Webmaster API.
- Check submission quota before batches.
- Microsoft recommends IndexNow for change notifications, but it requires a hosted key.
- Keep permanent HTTP removal behavior even when using a temporary removal control.

Official references:

- https://learn.microsoft.com/en-us/bingwebmaster/
- https://learn.microsoft.com/en-us/bingwebmaster/oauth2
- https://www.bing.com/webmasters/help/URL-Submission-62f2860b
- https://www.bing.com/indexnow/getstarted

### LinkedIn

- Expect a vetted developer product, organization verification, three-legged OAuth, and appropriate company-page roles.
- Use the default browser when API access is absent or the desired field is not supported by the approved product.

Official references:

- https://learn.microsoft.com/en-us/linkedin/marketing/community-management/community-management-overview
- https://learn.microsoft.com/en-us/linkedin/marketing/community-management/organizations

### X

- Use only documented public APIs and approved OAuth flows.
- Do not automate profile settings through internal web endpoints, cookies, or captured sessions.
- Use Computer Use with the default browser for profile edits unless current official documentation proves a supported endpoint.

Official reference:

- https://docs.x.com/x-api/users/lookup/introduction

### Discord

- Use the Modify Guild endpoint only with a properly installed bot and `MANAGE_GUILD`.
- Return control for bot installation or permission changes.

Official reference:

- https://docs.discord.com/developers/resources/guild
