# Atlassian (Jira) agent tooling: raw findings

Collected 2026-11-02. Every claim has a URL and a short verbatim quote. "Observed on box" means seen in tool schemas on this machine, not in docs. UNVERIFIED marks anything with no official source.

## 1. Atlassian Rovo MCP Server (remote MCP)

### Endpoints
- Recommended endpoint: `https://mcp.atlassian.com/v2/mcp`. Source: https://developer.atlassian.com/cloud/rovo-mcp/ ("https://mcp.atlassian.com/v2/mcp").
- v1 endpoints still supported: `https://mcp.atlassian.com/v1/mcp/authv2` and `https://mcp.atlassian.com/v1/mcp`. The legacy SSE endpoint `https://mcp.atlassian.com/v1/sse` stops after 30 June 2026 (date already passed on 2026-11-02). Source: https://github.com/atlassian/atlassian-mcp-server (README).
- Flat tool list for gateways: "a paginated flat list is available at `https://mcp.atlassian.com/v2/mcp?tools=all`". Source: https://developer.atlassian.com/cloud/rovo-mcp/guides/supported-tools/

### Auth
- "The server initiates a secure OAuth 2.1 authorization flow (or accepts an API token for headless authentication)." Source: https://developer.atlassian.com/cloud/rovo-mcp/
- API token needs admin enablement: "If your organization admin has enabled it, authentication via API token". Source: https://developer.atlassian.com/cloud/rovo-mcp/guides/getting-started/
- README: a personal token goes in a Basic auth header, and a service account API key goes in a Bearer header. JSM tools are API token only and Compass tools are OAuth only. Source: https://github.com/atlassian/atlassian-mcp-server
- Per-product auth on the tools page: `search_code` and Teams groups are "OAuth 2.1 only" (fetch summary). Source: https://developer.atlassian.com/cloud/rovo-mcp/guides/supported-tools/

### Plans / editions
- The Jira pricing page feature matrix lists "Rovo MCP Server" for Standard, Premium and Enterprise, not Free. Description: "Connect Jira, Confluence, Bitbucket, and more to Claude, ChatGPT, Cursor, VS Code, and other AI tools, so they act on your work with your existing permissions." Source: https://www.atlassian.com/software/jira/pricing (from the page's embedded plan data)
- The developer and support MCP docs do not name plans. Source: https://support.atlassian.com/atlassian-rovo-mcp-server/docs/use-atlassian-rovo-mcp-server/ (no plan text found).
- A community thread says MCP is "free on all Cloud plans" (forum answer, not docs). This conflicts with the pricing matrix. UNVERIFIED.

### Rate limits
- Official MCP docs publish no MCP call limits. I found none on the developer docs, support docs or README.
- Search snippets quote atlassian.com/platform/rovo-mcp: "Free: 500 calls per hour • Standard: 1000 calls per hour • Premium/Enterprise: 1000 calls per hour (+ 20 additional calls per user with up to 10,000 calls per hour)". WebFetch got a truncated page and could not confirm this. UNVERIFIED (snippet only). Source: https://www.atlassian.com/platform/rovo-mcp
- Community thread title: "Clarification on Atlassian Rovo MCP Server Rate Limits (10,000 calls on Enterprise Plan)". Source: https://community.atlassian.com/forums/Rovo-questions/Clarification-on-Atlassian-Rovo-MCP-Server-Rate-Limits-10-000/qaa-p/3264375
- GitHub issue #171 reports 429s from concurrency: "after roughly 20 parallel calls, with only ~200–300 total calls made over a couple of hours" and "We don't see `x-ratelimit-limit`, `x-ratelimit-remaining`...". Maintainer, Sep 27 2026: "We're investigating this internally." No numbers were given. Source: https://github.com/atlassian/atlassian-mcp-server/issues/171

