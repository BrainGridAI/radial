<div align="center">

# Radial

### The fast, keyboard-first issue tracker with no AI bolted on.

No credits, no copilots, no surprises. Bring your own agent via a first-class CLI and MCP.
**$50 per user per year, flat.**

[![npm](https://img.shields.io/npm/v/radial.build?label=radial.build&color=4f46e5)](https://www.npmjs.com/package/radial.build)
&nbsp;[![provenance](https://img.shields.io/badge/npm-provenance-4f46e5)](https://www.npmjs.com/package/radial.build)
&nbsp;[![license](https://img.shields.io/badge/license-MIT-555)](./LICENSE)

[**radial.build**](https://radial.build) · [Developers](https://radial.build/developers) · [MCP](https://mcp.radial.build)

</div>

---

This is Radial's **developer surface** — the `radial` CLI, the MCP server, and the REST API.
Built to be scripted by you and your agents. The Radial app itself lives at
[radial.build](https://radial.build); this repo is the home of the tooling and its releases.

## Install

```bash
# npm — any platform with Node 18+
npm install -g radial.build

# Homebrew — macOS / Linux
brew install BrainGridAI/radial/radial

# or the single binary, no runtime needed
curl -fsSL https://radial.build/cli/install.sh | sh
```

Then run `radial`.

## Quickstart

```bash
radial auth                                              # device-flow sign-in (opens your browser)
radial create "Search flashes an empty state" -p high -l bug -a me
radial list --status open --assignee me
radial show RAD-219
```

## Commands

| Command | What it does |
| --- | --- |
| `radial auth` | Device-flow sign-in; stores a session under `~/.config/radial/` |
| `radial create <title>` | Create an issue. `-p` priority, `-l` label (repeatable), `-a` assignee, `-t` team |
| `radial list` | List issues. `--assignee`, `--status`, `--label`, `--team`, `--priority`, `--json` |
| `radial show RAD-219` | Full detail + comments |
| `radial close RAD-219` | Close, with optional `-m "message"` |
| `radial triage` | Step through the triage queue |
| `radial search <query>` | The same fast index the app uses |
| `radial import --from linear\|jira <file>` | Deep import (issues, labels, projects, parents, relations, comments). `--dry-run` first |
| `radial export` | Full workspace export. `--format json\|csv`, `-o file` |
| `radial mcp` | Run the MCP server over stdio for any MCP-capable agent |

Add `--json` to any read command to pipe into `jq` and friends.

## MCP

Point any MCP-capable agent (Claude, etc.) at Radial.

**Remote (recommended)** — authorizes over OAuth in the browser, no keys to paste:

```json
{ "mcpServers": { "radial": { "url": "https://mcp.radial.build" } } }
```

**Local stdio** — run the server yourself, using your `radial auth` session:

```json
{ "mcpServers": { "radial": { "command": "radial", "args": ["mcp"] } } }
```

Tools: `create_issue`, `update_issue`, `search_issues`, `list_issues`, `comment`,
`close_issue`, `list_projects`, `triage_queue`.

## REST API

Base URL `https://api.radial.build/v1`. Authenticate with a Bearer **API key**
(`rk_…`, created in **Settings → Developers**) or via OAuth 2.1.

```bash
curl https://api.radial.build/v1/issues \
  -H "Authorization: Bearer rk_full_xxxxxxxx"
```

Resources: `issues`, `projects`, `search`, `triage`, `export`, `import`, `meta`.
Full reference at [radial.build/developers](https://radial.build/developers).

## Configuration

State lives in `~/.config/radial/config.json` (mode `0600`). Override endpoints with
`RADIAL_API_URL`, `RADIAL_AUTH_URL`, `RADIAL_MCP_URL` — handy for self-hosting.

## License

MIT — see [LICENSE](./LICENSE).
