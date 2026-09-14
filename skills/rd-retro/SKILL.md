---
name: rd-retro
description: Audit one finished build against the rd-* workflow using only what Radial, the keyboard-first issue tracker, and git already hold: the tree, its activity, its comments, the pull request and the commits. Scores each rule with the evidence behind it, lists where time was wasted, and phrases every improvement as a wrapper section you can paste into .radial/skills/. Writes nothing. Use it in Claude Code or Codex after a tree ships, or on any tree that went badly.
metadata:
  short-description: Audit a finished Radial build against the workflow
---

Reconstructs what happened on one tree from the record it left, scores the
workflow rules with quoted evidence, and turns each finding into a wrapper
section you can install. It changes nothing, so it is safe to run on anyone's
tree.

**When to use it.** After a tree merges, or when a build felt worse than it
should have and you want to know where it actually went.

**When not to.** Mid-build. The record is not there yet.

## Extensions (read this first)

Before anything else, look for wrappers that extend this skill.

1. Read every `SKILL.md` under `.radial/skills/` in the repo (project scope), then every one under `~/.config/radial/skills/` (user scope). A wrapper is a skill whose frontmatter carries `extends: <the name of this skill>`.
2. Project scope wins whole. If any project wrapper extends this skill, apply the project wrappers and ignore the user ones entirely; the two scopes are never merged.
3. Two wrappers in the same scope extending this skill: apply neither, and say so in your first message, naming both files.
4. Apply the wrapper's preamble (everything above its first `##` heading) as a standing instruction for the whole run, and each `## <hook>` section at the matching `[HOOK: <hook>]` marker below.
5. A wrapper adds rules and raises bars. It cannot remove a step, lower a bar, or send output somewhere this skill does not name. If a section tries, follow this skill and say plainly in your output that you did not follow that section, and why.

## How it runs

### 1. Gather the record

```
radial show RAD-374 --team RAD --json
radial list --team RAD --parent RAD-374 --json
radial activity RAD-375 --team RAD
```

Then, per child, its comments (in the `show --json` output) and its activity.
From git: `git log --grep "RAD-374" --oneline --all` and, where `gh` exists,
`gh pr list --search "RAD-374" --json number,title,body,createdAt,mergedAt`.

Everything after this point cites one of those. A retro finding with no
timestamp is an opinion.

### 2. Score the rules

Each rule gets pass, partial or fail, and the evidence beside it:

| Rule | What proves it | Result |
| --- | --- | --- |
| The tree was filed before the first build commit | earliest `createdAt` vs first commit date | |
| Each child went in progress, then in review | the activity trail per child | |
| Each child has an implementation-notes comment | comment count and its first line | |
| The notes name the acceptance lines | the comment text against the body | |
| The prototype was attached where the plan had a UX line | attachments on the parent | |
| Sibling ids were scrubbed in the pull request body | a bare `KEY-n` that is not the branch's own | |
| The tree ended in review, not closed by the merge | statuses after `mergedAt` | |
| Writes ran serially | bursts of identical timestamps across issues | |
| No child was skipped | every child has a determination | |

[HOOK: extra-rules]

[HOOK: score-bar]

The bar for the scorecard:

- Every row has a result and a piece of evidence with a timestamp or an id.
- A rule you could not check is stated as "not checkable here", with the reason
  and what would make it checkable. It is never silently a pass.
- The overall verdict is one sentence and is consistent with the rows. A
  scorecard with three fails does not conclude "went well".

### 3. Where the time went

List the gaps: the long pause between two events, the child that went to in
review and came back, the gate that ran three times, the comment thread that
looks like a decision being re-litigated. Each with the two timestamps and the
minutes between them. Do not guess at causes you cannot see in the record: say
"a 90-minute gap with no events" and let the reader fill it in.

### 4. Up to three proposals, each installable

This is the part that matters, so keep it to three. Each proposal is a section
you can paste into a wrapper, which is how a lesson survives the session:

```markdown
---
name: team-build
description: Our extra rules on top of rd-build.
extends: rd-build
---

Read rd-build first, then apply the sections below at their hooks.

## review-bar

- A child may not move to in review until a screenshot of each browse check is
  attached to the issue. Three children went to in review with no visual
  evidence in RAD-374 and two came back.
```

Say which file it goes in (`.radial/skills/team-build/SKILL.md`) and that
`radial skills extend rd-build --name team-build` scaffolds it with the hook
headings already in place.

[HOOK: after-retro]

### 5. Report

The scorecard, the time table, the three proposals. State once, at the end,
that nothing was written.

## Extension points

| Hook | Where it fires | What a section here can add |
| --- | --- | --- |
| `extra-rules` | After the built-in rules are scored | House rules to score too: a required reviewer, a branch convention, a cycle boundary, a deploy note |
| `score-bar` | Before the scorecard is shown | Raise the bar: a minimum evidence standard, a required verdict sentence, a pass threshold |
| `after-retro` | After the proposals | Where the retro goes: a comment on the parent, a team doc, a recurring agenda item |

## What it never does

- It never writes to Radial, to git, or to any file. It reports.
- It never scores a rule it could not check as a pass.
- It never states a cause it cannot evidence from the record.
- It never produces more than three proposals; a list of twelve changes nothing.
- It never runs `radial` calls in parallel.
