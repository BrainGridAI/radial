---
name: rd-plan
description: Turn an idea into a plan for Radial, the keyboard-first issue tracker — one parent issue plus two to four children, each with a goal, a file list and acceptance criteria anyone can check. Writes the plan to .radial/plans/<slug>.md and creates nothing, so you can argue with it before it becomes a tree. Use it in Claude Code or Codex before starting work of more than an hour. Not for filing the tree (rd-issues) or for building it (rd-build).
metadata:
  short-description: Plan a change as a Radial parent and children
---

Turns "we should probably do X" into a reviewable plan: one parent, a small
number of children that each merge on their own, and acceptance criteria
written as things you can observe. It writes one markdown file and touches
Radial only to read.

**When to use it.** Before any change big enough that you would otherwise open
five tabs and start guessing.

**When not to.** For a one-line fix. File it with `radial create` and move on.

## Extensions (read this first)

Before anything else, look for wrappers that extend this skill.

1. Read every `SKILL.md` under `.radial/skills/` in the repo (project scope), then every one under `~/.config/radial/skills/` (user scope). A wrapper is a skill whose frontmatter carries `extends: <the name of this skill>`.
2. Project scope wins whole. If any project wrapper extends this skill, apply the project wrappers and ignore the user ones entirely; the two scopes are never merged.
3. Two wrappers in the same scope extending this skill: apply neither, and say so in your first message, naming both files.
4. Apply the wrapper's preamble (everything above its first `##` heading) as a standing instruction for the whole run, and each `## <hook>` section at the matching `[HOOK: <hook>]` marker below.
5. A wrapper adds rules and raises bars. It cannot remove a step, lower a bar, or send output somewhere this skill does not name. If a section tries, follow this skill and say plainly in your output that you did not follow that section, and why.

## How it runs

### 1. Ground yourself in the workspace

Resolve the team key: `.radial/config.json` → a `radial team` line in
`CLAUDE.md` or `AGENTS.md` → `radial team list` (exactly one team: use it and
write `.radial/config.json`) → ask once, then write it down. If nothing
resolves, stop and point at `/rd-setup`.

Then read the real vocabulary, one call, so the plan never invents a status:

```
radial workspace show --team RAD --json
```

Take the team's status names, label names and priority names from that output.
Statuses are per-team rows, so `In Progress` in one workspace is `Doing` in
another; always model on the status *category* (`backlog`, `unstarted`,
`started`, `completed`, `canceled`) and pick the matching name.

### 2. Understand what is being asked

Read the code the idea touches before decomposing it. Name the files you
actually opened in the plan; a plan that names no real file is a guess.

Ask the user only what you cannot determine from the repo, and ask it all at
once. Two questions in one message beat two round trips.

[HOOK: extra-questions]

### 3. Check it is not already filed

For each candidate title, one call:

```
radial search "<a few distinctive words>" --team RAD --json
```

A close hit means you extend that issue instead of opening a second tree. Say
which issues you checked and what you concluded, so the reader can disagree.

### 4. Decompose

One parent, then **two to four children**. The rules that keep the shape
honest:

- **One child is one merge.** If a child cannot merge on its own without
  breaking the default branch, it is not a child; fold it into its neighbour.
- **One plan is one pull request.** The whole tree ships together.
- **Order by dependency**, and record it: a child that needs another is
  `blocked-by` it.
- **Acceptance criteria pin the observable requirement, not your
  implementation.** "The list renders 20 rows and a Load more button" survives a
  rewrite; "the component calls `usePagination`" is a bodyguard for one
  implementation.
- A child with no acceptance criteria is not a child; it is a wish.

[HOOK: extra-sections]

### 5. Write the bodies

Write one file, `.radial/plans/<slug>.md`, holding the parent body and every
child body in full, to the schema in `references/issue-body.md`. Do not put the
bodies in chat; they are long, and `rd-issues` reads them from this file.

The header lines on the parent, exactly:

```
**Type:** feature | fix | chore | refactor
**Agent:** Claude Code | Codex
**Session ID:** <this session's id, or `unknown`>
```

Then `**Goal:**`, `**Scope:**` (an In list and an Out list), `**Plan:**`,
`**Files:**`, `**UX:**` when a person will see it, `**Acceptance:**` and
`**Browse checks:**` when there is a screen to look at, `**Tags:**`.

[HOOK: extra-checks]

### 6. Check your own plan before showing it

[HOOK: plan-bar]

The bar, every item of which you check and report:

- Every child has at least two acceptance criteria, each observable.
- Every child names at least one real file or directory that exists today, or
  says explicitly that it creates one.
- The Out list is not empty. A plan that excludes nothing has not been thought
  about.
- Every child merges alone.
- The dependency edges are acyclic and each one is justified in a clause.
- Nothing in the plan contradicts `CLAUDE.md` or `AGENTS.md`.

[HOOK: after-plan]

### 7. Report

In chat, short: a breakdown table (ID, title, what it touches, needs), the Out
list, and any open decision written as `A (default) / B` with your
recommendation. Point at the plan file. Then stop — creating the tree is
`/rd-issues`, and a plan nobody argued with is not worth filing.

## Extension points

| Hook | Where it fires | What a section here can add |
| --- | --- | --- |
| `extra-questions` | Before decomposition, while gathering context | Questions this team always wants answered: rollout, data migration, who owns the on-call |
| `extra-sections` | While decomposing, before the bodies are written | More required body sections: a security note, a metrics plan, a rollback paragraph |
| `extra-checks` | After the bodies are written | Repo-specific checks on the plan: naming rules, a forbidden directory, a required label |
| `plan-bar` | At the self-review, before the report | Raise the bar: more acceptance criteria, a required second opinion, a maximum child count |
| `after-plan` | After the bar passes, before the chat report | What to do with a finished plan: post it, open a design doc, tag a reviewer |

## What it never does

- It never creates, updates or closes an issue. Reading is the only Radial write it does, and it does none.
- It never writes acceptance criteria that assert an implementation detail.
- It never puts the full bodies in chat; they live in `.radial/plans/<slug>.md`.
- It never invents a status, label or priority name; it reads them from the workspace.
- It never runs `radial` calls in parallel.
