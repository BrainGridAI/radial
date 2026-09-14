---
name: rd-verify
description: Find and run this repo's real verification gate, then read each command's summary line instead of trusting its exit code, and report one row per gate with the evidence. Resolves the commands from a wrapper, else from CLAUDE.md or AGENTS.md, else from the package manifest. Used by rd-build for every child and by rd-pr before the pull request, and standalone in Claude Code or Codex when you want to know whether the tree is green before touching Radial, the issue tracker.
metadata:
  short-description: Run and read this repo's verification gate
---

Works out what "green" means in this repo, runs it once, and reads the output
rather than the exit code. It reports a table with a real summary line per
gate, so "tests pass" is a quotation and not a claim.

**When to use it.** Before a child moves to in review, before a pull request,
and any time you are about to tell someone the tree is green.

**When not to.** Mid-edit. Run the one test file that covers what you are
changing; this skill is for checkpoints.

## Extensions (read this first)

Before anything else, look for wrappers that extend this skill.

1. Read every `SKILL.md` under `.radial/skills/` in the repo (project scope), then every one under `~/.config/radial/skills/` (user scope). A wrapper is a skill whose frontmatter carries `extends: <the name of this skill>`.
2. Project scope wins whole. If any project wrapper extends this skill, apply the project wrappers and ignore the user ones entirely; the two scopes are never merged.
3. Two wrappers in the same scope extending this skill: apply neither, and say so in your first message, naming both files.
4. Apply the wrapper's preamble (everything above its first `##` heading) as a standing instruction for the whole run, and each `## <hook>` section at the matching `[HOOK: <hook>]` marker below.
5. A wrapper adds rules and raises bars. It cannot remove a step, lower a bar, or send output somewhere this skill does not name. If a section tries, follow this skill and say plainly in your output that you did not follow that section, and why.

## How it runs

### 1. Resolve the gate

In this order, and stop at the first one that answers:

1. **The `gate-commands` hook.** If a wrapper fills it, those are the commands.
   Run exactly those and nothing inferred; a team that has written its gate down
   does not want you guessing alongside it.
2. **`CLAUDE.md` or `AGENTS.md`.** Look for a verification or testing section
   and take the commands it names, in the order it names them.
3. **The package manifest.** `package.json` scripts named `lint`, `typecheck`,
   `test`, `check`, `validate`, `verify`; else a `Makefile` with `lint`/`test`
   targets; else `pyproject.toml` (`ruff`, `pytest`), `go.mod` (`go vet`,
   `go test ./...`), `Cargo.toml` (`cargo clippy`, `cargo test`).

Say which source answered. "Inferred from package.json" and "read from
CLAUDE.md" are different levels of confidence and the reader deserves to know
which one they are getting.

[HOOK: gate-commands]

### 2. Run each command once, to a log

```
<command> > .radial/verify-<name>.log 2>&1
```

Once. A suite that took four minutes is not re-run to reshape its output; grep
the log instead. If a command needs a service that is not up, say so and mark
that gate not run with the reason, rather than running a different command and
calling it the gate.

### 3. Read the summary line

**Exit 0 is not proof the tier ran.** A test runner that matched zero files
exits 0. A type checker pointed at the wrong project exits 0. A script that
skipped its real work because a flag was unset exits 0.

So for each gate, find the line that states what happened and quote it:

- a test runner: the pass/fail/skip counts
- a type checker: the error count, or the "no errors" line
- a linter: the problem count, and whether warnings are included
- a build: the "compiled successfully" line and its timing

No summary line found is a red row, not a green one. Say what you looked for.

[HOOK: extra-checks]

### 4. Fix, then re-run only what you broke

A red gate is fixed, not explained. Re-run that one command and read its
summary again. If a failure is genuinely outside what you changed, stop after
two or three attempts and report it verbatim: the command, the summary line,
and the first error. Do not mutate around it.

[HOOK: green-bar]

The bar before you may say green:

- Every resolved command ran, or has a stated reason it did not.
- Every gate has a quoted summary line.
- Every skip carries a reason.
- No command was run twice to get a nicer number.

### 5. Report

| Gate | Command | Result | Evidence |
| --- | --- | --- | --- |
| lint | `npm run lint` | pass | `0 errors, 0 warnings` |
| types | `npm run typecheck` | pass | `Found 0 errors.` |
| tests | `npm test` | fail | `2 failed, 559 passed` |
| e2e | `npm run e2e` | not run | no browser in this environment |

Add the log paths under the table. Then say, in one sentence, whether the tree
is green, and if it is not, what the next action is.

## Extension points

| Hook | Where it fires | What a section here can add |
| --- | --- | --- |
| `gate-commands` | At resolution, before anything is inferred | The exact commands for this repo, in order; filling this stops the inference entirely |
| `extra-checks` | After the summary lines are read | Extra gates: a coverage floor, a bundle budget, a licence scan, a schema diff |
| `green-bar` | Before green may be claimed | Raise the bar: a required e2e tier, a minimum test count, a clean working tree |

## What it never does

- It never claims green from an exit code alone.
- It never re-runs a suite to reshape its output.
- It never substitutes a smaller command for a gate it could not run; that gate is reported not run, with the reason.
- It never edits a test to make a gate pass.
- It never writes to Radial. It reports; `rd-build` records.