### Admin controls
- Settings location: "Connectors, then Atlassian MCP server". API token: "In the Authentication section, turn API token on or off." Domains: "Deselect Allow Atlassian supported domains" and "You can add domains you trust to enable integrations with specific AI tools." Source: https://support.atlassian.com/security-and-access-policies/docs/control-atlassian-rovo-mcp-server-settings/
- The settings page does not describe a single switch that turns MCP off.
- IP allowlist applies to MCP traffic. README: hosted AI clients may send traffic from provider IP ranges. IP allowlisting itself is Premium and Enterprise only (pricing matrix, "IP allowlisting": Premium, Enterprise). Sources: https://github.com/atlassian/atlassian-mcp-server and https://www.atlassian.com/software/jira/pricing
- Admin-gated groups: per the README, `delete_jira` and `manage_jira` "must be enabled by an admin before they can be used." Source: https://github.com/atlassian/atlassian-mcp-server
- Audit: per the README, tool usage is logged under Insights, Audit log, filterable for "Rovo MCP User Actions". Source: https://github.com/atlassian/atlassian-mcp-server
- Permission groups: "Admins grant or revoke access at the group level" (search summary of the tools page). Source: https://developer.atlassian.com/cloud/rovo-mcp/guides/supported-tools/

### Documented tool list and count
Source: https://developer.atlassian.com/cloud/rovo-mcp/guides/supported-tools/
- Primary vs deferred: "Primary tools are marked *(Primary)* below. They're returned directly in the MCP `tools/list` response and are always visible to clients." "Deferred tools are found at runtime through the `discover` tool, which takes a natural-language description of what you want to do, and are then invoked with `executeRead`, `executeWrite`, or `executeDestructive` depending on the operation's risk tier."
- Total documented catalog: 248 unique tool names, counted from the raw page tables on 2026-11-02. That is 7 common tools plus 241 in permission groups. Jira core has 52 (read_jira 27, write_jira 15, search_jira 1, delete_jira 3, manage_jira 6). The page has no "~330" figure, so the observed "~330 operations" is UNVERIFIED.
- Documented primary tools (22): addOrEditJiraIssueComment, addTeamworkGraphContext, atlassianUserInfo, createConfluenceContent, createJiraIssue, discover, editJiraIssue, executeRead, executeWrite, executeDestructive, getAccessibleAtlassianResources, getConfluenceContent, getJiraIssue, getLoomObjectsContent, getTeamworkGraphContext, getTeamworkGraphObject, listJiraIssueComments, search (beta), searchConfluence, searchJiraIssuesUsingJql, transitionJiraIssue, updateConfluenceContent.
- The changelog confirms listJiraIssueComments moved to primary on Oct 28, 2026: "Previously it was a deferred tool, reachable only through `discover` followed by `executeRead`." Source: https://developer.atlassian.com/cloud/rovo-mcp/changelog/
- Deferred and relevant to the observed notes: `listJiraIssueTransitions` (read_jira) and `uploadAttachmentToJiraIssue` (write_jira) are both in the docs as non-primary. This matches "via discover/execute".
- Common, non-primary, documented: `getContentFormatGuide`: "Get format guidance for rich content and Confluence Remix prompts."

### Diff: observed 26 vs documented 22 primary
- Exact match (19): addOrEditJiraIssueComment, atlassianUserInfo, createConfluenceContent, createJiraIssue, discover, editJiraIssue, executeDestructive, executeRead, executeWrite, getAccessibleAtlassianResources, getConfluenceContent, getJiraIssue, getLoomObjectsContent, listJiraIssueComments, search, searchConfluence, searchJiraIssuesUsingJql, transitionJiraIssue, updateConfluenceContent.
- Name differs (3): the box shows addGraphContext, getGraphContext and getGraphObject. The docs show addTeamworkGraphContext, getTeamworkGraphContext and getTeamworkGraphObject. The raw page has 0 hits for "getGraphContext". The names may differ by client prefixing or by a rename; I found no doc for either cause. UNVERIFIED.
- On box only, not in docs (4 beta): getCollaborators, getPeopleInfo, getWorkActivity, getWorkPortfolio. The raw page has 0 hits for each, and the changelog does not mention them. UNVERIFIED as documented tools.

