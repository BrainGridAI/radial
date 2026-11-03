# Linear: raw findings (fetched 2026-11-02)

Every quote below came back through a WebFetch summarizer, so treat it as near-verbatim. Re-check against the live page before you publish.

## 1. Official MCP server

Source: https://linear.app/docs/mcp

- Endpoints: read-write `https://mcp.linear.app/mcp`, read-only `https://mcp.linear.app/mcp/readonly`, and the deprecated SSE fallback `https://mcp.linear.app/sse`.
- Transport: Streamable HTTP is the primary transport. SSE is marked as a deprecated fallback.
- Auth: OAuth 2.1 with dynamic client registration. You can also send an OAuth token or a Linear API key directly in the `Authorization: Bearer` header. Read-only access works through the `read` OAuth scope or an API key that has only the Read permission. Okta enterprise-managed authorization is supported, and Claude-issued authentication is in beta.
- Read-only endpoint: "only ever exposes read tools".
- Rate limits: the MCP docs page states none.
- Tool names: NOT LISTED. The page says the server "has tools available for finding, creating, and updating objects in Linear" and mentions "issues, projects, and comments", with "more functionality on the way".
- The launch post (https://linear.app/changelog/2025-05-01-mcp) names no tools either: "finding, creating, and updating objects in Linear like issues, projects, and comments."
- Other official places I checked for a tool list. None of them has one:
  - https://linear.app/developers/mcp returns 404.
  - https://mcp.linear.app/ redirects (302) to docs/mcp.
  - https://github.com/linear/cursor-plugin has an `mcp.json` that holds only `"type": "streamable-http", "url": "https://mcp.linear.app/mcp"`.
  - The README at https://github.com/linear/antigravity-plugin says the plugin "uses Linear's hosted MCP server" and names no tools.
  - The README at https://github.com/linear/linear lists no MCP package.
- Verdict: the tool list and count are UNVERIFIED from official sources. The JSON file leaves the list empty on purpose. Third-party listings (for example mcpbundles.com, which claims "25+ tools") were not used.
- Changelog items that touch MCP:
  - 2026-08-13: "Linear's MCP now supports managing employee access through your existing Okta-managed identity." (https://linear.app/changelog/2026-08-13-team-initiatives#enterprise-managed-authorization-for-mcp)
  - 2026-10-22: "Fixed sub-issues created through MCP or Linear Agent missing their parent's project..." (https://linear.app/changelog)
  - 2026-07-30: "Added Zapier to the built-in MCP connector directory." This refers to Linear Agent's outbound MCP connectors.

## 2. CLI

- General-purpose CLI: no official one found. The changelog page (https://linear.app/changelog) does not mention a CLI. Its only "command" reference is the UI "command menu".
- Official narrow-scope CLIs:
  - `linear/linear-release` (https://github.com/linear/linear-release): "CLI to automatically track releases in Linear". Commands are `sync`, `complete`, and `update`. 70 stars, last pushed 2026-10-20 (per https://api.github.com/orgs/linear/repos). No release version shown.
  - CLI Importer (https://linear.app/docs/cli-importer): a "Command Line interface (CLI) tool" for "moving from a tool without a dedicated Linear import assistant". Source is at github.com/linear/linear/tree/master/packages/import.
- Org repos with no general CLI:
  - `linear` (1,656 stars): "Tools, SDK's and plugins for Linear". Its packages are sdk, import, codegen-doc, codegen-sdk, and codegen-test.
  - Also: cursor-plugin, antigravity-plugin, claude-managed-agents-demo ("Example for connecting Linear Agents SDK with Claude Managed Agents", 92 stars), linear-zapier, and linear-release-action.
- Verdict: as of 2026-11-02, Linear ships no official general-purpose CLI for issues. It does ship two narrow official CLIs: linear-release and the CLI Importer.
- Community CLIs (all unofficial; data from https://api.github.com/search/repositories?q=linear-cli+in:name):

| Repo | Stars | Last push | Description |
|---|---|---|---|
| https://github.com/schpet/linear-cli | 1034 | 2026-10-23 | "linear without leaving the command line: list, start, and create PRs for linear issues. agent friendly." |
| https://github.com/joa23/linear-cli | 146 | 2026-09-13 | "A token-efficient CLI for Linear" |
| https://github.com/nesszer/linear-cli | 138 | 2026-09-13 | "A powerful CLI for Linear.app built with Rust" |
| https://github.com/evangodon/linear-cli | 91 | 2025-10-15 | "A CLI for interacting with the Linear API." |
| https://github.com/mixpeek/linear-cli | 16 | 2025-05-08 | "A CLI tool for interacting with Linear.app" |
| https://github.com/choam2426/Linear-CLI | 9 | 2026-04-03 | "Agent-optimized Linear CLI ... no OAuth, no MCP, no dependencies." |
| https://github.com/aaronkwhite/linear-cli | 7 | 2026-09-06 | "lin: A fast, native CLI for Linear." |

## 3. Agents, AI features, pricing

- Third-party agent platform:
  - https://linear.app/docs/agents-in-linear: "Linear also maintains an open platform for third party agents (including those you build yourself.)" The same page says "Agents are not counted as billable seats in Linear."
  - https://linear.app/developers/agents: "Agents behave similar to other users in a workspace." Agents installed in a workspace "do not count as billable users."
  - Agent model: an Agent Session "tracks the lifecycle of a given agent task." An app installs through OAuth with `actor=app`. Scopes are `app:assignable` ("Allow the app to be assigned as a delegate on issues") and `app:mentionable`.
  - On delegation the agent should "Emit a `thought` activity within 10 seconds". It receives events through "Agent session events" webhooks.
- First-party Linear Agent:
  - https://linear.app/docs/linear-agent: "Linear's native agent can answer questions about your workspace and codebase." It can "Create and update work like issues, projects, milestones and initiatives". It can start coding sessions and connect to external MCP servers (Granola, Notion, Figma). "Linear Agent is available by default in your workspace."
  - Changelog, 2026-09-24 (https://linear.app/changelog/2026-09-24-new-controls-for-linear-coding-agent): "Assign a task to Linear Agent, and it works in a secure cloud environment to write and test the code".
  - Loops (https://linear.app/changelog/2026-07-20-introducing-loops): "Loops are a new way for Linear Agent to take on recurring work for your team."
  - AI credits (https://linear.app/changelog/2026-10-08-stacked-pull-requests): "Admins can now see what's driving AI credit usage and set limits to manage spend."
- Triage Intelligence (https://linear.app/docs/triage-intelligence): "Triage Intelligence automates the time consuming assessment and routing steps required when triaging issues." It is "Available to workspaces on Business and Enterprise plans."
- Partner agents named on https://linear.app/agents: Linear Agent, Cursor, OpenAI Codex, Devin, Sentry, ChatPRD, Oz by Warp, Factory, Charlie, Ranger, and Tembo.
  - GitHub Copilot is announced separately (https://linear.app/changelog/2026-07-30-coding-sessions-on-mobile#github-copilot-for-linear): "GitHub Copilot users can assign issues directly to Copilot's cloud agent from Linear."
  - Claude: I found no partner listing on /agents. The org has a `claude-managed-agents-demo` repo, and the MCP docs mention Claude-issued auth (beta). A Claude partner listing is UNVERIFIED.
- Pricing (https://linear.app/pricing):
  - Free: "$0".
  - Basic: "$10 per user/month", "Billed yearly".
  - Business: "$16 per user/month", "Billed yearly".
  - Enterprise: "Custom", "Annual billing only".
  - The page shows no monthly-billing price.

| Feature | Free | Basic | Business | Enterprise |
|---|---|---|---|---|
| SSO | Google | Google | Google | Google + SAML |
| SCIM | no | no | no | yes |
| Audit log | no | no | no | yes |
| Guests | no | no | yes | yes |
| API and webhooks | yes | yes | yes | yes |
| Agent platform | yes | yes | yes | yes |
| MCP access | yes | yes | yes | yes |
| Linear Agent | yes | yes | yes | yes |
| Triage Intelligence | no | no | yes | yes |
| Code Intelligence | no | no | yes | yes |

  - Coding sessions and Loops are on all tiers but "Require AI credits".
  - The pricing page itself says nothing on seat counting for agents. The docs pages cited above say agents are not billable seats.

## 4. API rate limits

Source: https://linear.app/developers/rate-limiting

- API key: "you can make up to 2,500 requests per hour" and "up to 3,000,000 points per hour".
- OAuth app: 5,000 requests per hour and 2,000,000 points per hour, counted per user (or app user). Table rows: "OAuth App | 5,000 | User (or App User) | 1 hour" and "OAuth app | 2,000,000 | User (or App User) | 1 hour".
- Unauthenticated: "limited to 600 requests per hour" and "100,000 points per hour".
- Per-query cap: "maximum complexity of a single query at any time to 10,000 points."

## 5. Platform features

- Webhooks (https://linear.app/developers/webhooks): "receive HTTP push notifications whenever data is created, updated or removed." "Only workspace admins, or OAuth applications with the `admin` scope, can create or read webhooks." Available on all tiers per the pricing page ("API and webhook access").
- Attachments (https://linear.app/developers/attachments): "Issue attachments allow you to link external resources to issues". No tier is stated (it is part of the API, which is on all tiers).
- Export (https://linear.app/docs/exporting-data): "Workspace admins can export this data". On Enterprise, only owners can export. "Members can export up to 250 issues at a time". Admins can export views of "up to 2,000 issues". "Guest users cannot export issues". No plan restriction is stated.
- Import (https://linear.app/docs/import-issues): the importers are Jira, GitHub Issues, Asana, Shortcut, Linear, and CLI. "Imports can only be started by workspace admins." No plan restriction is stated.
- Audit log (https://linear.app/docs/audit-log): "Audit logs show you a record of workspace events over the last 90 days." It is "Available to workspaces on our Enterprise plan".
- SAML SSO (https://linear.app/docs/saml-and-access-control): "Customers can opt to enable SAML for their workspace to manage logins through an Identity Provider." Enterprise only.
- SCIM (same page): "We support enabling SCIM 2.0 for you on the Enterprise plan if you have SAML enabled."
