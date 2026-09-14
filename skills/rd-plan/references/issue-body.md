# The Radial issue body

One schema, used by `rd-plan` to write bodies, by `rd-issues` to file them, by
`rd-build` to know when a child is done, and by `rd-retro` to score the run.
It is markdown, so it renders in the app, in `radial show`, and in a diff.

Two sizes. **Compact** is the four bold fields a small change needs. **Full**
adds the sections a feature needs. Use the smallest one that carries the
contract; a body padded with empty headings teaches readers to skim.

## The parent

Three header lines first, in this order, nothing above them:

```markdown
**Type:** feature
**Agent:** Claude Code
**Session ID:** 9f2c1a44-0c3e-4a5d-8b21-6f0d7e2b1c88
```

`Type` is one of `feature`, `fix`, `chore`, `refactor`, `docs`. `Agent` is the
client that wrote the plan. `Session ID` makes the planning conversation
findable a month later, which is the only reason it is there; `unknown` is an
acceptable value and a missing line is not.

Then:

```markdown
**Goal:** One sentence a stakeholder would recognise, describing the state of
the world after this ships.

**Scope:**
- In: everything this tree covers, as a list.
- Out: what a reasonable reader would expect and will not get, and why.

**Plan:** How the children fit together, the decisions already made and the
reason for each. This is where a reader learns why it is three children and not
one.

**Files:** owned by the children.

**Acceptance:**
- [boot] The repo's gate is green.
- [behavioral] A named person can do a named thing.

**Tags:** [ui, api]
```

## A child

```markdown
**Goal:** One sentence. What exists after this child merges.

**Scope:**
- In: …
- Out: …

**Plan:** The approach, the key decision, and the trap to avoid. Two to six
sentences. Name the pattern the repo already uses so the builder follows it
instead of inventing a second one.

**Files:**
create: src/lib/skills/manifest.ts, src/lib/skills/manifest.test.ts
modify: src/app/developers/page.tsx

**UX:** The journey a person takes through this child, including the empty,
loading and error states. Omit for a child with no human-visible surface, and
say `n/a (no UI surface)` rather than deleting the line, so a reader knows it
was considered.

**Acceptance:**
- [integration] With the manifest unreachable, the page renders the degraded
  hook table and no 500.
- [integration] A page whose frontmatter omits `section` fails the content
  build, naming the file.

**Browse checks:**
1. Open `/docs/skills` → the sidebar shows the eleven skills in two groups →
   click "Install and update" → the page shows a Claude Code section and a
   Codex section, each with a copy button.
2. At 390px wide → the sidebar is a disclosure above the article and nothing
   overflows horizontally.

**Tags:** [ui]
```

## The rules that matter

**An acceptance criterion is observable.** It names an input and a result
someone can see: a rendered string, a returned status code, a row in the
database, an exit code. It never names a function you intend to call. The test
is simple: could a reviewer who has not read your diff check this line? If not,
rewrite it.

**A tag in brackets says how it is checked.** `[boot]` the process starts and
the gate passes. `[integration]` two real parts meet. `[behavioral]` a person
does something and sees something. `[perf]` a number with a bound.

**Browse checks are numbered walkthroughs, not intentions.** Each one starts
where the reader starts (a URL, a state), lists the clicks, and ends on a
condition that is either on screen or not. `rd-build` runs these verbatim
before a child is allowed to move to in review, so vagueness here becomes a
false "done" later.

**Scope's Out list is load-bearing.** It is where you record what you decided
not to do, so nobody re-litigates it in review, and so `rd-retro` can tell a
deliberate omission from a dropped ball.

**Write it once, for the reader who arrives late.** The body is read by a
teammate in six months and by an agent with no memory of this conversation.
Neither has the context you have right now.

## Where the bodies live

`rd-plan` writes every body of one plan into a single file,
`.radial/plans/<slug>.md`, with the parent first and a `## C1 — <title>`
heading per child. `rd-issues` reads that file and files each body with
`radial create --description-file`, because `-d` is inline text: passing a path
to `-d` stores the literal path as the description.

`.radial/plans/` is gitignored by `rd-setup`. The plan is scaffolding; the tree
in Radial is the record.
