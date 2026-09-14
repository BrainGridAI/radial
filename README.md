<div align="center">

# Radial

### The fast, keyboard-first issue tracker with no AI bolted on.

No credits, no copilots, no surprises. Bring your own agent via a first-class CLI and MCP.
**$50 per user per year, flat.**

[![npm](https://img.shields.io/npm/v/radial.build?label=radial.build&color=4f46e5)](https://www.npmjs.com/package/radial.build)
&nbsp;[![provenance](https://img.shields.io/badge/npm-provenance-4f46e5)](https://www.npmjs.com/package/radial.build)
&nbsp;[![license](https://img.shields.io/badge/license-MIT-555)](./LICENSE)

[**radial.build**](https://radial.build) · [Docs](https://radial.build/docs) · [Agent skills](https://radial.build/docs/skills) · [Developers](https://radial.build/developers) · [MCP](https://mcp.radial.build)

</div>

---

This is Radial's **developer surface** — the `radial` CLI, the MCP server, the REST API, and
the `rd-*` agent skills. Built to be scripted by you and your agents. The Radial app itself
lives at [radial.build](https://radial.build); this repo is the home of the tooling, the skills
and the releases.

## Install

```bash
# npm — any platform with Node 18+
npm install -g radial.build

# Homebrew — macOS / Linux
brew install BrainGridAI/radial/radial
```

Then run `radial`.

## Quickstart

```bash
radial auth                                              # device-flow sign-in (opens your browser)
radial create "Search flashes an empty state" -p high -l bug -a me
radial list --status open --assignee me
radial show RAD-219
```

## Agent skills

Eleven skills that teach Claude Code and Codex how to work in Radial: plan a change into a
parent and a few children, file the tree with its dependency edges, build it child by child
leaving notes on each issue, and open a pull request that does not auto-close the siblings.
They are prose, not scripts — no code runs on your machine that you did not read.

**60 seconds:**

```bash
radial skills install          # ~/.claude/skills and ~/.agents/skills
radial skills install --project  # .claude/skills and .agents/skills, for a repo
radial skills list
```

Then restart your agent and type `/rd-setup` (Claude Code) or `$rd-setup` (Codex).

Prefer another installer? Both of these read the same folders:

```bash
npx skills add BrainGridAI/radial
codex -- '$skill-installer --repo BrainGridAI/radial --path skills/rd-plan'
```

### The workflow, in order

| Skill | What it does | Extension points |
| --- | --- | --- |
| [`rd-setup`](./skills/rd-setup/SKILL.md) | CLI, sign-in, team, `.radial/config.json`, the `CLAUDE.md` / `AGENTS.md` block, MCP, the pack | `extra-checks`, `extra-config`, `after-setup` |
| [`rd-plan`](./skills/rd-plan/SKILL.md) | An idea becomes one parent and 2–4 children with acceptance criteria, written to `.radial/plans/` | `extra-questions`, `extra-sections`, `extra-checks`, `plan-bar`, `after-plan` |
| [`rd-prototype`](./skills/rd-prototype/SKILL.md) | One self-contained clickable HTML file, attached to the issue with a Preview URL | `extra-craft`, `extra-screens`, `save-bar`, `extra-notes`, `extra-checks` |
| [`rd-issues`](./skills/rd-issues/SKILL.md) | Files the tree, wires `blocked-by`, reads every issue back | `extra-fields`, `file-bar`, `after-file` |
| [`rd-build`](./skills/rd-build/SKILL.md) | Works the tree child by child: in progress → build → gate → browse checks → notes → in review | `before-child`, `extra-checks`, `review-bar`, `after-child`, `after-tree` |
| [`rd-verify`](./skills/rd-verify/SKILL.md) | Resolves and runs this repo's gate, then reads the summary line instead of the exit code | `gate-commands`, `extra-checks`, `green-bar` |
| [`rd-pr`](./skills/rd-pr/SKILL.md) | Branch, base sync, commit, pull request with sibling ids scrubbed, post-merge status repair | `extra-checks`, `extra-sections`, `merge-bar`, `after-pr` |

### Hygiene, any time

| Skill | What it does | Extension points |
| --- | --- | --- |
| [`rd-triage`](./skills/rd-triage/SKILL.md) | Ranks open parents Now / Next / Later / Icebox from real signal; writes only on yes | `extra-signals`, `rank-bar`, `after-rank` |
| [`rd-cleanup`](./skills/rd-cleanup/SKILL.md) | Open children under done parents, decided on evidence: close or promote. Never deletes | `evidence-bar`, `extra-sweeps`, `after-sweep` |
| [`rd-changelog`](./skills/rd-changelog/SKILL.md) | Completed issues become Feature / Improvement / Fix entries in `.radial/changelog.md` | `extra-sources`, `entry-bar`, `output` |
| [`rd-retro`](./skills/rd-retro/SKILL.md) | Scores one finished build against the workflow, with evidence; proposes wrapper sections | `extra-rules`, `score-bar`, `after-retro` |

### What lives where

| Path | What it is | Commit it? |
| --- | --- | --- |
| `.radial/config.json` | The team key for this repo | yes |
| `.radial/skills/<name>/` | Your wrappers — how your team extends a skill | yes |
| `.radial/changelog.md` | The changelog `rd-changelog` writes | yes |
| `.radial/plans/` | Plan bodies, scaffolding for `rd-issues` | no |
| `.radial/prototypes/` | Prototype HTML before it is attached | no |

Full reference, one page per skill, at
[radial.build/docs/skills](https://radial.build/docs/skills).

## Extending a skill

**Yours does not replace ours.** A wrapper adds rules to a built-in at named places, so you
keep getting our updates and we never overwrite your conventions.

A wrapper is an ordinary skill folder with an `extends` field:

```markdown
---
name: team-build
description: Our extra rules on top of rd-build, for the payments repo.
extends: rd-build
---

Read rd-build first, then apply the sections below at their hooks.

## before-child

- Refuse to start a child on a dirty working tree.

## review-bar

- A child may not move to in review until a screenshot of every browse check is
  attached to its issue.
```

Save it at `.radial/skills/team-build/SKILL.md` (this repo) or
`~/.config/radial/skills/team-build/SKILL.md` (you, everywhere), or let the CLI scaffold it
with every heading already in place:

```bash
radial skills extend rd-build --name team-build
```

The rules, each with its reason:

| Rule | Why |
| --- | --- |
| Sections are named places, not line numbers | The built-in can be rewritten without breaking your wrapper |
| A wrapper adds rules and raises bars; it cannot remove a step or lower a bar | Otherwise an extension could quietly disable the check that mattered |
| The nearest scope wins **whole** — project beats user, never merged | Two half-applied rule sets is the worst of both |
| Two wrappers in one scope extending one skill: neither applies | Silent precedence is worse than a loud refusal |
| `rd-*` names are reserved | So an update never fights your wrapper for a name |

`radial skills install --project` also copies this repo's wrappers into `.claude/skills` and
`.agents/skills`, so `/team-build` is invocable directly.

Full guide: [radial.build/docs/skills/extending](https://radial.build/docs/skills/extending).

### Contributing a skill

The pack is MIT and lives in [`skills/`](./skills). Copy
[`skills/_template/SKILL.md`](./skills/_template/SKILL.md), keep the section order, then:

```bash
npm run manifest   # regenerate skills/manifest.json
npm test           # the guards — zero dependencies, node --test
```

The guards enforce the things that rot: the manifest matches the folders, every hook marker is
alone on its line, bar names are unique across the pack, no executable ships inside a skill
folder, and this README lists every skill and every hook.

## Commands

| Command | What it does |
| --- | --- |
| `radial auth` | Device-flow sign-in; stores a session under `~/.config/radial/` |
| `radial create <title>` | Create an issue. `-p` priority, `-l` label (repeatable), `-a` assignee, `-t` team |
| `radial update <ID>` | Edit an issue. `--add-label` / `--remove-label` change one label; `-l` replaces the set |
| `radial list` | List issues. `--assignee`, `--status`, `--label`, `--team`, `--priority`, `--json` |
| `radial show RAD-219` | Full detail + comments |
| `radial close RAD-219` | Close, with optional `-m "message"` |
| `radial skills <sub>` | `install` · `update` · `list` · `remove` · `extend` — the `rd-*` agent skills |
| `radial triage` | Step through the triage queue |
| `radial search <query>` | The same fast index the app uses |
| `radial branch RAD-219` | The suggested git branch name for an issue |
| `radial attach <ID> <file>` | Attach a prototype (or file) and print its Preview URL |
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
`RADIAL_API_URL`, `RADIAL_AUTH_URL`, `RADIAL_MCP_URL` — handy for self-hosting. The skills
installer reads `RADIAL_SKILLS_URL` the same way.

## License

MIT — see [LICENSE](./LICENSE).
