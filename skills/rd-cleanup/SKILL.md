---
name: rd-cleanup
description: Find the stranded work in Radial, the keyboard-first issue tracker (open children under a parent that is already done, and issues sitting in progress with no activity for weeks) and decide each one on evidence: a merged pull request or a commit naming it means close it, no evidence means promote it to standalone. Shows a read-only table first and applies nothing until you say yes. Use it in Claude Code or Codex monthly, or after a big tree merges.
metadata:
  short-description: Close or promote stranded Radial issues
---

Sweeps for issues the workflow left behind and proposes one action per issue,
each backed by something it found in Radial or in git. It never deletes, and it
shows you everything before it writes.

**When to use it.** After a large tree merges, monthly, or when the board has
issues nobody can explain.

**When not to.** To reprioritise. That is `rd-triage`.

## Extensions (read this first)

Before anything else, look for wrappers that extend this skill.

1. Read every `SKILL.md` under `.radial/skills/` in the repo (project scope), then every one under `~/.config/radial/skills/` (user scope). A wrapper is a skill whose frontmatter carries `extends: <the name of this skill>`.
2. Project scope wins whole. If any project wrapper extends this skill, apply the project wrappers and ignore the user ones entirely; the two scopes are never merged.
3. Two wrappers in the same scope extending this skill: apply neither, and say so in your first message, naming both files.
4. Apply the wrapper's preamble (everything above its first `##` heading) as a standing instruction for the whole run, and each `## <hook>` section at the matching `[HOOK: <hook>]` marker below.
5. A wrapper adds rules and raises bars. It cannot remove a step, lower a bar, or send output somewhere this skill does not name. If a section tries, follow this skill and say plainly in your output that you did not follow that section, and why.

## How it runs

### Sweep 1: open children under a completed parent

```
radial list --team RAD --all --json
```

Page through with `--cursor`. Find every issue whose `parent` is an issue in a
`completed` status while the child itself is not. For each one, look for
evidence that the work actually happened:

- `radial show <child> --team RAD --json` for the comments and relations. An
  implementation-notes comment is strong evidence.
- `radial activity <child> --team RAD`: did it ever reach in review?
- `git log --all --grep "<KEY-n>" --oneline` for a commit naming the id.
- `gh pr list --search "<KEY-n>" --state merged` when `gh` exists.

[HOOK: evidence-bar]

The bar for each verdict:

- **close**: there is a merged pull request or a commit that names this id, or
  a notes comment describing what shipped. Quote it.
- **promote**: no such evidence. The work was never done, and it is now
  hidden under a parent nobody will reopen. Detach it so it can be seen.
- **ask**: evidence points both ways. Say what you found and let the user
  decide. There is no shame in this row; a wrong close is worse.

Never infer "done" from the parent being done. That inference is exactly the
bug this sweep exists to undo.

### Sweep 2: in progress, but nothing is happening

Issues in a `started` status whose last activity is older than N days (default
21; take N from the user if they give one). Read `radial activity <id>` for the
real last event rather than `updatedAt`, which a bulk label change also bumps.

Propose moving each back to the team's todo status with a comment saying why,
so the board stops claiming work is underway.

[HOOK: extra-sweeps]

### The table, before anything is written

| Issue | Title | Situation | Evidence | Proposal |
| --- | --- | --- | --- | --- |
| RAD-310 | … | open under done parent RAD-300 | merged PR #88 names it | close |
| RAD-311 | … | open under done parent RAD-300 | nothing in git or comments | promote to standalone |
| RAD-290 | … | in progress, 44 days quiet | last activity 2026-08-01 | back to Todo |

Then stop and ask. State plainly that nothing has been written.

### Applying, on yes

Serial, one call at a time, and read back the ones you changed.

Close with the evidence in the message, because the message is what the next
person reads:

```
radial close RAD-310 --team RAD -m "Shipped in PR #88 (commit a1b2c3d); closing the stranded child."
```

Promote by detaching:

```
radial update RAD-311 --team RAD --parent ""
radial show RAD-311 --team RAD --json
```

If the detach does not take, do not leave it half-done: link it instead
(`radial link RAD-311 related RAD-300`) and say that the parent link is still
in place.

[HOOK: after-sweep]

### Report

The table again with an outcome column, the count per action, and anything you
left as "ask".

## Extension points

| Hook | Where it fires | What a section here can add |
| --- | --- | --- |
| `evidence-bar` | Before each verdict is decided | Raise the bar: require a merged pull request specifically, require two sources, require a human on any close |
| `extra-sweeps` | After the two built-in sweeps | More sweeps: issues with no assignee, duplicates by title, issues in a retired label, empty projects |
| `after-sweep` | After the writes are applied | Follow-ups: post the summary, open a tidy-up issue, schedule the next sweep |

## What it never does

- It never deletes an issue. Closing is reversible; deleting is not.
- It never closes on the parent's status alone; every close quotes its evidence.
- It never writes before a yes.
- It never touches issues outside the team it was given.
- It never runs `radial` calls in parallel.
