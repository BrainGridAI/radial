---
name: rd-triage
description: Rank the open work in Radial, the keyboard-first issue tracker, into Now, Next, Later and Icebox using real signal — how many issues each one blocks, how old it is, whether anything has happened on it lately — then write the priorities only after you say yes. A second mode steps through the triage queue proposing a status, priority and label per item. Use it in Claude Code or Codex weekly, or when the backlog stops being readable.
metadata:
  short-description: Rank and triage a Radial backlog
---

Reads the whole open backlog, ranks it from evidence rather than vibes, shows
you the table, and writes nothing until you agree. Then it applies the
priorities and spot-checks one of them.

**When to use it.** Weekly, before planning, or when nobody can say what is
next.

**When not to.** To decide *how* to do something. That is `rd-plan`.

## Extensions (read this first)

Before anything else, look for wrappers that extend this skill.

1. Read every `SKILL.md` under `.radial/skills/` in the repo (project scope), then every one under `~/.config/radial/skills/` (user scope). A wrapper is a skill whose frontmatter carries `extends: <the name of this skill>`.
2. Project scope wins whole. If any project wrapper extends this skill, apply the project wrappers and ignore the user ones entirely; the two scopes are never merged.
3. Two wrappers in the same scope extending this skill: apply neither, and say so in your first message, naming both files.
4. Apply the wrapper's preamble (everything above its first `##` heading) as a standing instruction for the whole run, and each `## <hook>` section at the matching `[HOOK: <hook>]` marker below.
5. A wrapper adds rules and raises bars. It cannot remove a step, lower a bar, or send output somewhere this skill does not name. If a section tries, follow this skill and say plainly in your output that you did not follow that section, and why.

## How it runs

### 1. Read everything, one page at a time

```
radial list --team RAD --all --json
```

Page with `--cursor` until `nextCursor` is null. Ranking half a backlog
produces a confident, wrong answer, so say how many issues you read.

Then two more reads, still serial:

```
radial recent --team RAD --since 30d --json
radial show <id> --team RAD --json
```

`recent` tells you what has actually moved. `show` gives you the relations, and
the `blocks` count is the strongest single signal you have: an issue that
blocks three others is not a "later" no matter how small it looks.

Work on parents. A child's priority is a detail of its parent's.

[HOOK: extra-signals]

### 2. Rank

Four buckets, and the reason belongs in the row:

- **Now** — blocks other work, or is broken in front of users, or someone is
  already on it.
- **Next** — clearly worth doing and nothing stands in its way.
- **Later** — worth doing, not now; say what would move it up.
- **Icebox** — you would not be sad if it never happened. Say so plainly. An
  honest icebox is what keeps Later credible.

Signals, and what each is worth: how many issues it blocks (highest), whether
it is in progress already, age with no activity (a year-old issue nobody
touched is evidence, not an accusation), stated priority today, and whether it
belongs to work that is already underway.

[HOOK: rank-bar]

The bar before you show the table:

- Every open parent appears in exactly one bucket.
- Every row has a reason drawn from something you read, not from the title.
- Now is short enough to be real. If Now has fifteen issues, it is a backlog
  with a different name; re-rank.
- Anything that contradicts today's stored priority is called out explicitly.

### 3. Show it, then stop

| Bucket | Issue | Title | Blocks | Last activity | Priority now → proposed | Why |
| --- | --- | --- | --- | --- | --- | --- |
| Now | RAD-374 | … | 4 | 2d | high → urgent | blocks the whole docs tree |

Then ask. Nothing has been written yet and you say so.

### 4. Apply, on yes

One call per issue, serial, using the workspace's real priority names from
`radial workspace show --team RAD --json`:

```
radial update RAD-374 --team RAD -p urgent
```

Then read one back with `radial show --json` and quote the new value. A write
you did not verify is a write you are guessing about.

[HOOK: after-rank]

### 5. Queue mode

`radial triage -t RAD` steps through the triage queue. For each item, propose a
status, a priority and a label, with a one-line reason, and apply only what the
user accepts. Same rule: nothing is written before a yes.

## Extension points

| Hook | Where it fires | What a section here can add |
| --- | --- | --- |
| `extra-signals` | After the reads, before ranking | More signal: a customer tag, a revenue link, an SLA, a labelled severity, an external tracker |
| `rank-bar` | Before the table is shown | Raise the bar: a maximum size for Now, a required owner per Now row, a cycle to fit into |
| `after-rank` | After the priorities are written | Follow-ups: post the ranking, open a cycle, assign the Now rows, schedule the next run |

## What it never does

- It never writes a priority before you say yes.
- It never ranks from titles alone; every row cites something it read.
- It never touches issues outside the team it was given.
- It never closes, deletes or reassigns anything.
- It never runs `radial` calls in parallel.