### Rovo credits
- "A typical request uses 15–30 Rovo credits" (Confluence infographic and Maui app tools). "The vast majority of enriched TWG API and tool calls are 1-10 Rovo credits per call." search: "May consume up to 10 Rovo credits per call". Source: https://developer.atlassian.com/cloud/rovo-mcp/guides/supported-tools/
- "When an AI client calls via Atlassian MCP to retrieve data or generate insights, it consumes Rovo credits." "credit usage is per call." Source: https://support.atlassian.com/rovo/docs/atlassian-remote-mcp-server
- Credits come from the shared pool: "These credits come from the same shared pool used by Rovo Chat, Studio, Agents, and the Teamwork Graph". Source: https://support.atlassian.com/atlassian-rovo-mcp-server/docs/use-atlassian-rovo-mcp-server/
- Allowances: Jira Standard 25, Premium 70, Enterprise 150 credits per user per month. Overage: "$0.01 per Rovo credit". "On December 3, 2026, extra usage billing takes effect for Rovo credits." Paid plans only: "included in all paid Jira, Confluence, Service Collection and Teamwork Collection cloud subscriptions". The page lists no Free allowance. Per the page, installing MCP and single-product write or lookup calls are free, while enriched calls cost credits. Source: https://support.atlassian.com/organization-administration/docs/usage-limits-in-atlassian-intelligence/
- The pricing page confirms "25 Rovo credits per user per month / 100 indexed objects per user" (Standard), 70/250 (Premium) and 150/625 (Enterprise). Source: https://www.atlassian.com/software/jira/pricing

## 2. Atlassian CLI (acli)

- Install (Linux): `curl -LO "https://acli.atlassian.com/linux/latest/acli_linux_amd64/acli"`, then `chmod +x ./acli`. Support window: "Each CLI version will only be supported 6 months after release". No plan requirement is stated. Source: https://developer.atlassian.com/cloud/acli/guides/install-linux/
- Auth: `acli jira auth login --web` (OAuth, "Authenticate using web browser"), or `acli jira auth login --site "<site>" --email "<email>" --token` with the token on stdin ("Read token from standard input"). Source: https://developer.atlassian.com/cloud/acli/reference/commands/jira-auth-login/
- Admin auth: `acli admin auth login --email admin@atlassian.com --token < token.txt` takes an org API key: "Authenticate for the organization admin-specific tasks." Source: https://developer.atlassian.com/cloud/acli/reference/commands/admin-auth-login/
- Top-level groups: `admin` (auth, user), `feedback`, `jira` (auth, board, dashboard, field, filter, project, sprint, workitem), `rovodev` (auth). Source: https://developer.atlassian.com/cloud/acli/reference/commands/
- `jira workitem` subcommands: archive, assign, attachment (attachment-delete, attachment-list), clone, comment (comment-create, comment-delete, comment-list, comment-update, comment-visibility), create, create-bulk ("Bulk create Jira issues."), delete, edit, link, search, transition, unarchive, view, watcher (watcher-remove). Source: https://developer.atlassian.com/cloud/acli/reference/commands/jira-workitem/
- Attachment upload: not documented. The attachment group lists only delete and list. UNVERIFIED that any upload exists.
- `jira project`: archive, create, delete, list, restore, update, view. Source: https://developer.atlassian.com/cloud/acli/reference/commands/jira-project/
- `jira board`: list-sprints, search. Source: https://developer.atlassian.com/cloud/acli/reference/commands/jira-board/
- `jira sprint`: list-workitems. Source: https://developer.atlassian.com/cloud/acli/reference/commands/jira-sprint/
- `jira filter`: add-favourite, change-owner, list, search. Source: https://developer.atlassian.com/cloud/acli/reference/commands/jira-filter/
- `jira dashboard`: search. Source: https://developer.atlassian.com/cloud/acli/reference/commands/jira-dashboard/
- `jira field`: cancel-delete, create, delete. Source: https://developer.atlassian.com/cloud/acli/reference/commands/jira-field/
- `admin user`: activate, cancel-delete, deactivate, delete. Source: https://developer.atlassian.com/cloud/acli/reference/commands/admin-user/
- Labels: create has `-l, --label strings`. Edit has `-l, --labels string` ("Edit the labels") and `--remove-labels string`. Sources: https://developer.atlassian.com/cloud/acli/reference/commands/jira-workitem-create/ and https://developer.atlassian.com/cloud/acli/reference/commands/jira-workitem-edit/
- Bulk by JQL: edit has `--jql string` ("JQL query for work items to be edited"), `--filter`, `--ignore-errors` and `-y, --yes`. Transition has `--jql string` ("JQL query for work items to be transitioned"), `-s, --status`, `--yes`. Example: `acli jira workitem edit --jql "project = TEAM" --assignee "user@atlassian.com"`. Sources: https://developer.atlassian.com/cloud/acli/reference/commands/jira-workitem-edit/ and https://developer.atlassian.com/cloud/acli/reference/commands/jira-workitem-transition/
- JSON output: `--json` ("Generate a JSON output") on create, edit, search and transition. Search also has `--csv`, `--paginate`, `--limit`, `--count` and `--fields`. Example: `acli jira workitem search --jql "project = TEAM" --limit 50 --json`. Source: https://developer.atlassian.com/cloud/acli/reference/commands/jira-workitem-search/
- Rate limits or plan requirements for acli: none documented on the pages I fetched. UNVERIFIED. By inference, token-auth traffic falls under the REST API token rules in section 3.
- acli is not installed on this box (`acli: command not found`), so I could not run local `--help`.

