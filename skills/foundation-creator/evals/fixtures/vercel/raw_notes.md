# Vercel Source Packet

Assembled on April 20, 2026 from official Vercel sources.

This packet is intentionally paraphrased. It is meant to test whether
`foundation-creator` can turn a modern company/product platform into a durable
foundation document without collapsing brand transition into fake certainty.

## Source 1

- URL: [https://vercel.com/about](https://vercel.com/about)
- Accessed: April 20, 2026
- The About page says Vercel "enables the world to ship the best products."
- It describes the `Frontend Cloud` as the developer experience and
  infrastructure to build, scale, and secure a faster, more personalized web.
- Its brand values emphasize products that are easy, universal, and
  accessible.

## Source 2

- URL: [https://vercel.com/docs](https://vercel.com/docs)
- Last updated: January 30, 2026
- The docs index now describes Vercel as the `AI Cloud`, a unified platform
  for building, deploying, and scaling AI-powered applications.
- The docs say Vercel can ship web apps, agentic workloads, and "everything in
  between."
- Git-connected deployment is still central: connect a repository and deploy
  on every push, with automatic preview environments before production.
- Build surfaces listed in the docs include `Next.js`, `Functions`, `Routing
  Middleware`, `Incremental Static Regeneration`, `Image Optimization`,
  environment management, and feature flags.
- AI surfaces listed in the docs include `v0`, `AI SDK`, `AI Gateway`,
  `Agents`, `MCP Servers`, `Agent Resources`, `Sandbox`, and claim
  deployments.
- Collaboration surfaces listed in the docs include `Toolbar`, `Comments`, and
  `Draft mode`.
- Security surfaces listed in the docs include `Deployment Protection`,
  `RBAC`, `Configurable WAF`, `Bot Management`, and `BotID`.

## Source 3

- URL: [https://vercel.com/docs/getting-started-with-vercel](https://vercel.com/docs/getting-started-with-vercel)
- Last updated: September 24, 2025
- Vercel is described as a platform for developers that provides tools,
  workflows, and infrastructure to build and deploy web apps faster without
  needing additional configuration.
- The getting started guide says Vercel supports popular frontend frameworks
  out of the box.
- It also says the infrastructure is globally distributed.
- During development, Vercel provides preview and production environments and
  comments for real-time collaboration.
- The docs repeatedly support both dashboard and CLI workflows.

## Source 4

- URL: [https://vercel.com/blog/introducing-vercel-mcp-connect-vercel-to-your-ai-tools](https://vercel.com/blog/introducing-vercel-mcp-connect-vercel-to-your-ai-tools)
- Published: August 6, 2025
- Vercel launched an official MCP server in public beta.
- The launch framing says AI tools lacked secure, structured access to
  infrastructure like Vercel.
- The launch post describes Vercel MCP as a secure, OAuth-compliant interface
  that lets AI clients interact with Vercel projects.
- The launch capabilities include searching docs, retrieving deployment logs,
  fetching teams, and fetching projects.
- The launch post explicitly frames the initial server as read-only and
  approved-client only.
- The launch post also says Vercel wants to be a place where developers ship
  their own MCP servers.

## Source 5

- URL: [https://vercel.com/docs/agent-resources/vercel-mcp](https://vercel.com/docs/agent-resources/vercel-mcp)
- Last updated: January 30, 2026
- The product docs describe Vercel MCP as Vercel's official remote MCP with
  OAuth at `https://mcp.vercel.com`.
- The docs say it lets AI tools search docs, manage projects and deployments,
  and analyze deployment logs.
- Supported AI clients listed in the docs include Claude, ChatGPT, Codex CLI,
  Cursor, VS Code with Copilot, Devin, Raycast, Goose, Windsurf, and Gemini
  tools.
- The docs emphasize allowlisted clients, OAuth, and official endpoint
  verification as security controls.
- There is a likely product transition to capture: the August 6, 2025 launch
  post frames the service as read-only, while the January 30, 2026 product
  docs frame it as broader project and deployment management.

## Source 6

- URL: [https://vercel.com/platforms/docs](https://vercel.com/platforms/docs)
- Accessed: April 20, 2026
- Vercel for Platforms supports two patterns: `Multi-Tenant` and
  `Multi-Project`.
- The docs say `Multi-Tenant` is for one application structure with
  tenant-specific content and branding.
- The docs say `Multi-Project` is for unique codebases, per-customer
  environments, and AI coding platforms where complete isolation is required.
- This suggests Vercel is not only a deployment product for a single app team;
  it is also a substrate for other platforms.

## Tensions and questions the evaluator should preserve

- Vercel still publicly uses `Frontend Cloud` language on the About page while
  the docs index now centers `AI Cloud`.
- The same company appears to span deployment infrastructure, collaboration,
  security, AI application tooling, and platform-building primitives.
- It should be treated as more than hosting, but not flattened into generic
  cloud infrastructure.
- A good foundation document should preserve whether the core primitive is
  "ship products fast", "deploy web and AI apps", "developer cloud", or
  "infrastructure for the product surface of the internet" if the sources do
  not settle it cleanly.
