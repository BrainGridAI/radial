---
name: rd-prototype
description: Build one self-contained clickable HTML prototype from a plan or from a Radial issue, then attach it to the issue in Radial, the keyboard-first issue tracker, so reviewers click a Preview URL instead of reading a wireframe description. No build step, no CDN, no framework; one file you can open. Use it in Claude Code or Codex whenever a change has a screen in it and you want the design argued about before the code exists. Not for production code (rd-build).
metadata:
  short-description: Build and attach a clickable HTML prototype
---

Builds one HTML file that shows every screen and state a plan names, opens it
locally, and attaches it to the Radial parent so the Preview URL can be shared.
It is a prototype, so it is throwaway: real copy, fake data, no dependencies.

**When to use it.** A change with a visible surface, before anyone writes the
real component. Also on an existing issue, when a reviewer says "I can't
picture it".

**When not to.** A change with no screen. Skip it and say why.

## Extensions (read this first)

Before anything else, look for wrappers that extend this skill.

1. Read every `SKILL.md` under `.radial/skills/` in the repo (project scope), then every one under `~/.config/radial/skills/` (user scope). A wrapper is a skill whose frontmatter carries `extends: <the name of this skill>`.
2. Project scope wins whole. If any project wrapper extends this skill, apply the project wrappers and ignore the user ones entirely; the two scopes are never merged.
3. Two wrappers in the same scope extending this skill: apply neither, and say so in your first message, naming both files.
4. Apply the wrapper's preamble (everything above its first `##` heading) as a standing instruction for the whole run, and each `## <hook>` section at the matching `[HOOK: <hook>]` marker below.
5. A wrapper adds rules and raises bars. It cannot remove a step, lower a bar, or send output somewhere this skill does not name. If a section tries, follow this skill and say plainly in your output that you did not follow that section, and why.

## How it runs

### 1. Find the source

Either a plan file at `.radial/plans/<slug>.md`, or an issue:

```
radial show RAD-374 --team RAD --json
```

Read every `**UX:**` line and every `**Browse checks:**` block. Those are the
screens and the states. A plan with no UX line has nothing to prototype: say so
and stop.

### 2. Learn what the product already looks like

A prototype that does not look like the app is a distraction, because reviewers
spend the review arguing about your invented visual language. Before drawing
anything, find the real one: the stylesheet or theme file, the colour tokens,
the type scale, the spacing rhythm, the corner radius, one shipped screen to
copy the chrome from. Name the files you read in your report.

If the repo genuinely has no visual language yet, say so and pick one
deliberately: a neutral grey scale, one accent, one font stack, and say which.

[HOOK: extra-craft]

### 3. Build one file

`.radial/prototypes/<slug>.html`. The constraints exist so it opens anywhere,
forever, from a Preview URL with no network:

- One file. CSS in a `<style>`, JS in a `<script>`, images inline as data URIs
  or omitted.
- **No external URL of any kind.** No CDN, no Google Fonts, no unpkg. A
  prototype that needs the network is a prototype that renders blank in the
  reviewer's sandbox.
- A screen index at the top: every screen as a labelled button that shows it,
  so a reviewer can reach all of them without guessing.
- Every state the plan names: empty, loading, error, populated, permission
  denied. States are where designs actually fail.
- Real copy. Placeholder text hides the hardest layout problems, which are
  always the long strings.
- Interactivity only where it carries meaning: the disclosure opens, the tab
  switches, the row selects. No routing, no persistence.

[HOOK: extra-screens]

### 4. Look at it

Open the file and look at every screen at desktop width, then at 390px. Fix
what you see: overflow, a truncated label, a control that vanishes, contrast
you cannot read. If you have a browser tool, take a screenshot of each screen
and read it back; if you do not, say in the report that you did not look at
rendered output, because unrendered HTML is a claim, not evidence.

[HOOK: save-bar]

The bar before it is worth attaching:

- Every screen the plan names exists and is reachable from the index.
- Every state named in a `**Browse checks:**` line is shown somewhere.
- Nothing overflows horizontally at 390px.
- `grep` the file for `http://` and `https://`: zero hits outside comments.
- It looks like the product, or it says plainly which visual language it chose.

### 5. Attach it

When the tree exists:

```
radial attach RAD-374 .radial/prototypes/<slug>.html --name "<slug> prototype" --team RAD
```

Take the Preview URL from the output and add it to the parent body as a
`**Prototype:**` line, with `radial update RAD-374 --description-file <file>`
after editing the body locally. Re-attaching a revision means deleting the old
attachment first (`radial attachments RAD-374`, then
`radial attachments delete <id>`), so the newest file is unambiguous.

When the tree does not exist yet, leave the file where it is and say so;
`rd-issues` attaches it when it files the parent.

[HOOK: extra-notes]

### 6. Report

The local path, the Preview URL as a clickable link, the screens you built, and
what you deliberately left out. Then ask for a reaction: the prototype exists
to be rejected cheaply.

[HOOK: extra-checks]

## Extension points

| Hook | Where it fires | What a section here can add |
| --- | --- | --- |
| `extra-craft` | After reading the product's visual language, before building | Design-system specifics: token names, a component to mimic, a density rule, an accessibility floor |
| `extra-screens` | After the screens are built, before reviewing them | More required screens or states: a print view, an RTL pass, a specific breakpoint |
| `save-bar` | At the self-review, before attaching | Raise the bar: a contrast ratio, a screenshot of every screen, a second reviewer |
| `extra-notes` | After attaching, before the report | Extra recording: a design-doc link, a comment on the issue, a note in the parent body |
| `extra-checks` | At the end of the report | Final checks this team wants stated: who must react, by when |

## What it never does

- It never fetches anything at runtime; the file has no external URL in it.
- It never becomes production code. Nothing from it is copied into `src/` without being rewritten.
- It never leaves two attachments claiming to be the current prototype.
- It never changes an issue's status, assignee or labels.
- It never runs `radial` calls in parallel.
