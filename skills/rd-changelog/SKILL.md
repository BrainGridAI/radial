---
name: rd-changelog
description: Write the changelog from what actually shipped in Radial, the keyboard-first issue tracker — the issues completed since a date or a tag, read as Feature, Improvement and Fix entries in customer language rather than issue titles. Prepends a dated section to .radial/changelog.md by default, and an output hook sends it anywhere else. Asks instead of guessing when an issue reads as internal. Use it in Claude Code or Codex at a release, or at the end of a week.
metadata:
  short-description: Write a changelog from completed Radial issues
---

Collects the work that reached a completed status in a window, reads each
issue's body rather than its title, and writes entries a customer would
understand. It asks about anything that looks internal instead of inventing a
user benefit for a refactor.

**When to use it.** Cutting a release, or writing the weekly update.

**When not to.** To find out what is left. That is `rd-triage`.

## Extensions (read this first)

Before anything else, look for wrappers that extend this skill.

1. Read every `SKILL.md` under `.radial/skills/` in the repo (project scope), then every one under `~/.config/radial/skills/` (user scope). A wrapper is a skill whose frontmatter carries `extends: <the name of this skill>`.
2. Project scope wins whole. If any project wrapper extends this skill, apply the project wrappers and ignore the user ones entirely; the two scopes are never merged.
3. Two wrappers in the same scope extending this skill: apply neither, and say so in your first message, naming both files.
4. Apply the wrapper's preamble (everything above its first `##` heading) as a standing instruction for the whole run, and each `## <hook>` section at the matching `[HOOK: <hook>]` marker below.
5. A wrapper adds rules and raises bars. It cannot remove a step, lower a bar, or send output somewhere this skill does not name. If a section tries, follow this skill and say plainly in your output that you did not follow that section, and why.

## How it runs

### 1. The window

`--since <date>` or `--since <tag>`. With a tag, resolve it to a date with
`git log -1 --format=%aI <tag>`. With neither, use the date of the last section
already in the changelog file, and say which date you chose.

### 2. What shipped

```
radial list --team RAD --status done --json
```

Page with `--cursor`, then filter on `completedAt` falling inside the window —
not on `updatedAt`, which a label change bumps. Prefer parents: a tree's six
children are one entry, not six.

Where `gh` exists, cross-check against merged pull requests, because a tree
that shipped but was never closed would otherwise be missing:

```
gh pr list --state merged --search "merged:>=<date>" --json title,body,mergedAt
```

Any `KEY-n` in a merged title or body that is not already in your list is a
candidate; read it and decide.

[HOOK: extra-sources]

### 3. Read each issue, not its title

```
radial show RAD-374 --team RAD --json
```

The `**Type:**` header line gives you the section: `feature` → Features,
`fix` → Fixes, everything else → Improvements. The `**Goal:**` line gives you
the sentence, once you have rewritten it for someone who does not work here.

If the body carries a `**Changelog**` block, that is the author's own wording.
Prefer it.

[HOOK: entry-bar]

The bar for every entry:

- It says what a person can now do, in their words, not yours. "Search finds
  bare issue numbers" beats "resolve numeric tokens in the search index".
- No issue key, no internal component name, no branch name in the text.
- One sentence, two at most. A third sentence is a blog post.
- Nothing invented. If the issue does not say what changed for a user, ask.

An issue with no user-visible effect (a refactor, a test, a dependency bump)
does not get an entry. Do not manufacture a benefit for it; list it under
"Internal" only if the user asks for that section.

### 4. Write it

Default output: prepend a dated section to `.radial/changelog.md`, creating the
file if it is absent and **preserving everything already in it**. Read the file,
build the new content, write it back whole; never append to the end of a file
whose newest entry is at the top.

```markdown
## 2026-09-14

### Features
- Radial skills for Claude Code and Codex. `radial skills install` gives your
  agent the eleven `rd-*` workflows.

### Improvements
- Bare issue numbers now resolve in search.

### Fixes
- The comments panel opens only for files that have comments.
```

[HOOK: output]

### 5. Report

The entries you wrote, the issues you skipped and why, and the issues you could
not classify. Say where the file is. Do not close anything: shipping and
closing are separate decisions.

## Extension points

| Hook | Where it fires | What a section here can add |
| --- | --- | --- |
| `extra-sources` | After the issue list is built | More sources: commit subjects, a release tracker, a support inbox, an external tracker's export |
| `entry-bar` | Before entries are written | Raise the bar: a house voice, a length limit, a required link per entry, a banned-word list |
| `output` | Before the file is written | Redirect the output: a docs page, `CHANGELOG.md`, a release body, standard output only |

## What it never does

- It never invents a user-visible benefit for work that has none.
- It never overwrites or truncates an existing changelog; prior sections survive byte for byte.
- It never closes or edits an issue.
- It never puts an issue key or a branch name in customer-facing text.
- It never runs `radial` calls in parallel.