## 3. Jira Cloud REST rate limits
Source: https://developer.atlassian.com/cloud/jira/platform/rate-limiting/
- Model: Jira runs three independent limits: an hourly points quota, per-second burst limits per endpoint, and per-issue write limits. Each request has "a base cost of 1 point". Quotas "reset at the top of each UTC hour".
- Quotas: the Global Pool "shares a single 65,000 point hourly quota across all tenants". Per-tenant pools (after Atlassian review): Free 65,000 points per hour, Standard 100,000 + 10 per user, Premium 130,000 + 20 per user, Enterprise 150,000 + 30 per user. "Per-tenant rate limits are capped at 500,000 points per hour".
- Burst: 100 req/s for GET and POST, 50 for PUT and DELETE (defaults). Per-issue writes: 20 per 2 s and 100 per 30 s.
- 429: every limit returns "429 Too Many Requests", and `RateLimit-Reason` names which limit was hit. `Retry-After` "Indicates how many seconds to wait before retrying." On quota exhaustion, "All requests are denied until the next hourly reset."
- Scope: the points model "will apply to all Forge, Connect, and OAuth 2.0 (3LO) apps". API token traffic "is not affected by this change" and "will continue to be governed by existing burst rate limits". Enforcement "will begin on March 2, 2026".

## 4. Jira Cloud pricing and agent governance
Source: https://www.atlassian.com/software/jira/pricing (from the page's embedded JSON-LD and plan matrix, fetched 2026-11-02)
- Free: "Free forever for 10 users", price "0". Standard: "price":"8.48" USD, billingDuration "P1M", per "user". Premium: "price":"15.56" USD per user per month. Enterprise: no list price. "Contact our sales team for Enterprise pricing, available only for annual subscriptions." (eligibleQuantity minValue 801 users). The page does not say whether 8.48 and 15.56 assume annual or monthly billing. UNVERIFIED.
- User limit per site: "10 users" (Free) and "100,000 users" (paid). Storage: 2 GB (Free), 250 GB (Standard), unlimited (Premium and Enterprise).
- Audit logs: "Audit logs - site changes" on Standard, Premium and Enterprise. "Audit logs - user activity" ("Comprehensive audit logging of user-initiated activity in Jira, including permission changes.") on Enterprise only.
- SSO: "Atlassian Guard Standard (SSO, SCIM, Active Directory Sync)" shows "Requires Atlassian Guard Standard subscription" for Free, Standard and Premium, and "Included" for Enterprise.
- Guard price: Standard "$4.35" "per user / month" (includes "Enforced single sign-on (SSO)", "API token controls", "Organization audit log"). Premium "$8.55" per user per month. Source: https://www.atlassian.com/software/guard/pricing
- Permissions: "In the Free plan, every user is a admin." and "Permission settings for spaces or work items are only available on paid plans."
- Sandbox: Premium and Enterprise. IP allowlisting: Premium and Enterprise. Rovo Studio: Premium and Enterprise. Admin insights: Premium and Enterprise.
- Agents: "Agents in Jira" (Standard, Premium, Enterprise): "Turn plans into progress by assigning work to AI agents and tracking their progress alongside your team's work in Jira." "Agent Sessions" (Standard and up): "The Agent Sessions tab on your Jira For You page tracks all agent activity across spaces in one place."
- Third-party agents (Standard, Premium, Enterprise): "Bring third-party agents into Jira alongside Rovo, including coding agents like Claude, Cursor, and GitHub Copilot. Assign them, mention them, and run them in workflows, with every session tracked in Jira."
- Assigning work to agents: you can assign work to "a Rovo agent by Atlassian, a Rovo agent created by someone on your space, and agents built by third parties." "You'll need to be a site admin to enable Rovo, AI features, or MCP agents." Credits: agents are "a premium AI feature that consume[s] Rovo credits", and "Rovo credit allowances will be applied starting December 3, 2026." Source: https://support.atlassian.com/jira-software-cloud/docs/collaborate-on-work-items-with-ai-agents/
- Coding agents in Jira automation: the page lists GitHub Copilot in Jira, Cursor in Jira and Claude in Jira. "This experience is currently in beta." Site setup needs "Administer Jira" permissions. Source: https://support.atlassian.com/jira-software-cloud/docs/use-third-party-coding-agents-in-jira-automation/
- Rovo Dev: "Rovo Dev CLI understands the code in your repo and acts on your plans in Jira." It "is reaching end of life as a standalone product", and its capabilities are "moving directly into eligible Jira and Teamwork Collection (TWC) subscriptions." Source: https://www.atlassian.com/software/rovo-dev

