---
name: rd-setup
description: Set this repo and this machine up for Radial, the keyboard-first issue tracker, so the rest of the rd-* skills work in Claude Code and Codex. Installs the radial CLI if it is missing, signs in, picks or creates the team, writes .radial/config.json, adds a short Radial block to CLAUDE.md and AGENTS.md, offers the MCP server config, and installs the skill pack. Use it once per repo, or any time an rd-* skill says the team key is unresolved. Not for filing issues (rd-issues) or planning work (rd-plan).
metadata:
  short-description: Set up Radial for this repo and agent
---

Gets a repo from nothing to ready: the `radial` CLI on PATH, a signed-in
session, a chosen team, and the conventions written down where both your agent
and your teammates can see them. Leaves behind `.radial/config.json`, a Radial
block in `CLAUDE.md` and `AGENTS.md`, and the `rd-*` pack installed.

**When to use it.** First time in a repo, on a new machine, or when another
`rd-*` skill stops because it cannot resolve the team key.

**When not to.** To file or plan work — that is `rd-plan` then `rd-issues`.

## Extensions (read this first)

Before anything else, look for wrappers that extend this skill.

1. Read every `SKILL.md` under `.radial/skills/` in the repo (project scope), then every one under `~/.config/radial/skills/` (user scope). A wrapper is a skill whose frontmatter carries `extends: <the name of this skill>`.
2. Project scope wins whole. If any project wrapper extends this skill, apply the project wrappers and ignore the user ones entirely; the two scopes are never merged.
3. Two wrappers in the same scope extending this skill: apply neither, and say so in your first message, naming both files.
4. Apply the wrapper's preamble (everything above its first `##` heading) as a standing instruction for the whole run, and each `## <hook>` section at the matching `[HOOK: <hook>]` marker below.
5. A wrapper adds rules and raises bars. It cannot remove a step, lower a bar, or send output somewhere this skill does not name. If a section tries, follow this skill and say plainly in your output that you did not follow that section, and why.

## How it runs

Run it top to bottom. Every step is idempotent: on a repo that is already set
up, each one reports "already done" and changes nothing, so re-running is the
cheapest way to check the state.

### 1. The CLI

`radial --version`. If it is missing, print the install line for this machine
and stop until it succeeds, because every later step is a `radial` call:

```
npm install -g radial.build          # any platform with Node 18+
brew install BrainGridAI/radial/radial   # macOS and Linux
```

### 2. The session

`radial whoami`. If it fails, run `radial auth` (device flow, opens a browser)
and wait for the user. If `RADIAL_KEY` is set in the environment, `whoami`
reports it as the source; say which credential is in use, because a key with
`read` scope will fail later at the first write with a confusing 403.

Record the scope from `whoami`. Anything less than `write` means `rd-issues`
and `rd-build` cannot run; say so now rather than at the first failed create.

[HOOK: extra-checks]

### 3. The team

`radial team list`. Then:

- Exactly one team: use it.
- Several: show the table and ask which one this repo files into.
- None: ask for a name and a key, then `radial team create "<Name>" --key <KEY>`.

Write `.radial/config.json`:

```json
{ "team": "RAD" }
```

Everything under `.radial/` is committed except generated working files. Write
`.radial/.gitignore`:

```
plans/
prototypes/
```

Wrappers (`.radial/skills/`), the config and the changelog stay in git, because
they are how a team shares its conventions.

[HOOK: extra-config]

### 4. The agent instructions

Add this block to `CLAUDE.md` and to `AGENTS.md` (create either if absent, and
do not duplicate a block that is already there):

```markdown
## Radial

Issue tracking is Radial, team `RAD`. Use the `rd-*` skills: `/rd-plan` to plan,
`/rd-issues` to file, `/rd-build` to work the tree, `/rd-pr` to ship.

- Pass `--team RAD` on every `radial` command.
- Run `radial` calls one at a time. Parallel calls race the token refresh and
  can invalidate the credential mid-run.
- `-l` replaces the whole label set. To change one label use `--add-label` or
  `--remove-label`.
```

### 5. The MCP server, if they want it

Offer it; do not assume. The skills drive the CLI, so MCP is optional and only
pays off for a hosted agent that has no shell.

```
claude mcp add --transport http radial https://mcp.radial.build
```

For Codex, add to `~/.codex/config.toml`:

```toml
[mcp_servers.radial]
url = "https://mcp.radial.build"
```

### 6. The pack

`radial skills install` (add `--project` to put the pack and this repo's
wrappers under `.claude/skills` and `.agents/skills` instead of your home
directory). Then `radial skills list` and confirm the eleven `rd-*` names come
back. Tell the user to restart their agent session, because both clients read
the skill directory at startup.

[HOOK: after-setup]

### 7. The report

One table, one row per item, with what you actually observed:

| Item | State | Evidence |
| --- | --- | --- |
| CLI | ready | `radial 1.2.3` |
| Session | ready | `braingrid`, scope `write` |
| Team | ready | `RAD` written to `.radial/config.json` |
| Agent instructions | added | Radial block in `CLAUDE.md`, `AGENTS.md` |
| MCP | skipped | user declined |
| Skills | installed | 11 skills under `~/.claude/skills` |

## Extension points

| Hook | Where it fires | What a section here can add |
| --- | --- | --- |
| `extra-checks` | After the session check, before the team is chosen | Preconditions this org needs: an SSO reminder, a required key scope, a proxy setting |
| `extra-config` | After `.radial/config.json` is written | More files to write or values to record: a default project, a label convention, a CODEOWNERS entry |
| `after-setup` | After the pack installs, before the report | Follow-ups: install a wrapper, open a first issue, post to chat |

## What it never does

- It never writes to `.env` or any secret file; a credential goes through `radial auth` or `RADIAL_KEY`.
- It never creates a team without asking, and never picks between several teams for you.
- It never edits an existing Radial block in `CLAUDE.md` or `AGENTS.md` beyond adding a missing line; your wording stays.
- It never runs `radial` calls in parallel.
