# Vercel MCP Source Packet

Assembled on April 20, 2026 from official Vercel sources.

This packet is intentionally narrow. It exists to test whether `spec-creator`
can produce a concrete service specification from a modern product surface
without inventing capabilities that are still in transition.

## Source 1

- URL: [https://vercel.com/blog/introducing-vercel-mcp-connect-vercel-to-your-ai-tools](https://vercel.com/blog/introducing-vercel-mcp-connect-vercel-to-your-ai-tools)
- Published: August 6, 2025
- Vercel introduced an official MCP server in public beta.
- The launch post describes the service as a secure, OAuth-compliant interface
  that lets AI clients interact with Vercel projects.
- The launch motivation is that AI tools need secure, structured access to
  infrastructure like Vercel from inside development environments and AI
  assistants.
- The launch capabilities include searching docs, retrieving deployment logs,
  fetching teams, and fetching projects.
- The launch post says the initial service is read-only.
- The launch post also says only approved clients are allowed, and OAuth
  consent is shown on every connection.
- Official endpoint in the launch post: `https://mcp.vercel.com`.

## Source 2

- URL: [https://vercel.com/docs/agent-resources/vercel-mcp](https://vercel.com/docs/agent-resources/vercel-mcp)
- Last updated: January 30, 2026
- The product docs describe Vercel MCP as Vercel's official remote MCP with
  OAuth.
- The docs say it lets AI tools search docs, manage projects and deployments,
  and analyze deployment logs.
- The docs list many supported clients including Claude tools, ChatGPT, Codex
  CLI, Cursor, VS Code with Copilot, Devin, Raycast, Goose, Windsurf, and
  Gemini tools.
- The docs emphasize endpoint verification, OAuth, and approved-client
  restrictions as security controls.
- The docs position the service as part of an agent workflow around live
  Vercel context and project operations.

## Source 3

- URL: [https://vercel.com/docs](https://vercel.com/docs)
- Last updated: January 30, 2026
- The docs index places Vercel MCP inside a broader AI infrastructure surface
  alongside `Agents`, `MCP Servers`, `Agent Resources`, `Sandbox`, `AI SDK`,
  and `AI Gateway`.
- This suggests Vercel MCP is not an isolated side experiment; it is part of a
  broader AI-tooling platform direction.

## Important boundaries and tensions

- The service is specifically about Vercel context and operations for AI
  clients, not a generic MCP hosting platform.
- The endpoint is official and singular in the notes:
  `https://mcp.vercel.com`.
- August 6, 2025 launch framing is explicitly read-only.
- January 30, 2026 docs language suggests broader project/deployment
  management.
- A good spec should preserve that transition carefully. It should not invent
  arbitrary mutation powers if the source packet does not settle them.