## 5. Webhooks, notifications, audit log, API tokens
- Webhooks (all plans; the page names no tier): you register them in Jira admin, in a Connect descriptor, or via `POST /rest/api/3/webhook`. "For an OAuth 2.0 app, the limit is 5 webhooks per app per user on a tenant." Dynamic webhooks expire: "The expiration period is 30 days". Retries: "Jira Cloud will attempt to resend it up to five times." Source: https://developer.atlassian.com/cloud/jira/platform/webhooks/
- Notifications (no tier stated): "you must be logged in as a user with the Jira Administrators global permission." Schemes map events to email recipients per space. Source: https://support.atlassian.com/jira-cloud-administration/docs/configure-notification-schemes/
- Audit log (paid only): "The audit log isn't available if all of your Jira Cloud apps are on the Free plan." It records configuration changes, and viewing needs "the Administer Jira global permission". Source: https://support.atlassian.com/jira-cloud-administration/docs/audit-activities-in-jira-applications/
- API tokens (all plans): "By default we set API tokens to expire in one year." Range: "from one day up to one year." Scoped tokens: "We recommend you create an API token with scopes because it's more secure." Revoke: "When you revoke a token it no longer works and we permanently remove it from your account." Source: https://support.atlassian.com/atlassian-account/docs/manage-api-tokens-for-your-atlassian-account/
- Admin token oversight: Guard Standard ($4.35/user/month) "API token controls" gives admins "more oversight of who creates and revokes API tokens". Source: https://www.atlassian.com/software/guard/pricing
- Org-wide admin-enforced maximum token lifetime: an open feature request (https://jira.atlassian.com/browse/ID-8808) suggests this has not shipped. UNVERIFIED.
