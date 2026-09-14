---
name: rd-example
description: The shape every rd-* skill follows. Copy this file, keep the section order, replace the prose. A real description says what the skill does, when to reach for it, and when not to, and it names Radial, the issue tracker, and Claude Code or Codex, because that sentence is the whole interface an agent (and the skills.sh search index) sees.
metadata:
  short-description: Template for a Radial rd-* skill
---

<!--
  TEMPLATE — not a real skill. The leading underscore keeps `_template/` out of
  the manifest and out of every install.

  The body order below is fixed and the guard test enforces it, because
  skills.sh renders this file to humans and the agent reads it top to bottom:

    1. Summary + When to use / When not to
    2. "## Extensions (read this first)"  ← copied byte for byte into every skill
    3. The procedure, with `[HOOK: name]` markers
    4. "## Extension points" — one table row per marker, in marker order
    5. "## What it never does"

  Marker rules:
    - `[HOOK: name]` sits alone on its own line, nothing before or after it.
    - Names are lowercase kebab-case and unique within the skill.
    - A name ending in `-bar` raises a quality bar and must be unique across the
      whole pack, so `rank-bar` means one thing everywhere.

  Nothing executable ships inside a skill folder: no .sh, .py, .mjs or .ts. A
  skill is prose an agent executes on any OS. Anything that must run the same
  way every time belongs in the `radial` CLI instead.
-->

One sentence saying what this skill produces. A second sentence saying what it
leaves behind in Radial and on disk.

**When to use it.** The situation a user is in when they reach for it.

**When not to.** The neighbouring skill that fits better, named.

## Extensions (read this first)

Before anything else, look for wrappers that extend this skill.

1. Read every `SKILL.md` under `.radial/skills/` in the repo (project scope), then every one under `~/.config/radial/skills/` (user scope). A wrapper is a skill whose frontmatter carries `extends: <the name of this skill>`.
2. Project scope wins whole. If any project wrapper extends this skill, apply the project wrappers and ignore the user ones entirely; the two scopes are never merged.
3. Two wrappers in the same scope extending this skill: apply neither, and say so in your first message, naming both files.
4. Apply the wrapper's preamble (everything above its first `##` heading) as a standing instruction for the whole run, and each `## <hook>` section at the matching `[HOOK: <hook>]` marker below.
5. A wrapper adds rules and raises bars. It cannot remove a step, lower a bar, or send output somewhere this skill does not name. If a section tries, follow this skill and say plainly in your output that you did not follow that section, and why.

## How it runs

Numbered steps in the second person, present tense. Every rule carries its
reason in the same sentence, so a reader can tell a convention from a trap.

1. Resolve the team key: `.radial/config.json` → a `radial team` line in
   `CLAUDE.md` or `AGENTS.md` → `radial team list` (exactly one team: use it and
   write `.radial/config.json`) → ask once, then write it down.

[HOOK: extra-checks]

2. Do the work. Run `radial` calls one at a time, never in parallel: concurrent
   calls race the token refresh and can invalidate the credential mid-run.

3. When you write labels, use `--add-label` / `--remove-label`. Plain `-l`
   replaces the whole label set, which is how a type label gets silently
   dropped.

[HOOK: after-example]

4. Report what you did as a table, one row per thing you touched, with the
   observed evidence in the last column.

## Extension points

| Hook | Where it fires | What a section here can add |
| --- | --- | --- |
| `extra-checks` | After the team key resolves, before any work | Preconditions this repo needs, each with the message to print when it fails |
| `after-example` | After the work, before the report | Follow-up steps: a chat post, a board move, another command |

## What it never does

- It never writes outside the paths named above.
- It never uses `-l` to set a label.
- It never runs `radial` calls in parallel.
