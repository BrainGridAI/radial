---
name: team-example
description: Our team's rules on top of rd-example. Use it exactly where you would use rd-example; it runs the same procedure with our extra checks.
extends: rd-example
---

<!--
  WRAPPER TEMPLATE — the shape of an extension.

  A wrapper is an ordinary skill folder. Put it at:
    .radial/skills/<name>/SKILL.md          (project scope — commit it)
    ~/.config/radial/skills/<name>/SKILL.md  (user scope — yours alone)

  Frontmatter is `name`, `description`, `extends`. `extends` names the built-in
  this wrapper adds to; a name starting with `rd-` is reserved, so a wrapper
  cannot take one.

  Everything above the first `##` heading is the preamble: standing instruction
  for the whole run. Each `## <hook>` heading must be one of the built-in's
  extension points; `radial skills extend rd-example --name team-example`
  scaffolds the file with every heading already in place, so nobody has to
  memorise marker names.

  A wrapper adds rules and raises bars. It cannot remove a step, lower a bar, or
  redirect output somewhere the built-in does not name.
-->

This extends `rd-example`: read that skill first, then apply the sections below
at their hooks.

## extra-checks

- Refuse to continue on a dirty working tree; print `commit or stash first`.

## after-example

- Post the report to `#eng-releases` with the issue link.
