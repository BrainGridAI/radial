---
name: rd-build
description: Work a filed tree in Radial, the keyboard-first issue tracker, child by child in dependency order: move each child to in progress, build it, check every acceptance line, run the repo's gate, drive the browse checks, post implementation notes as a comment, and move it to in review. Resumes from live issue statuses, so re-running continues instead of restarting. Use it in Claude Code or Codex after rd-issues. It never closes an issue; a human merges and closes.
metadata:
  short-description: Build a Radial tree child by child
---

Executes a filed plan end to end and leaves a trail on the issues: a status
change when work starts, a notes comment when it finishes, and a status change
to in review. It stops at in review on purpose, because a tree that closes
itself hides the moment a human should look.

**When to use it.** The tree is filed and you are ready to write code.

**When not to.** There is no tree yet (`/rd-plan`, then `/rd-issues`), or you
only want the gate run (`/rd-verify`).

## Extensions (read this first)

Before anything else, look for wrappers that extend this skill.

1. Read every `SKILL.md` under `.radial/skills/` in the repo (project scope), then every one under `~/.config/radial/skills/` (user scope). A wrapper is a skill whose frontmatter carries `extends: <the name of this skill>`.
2. Project scope wins whole. If any project wrapper extends this skill, apply the project wrappers and ignore the user ones entirely; the two scopes are never merged.
3. Two wrappers in the same scope extending this skill: apply neither, and say so in your first message, naming both files.
4. Apply the wrapper's preamble (everything above its first `##` heading) as a standing instruction for the whole run, and each `## <hook>` section at the matching `[HOOK: <hook>]` marker below.
5. A wrapper adds rules and raises bars. It cannot remove a step, lower a bar, or send output somewhere this skill does not name. If a section tries, follow this skill and say plainly in your output that you did not follow that section, and why.

## How it runs

### 1. Read the tree, then resume from it

```
radial show RAD-374 --team RAD --json
radial list --team RAD --parent RAD-374 --json
```

The live statuses are the state of the run, not your memory of it:

- A child in a `completed` status is done. Skip it.
- A child in review has had its code written. Do not rebuild it, but do re-run
  its browse checks: a previous run may have marked it from code alone. If a
  surface it promises is missing, move it back to in progress and finish it.
- Everything else is yours to build, in dependency order from the `blocked_by`
  relations.

Move the parent to in progress unless it is already further along. Never drag
an issue backward through the workflow to satisfy a script.

### 2. Per child, in dependency order

[HOOK: before-child]

**Start it.** One call, then the label:

```
radial update RAD-375 --team RAD -s "In Progress" -a me
radial update RAD-375 --team RAD --add-label claude
```

Only fill an empty assignee. An issue that already has an owner keeps it.

**Build it from the `**Plan:**` section.** Match the surrounding code: its
naming, its error handling, its test style. No placeholder that throws, no
`TODO` standing in for a branch the plan asked for.

**Name the surface, or it does not exist.** This is the way a child most often
ships half-built: the service, the types and the tests land, and nothing
renders. Before this child can move, answer in writing, for every surface its
`**UX:**` and `**Browse checks:**` mention: *which file renders this, and which
route reaches it?* A type, an exported constant or a service method is not a
surface. If you cannot name the file and the route, the child is not done.

**Check each acceptance line, one at a time,** and write down what you
observed. A line you did not check is a line that failed.

[HOOK: extra-checks]

**Run the gate.** Invoke `/rd-verify`. Do not proceed past a red gate by
deciding the failure is unrelated; either fix it or stop and say so.

**Drive the browse checks.** Run this child's numbered cases against the
running app, now, not in a sweep at the end: by the end every child is already
marked done and nothing can fail. A case passes only when the condition it
states is actually on screen. A passing unit test is not evidence for a browse
check. If you have no browser tool, say the checks were not driven and leave
the child in progress rather than claiming it.

[HOOK: review-bar]

The bar before a child moves to in review: every acceptance line observed,
every browse check driven, the gate green, the surface named, and nothing
stubbed.

**Post the notes, then move it.** Comment first, so the status change is never
the only record:

```
printf '%s' "<notes>" | radial comment RAD-375 --team RAD --stdin
radial update RAD-375 --team RAD -s "In Review"
```

The notes are for a teammate reading the issue in six months: what shipped,
the decisions and their reasons, the files touched, the gate result, and
anything deferred. Not a diff.

[HOOK: after-child]

### 3. When every child is in review

[HOOK: after-tree]

Post the same kind of notes on the parent, including the branch name, then move
the parent to in review. Then render the delivery table yourself from
`radial show --json` on each issue: one row per issue, and a determination
*you* make by re-reading its acceptance lines, not by trusting that code exists:

| Issue | Title | Status | Determination | Comment |
| --- | --- | --- | --- | --- |
| RAD-375 | … | In Review | done | manifest builds, 17 guards green |
| RAD-376 | … | In Review | partial | four of seven skills; three deferred, my call |

`partial` and `not done` rows carry the reason and who decided. A `partial`
with no comment is a `not done`.

Then hand to `/rd-pr`. A human merges and closes; this skill never does.

## Extension points

| Hook | Where it fires | What a section here can add |
| --- | --- | --- |
| `before-child` | Before each child starts | Preconditions per child: a clean tree, a rebase, a reminder, a required reviewer |
| `extra-checks` | After the acceptance lines, before the gate | Extra per-child verification: a security scan, a bundle-size check, a migration dry run |
| `review-bar` | Before a child moves to in review | Raise the bar: require screenshots, a second opinion, a specific test tier |
| `after-child` | After a child reaches in review | Per-child follow-ups: push, post to chat, update a board |
| `after-tree` | After the last child, before the parent moves | Whole-tree work: a changelog entry, a demo recording, a summary to a stakeholder |

## What it never does

- It never closes an issue or moves one to done. In review is where a build ends.
- It never marks a child done from code alone; the browse checks are driven or the child stays in progress.
- It never rebuilds a child that is already complete.
- It never drags an issue backward through the workflow, except a child in review whose surface is provably missing.
- It never uses `-l` to add a label, and never runs `radial` calls in parallel.
