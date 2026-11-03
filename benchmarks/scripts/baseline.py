#!/usr/bin/env python3
"""No-tracker baseline: markdown TODO.md in git + local agent logs.

Scripted agents run tasks T1-T5, T7, T8 (T6 has no equivalent; see METHODOLOGY.md)
plus a 2-agent concurrent claim race and TODO.md merge-conflict tests.

Every shell command a scripted agent issues goes through `Agent.sh`, which counts
it and the bytes it reads back (stdout), so "commands" and "context bytes re-fed"
are measured, not assumed. Network is never touched: remotes are local bare repos.

Usage: baseline.py <out_dir> [--n 10] [--seed-tasks 50] [--seed-decisions 200]
"""
import argparse, json, os, random, shutil, statistics, subprocess, tempfile, threading, time
from pathlib import Path

ENV = {k: v for k, v in os.environ.items() if k != "RADIAL_KEY"}
ENV.update(GIT_AUTHOR_NAME="bench", GIT_AUTHOR_EMAIL="bench@local", GIT_COMMITTER_NAME="bench",
           GIT_COMMITTER_EMAIL="bench@local", GIT_CONFIG_GLOBAL="/dev/null", GIT_CONFIG_NOSYSTEM="1")


def pct(xs, p):
    xs = sorted(xs)
    k = (len(xs) - 1) * p
    lo, hi = int(k), min(int(k) + 1, len(xs) - 1)
    return xs[lo] + (xs[hi] - xs[lo]) * (k - lo)


class Agent:
    def __init__(self, name, cwd):
        self.name, self.cwd = name, cwd
        self.commands, self.bytes_read, self.errors, self.log = 0, 0, 0, []

    def sh(self, cmd, check=True, stdin=None):
        self.commands += 1
        p = subprocess.run(cmd, shell=True, cwd=self.cwd, env=ENV, capture_output=True, text=True, input=stdin)
        self.bytes_read += len(p.stdout.encode()) + len(p.stderr.encode())
        self.log.append({"cmd": cmd, "rc": p.returncode, "out_bytes": len(p.stdout.encode())})
        if p.returncode != 0:
            self.errors += 1
            if check:
                raise RuntimeError(f"{self.name}: {cmd} -> {p.returncode}: {p.stderr[:300]}")
        return p

    def stats(self):
        return {"commands": self.commands, "bytes_read": self.bytes_read, "errors": self.errors}


def git(cwd, *args):
    return subprocess.run(["git", *args], cwd=cwd, env=ENV, capture_output=True, text=True)


def seed_repo(root, n_tasks, n_decisions):
    """A project with history: n_tasks TODO lines (half done), n_decisions in DECISIONS.md, session logs."""
    bare = root / "remote.git"
    git(root, "init", "-q", "--bare", "-b", "main", str(bare))
    work = root / "seed"
    git(root, "clone", "-q", str(bare), str(work))
    rnd = random.Random(42)
    lines = ["# TODO", "", "Format: `- [ ] T-<n> <title> (owner: <agent|->) [status]`", ""]
    for i in range(1, n_tasks + 1):
        done = i <= n_tasks // 2
        owner = rnd.choice(["agent-a", "agent-b"]) if done else "-"
        lines.append(f"- [{'x' if done else ' '}] T-{i:03d} Task number {i} for module {rnd.choice('abcdef')} (owner: {owner}) [{'done' if done else 'todo'}]")
    (work / "TODO.md").write_text("\n".join(lines) + "\n")
    dec = ["# Decisions", ""]
    for i in range(1, n_decisions + 1):
        topic = rnd.choice(["auth", "billing", "search", "cache", "queue", "schema"])
        dec.append(f"## D-{i:03d} {topic}: choose option {rnd.randint(1, 3)} (2026-{rnd.randint(1, 10):02d}-{rnd.randint(1, 28):02d})")
        dec.append(f"Context: decided {topic} approach {i} after comparing alternatives. Owner: agent-{rnd.choice('ab')}.")
        dec.append("")
    dec.append("## D-999 rate-limiter: use token bucket, not fixed window (2026-10-30)")
    dec.append("Context: fixed window let bursts through at boundaries.")
    (work / "DECISIONS.md").write_text("\n".join(dec) + "\n")
    logs = work / "logs"
    logs.mkdir()
    for s in range(1, 21):
        with open(logs / f"session-{s:03d}.jsonl", "w") as f:
            for e in range(40):
                f.write(json.dumps({"session": s, "seq": e, "kind": rnd.choice(["tool_use", "assistant", "result"]),
                                    "text": f"step {e} of session {s} touching T-{rnd.randint(1, n_tasks):03d}"}) + "\n")
    git(work, "add", "-A")
    git(work, "commit", "-qm", "seed")
    git(work, "push", "-q", "origin", "main")
    return bare


def clone(bare, dest):
    git(dest.parent, "clone", "-q", str(bare), str(dest))
    return dest


# ---- tasks -----------------------------------------------------------------

def t1_create(a, title="New bug in search"):
    a.sh("git pull -q --rebase")
    n = int(a.sh("grep -c '^- \\[' TODO.md").stdout.strip()) + 1
    a.sh(f"printf '%s\\n' '- [ ] T-{n:03d} {title} (owner: -) [todo]' >> TODO.md")
    a.sh(f"git commit -qam 'todo: add T-{n:03d}'")
    a.sh("git push -q")
    return f"T-{n:03d}"


def t2_pickup(a):
    a.sh("git pull -q --rebase")
    line = a.sh("grep -m1 -n '^- \\[ \\] T-[0-9]* .*(owner: -)' TODO.md").stdout.strip()
    lineno, rest = line.split(":", 1)
    tid = rest.split()[3]
    a.sh(f"sed -i '{lineno}s/(owner: -) \\[todo\\]/(owner: {a.name}) [in-progress]/' TODO.md")
    a.sh(f"git commit -qam 'todo: {a.name} claims {tid}'")
    a.sh("git push -q")
    return tid


def t3_status_proof(a, tid):
    a.sh("mkdir -p proof && echo 'tests: 12 passed, 0 failed' > proof/" + tid + ".txt")
    a.sh(f"sed -i '/{tid} /s/\\[in-progress\\]/[review] proof: proof\\/{tid}.txt/' TODO.md")
    a.sh(f"git add -A && git commit -qm 'todo: {tid} review with proof'")
    a.sh("git push -q")


def t4_close(a, tid):
    a.sh("git pull -q --rebase")
    a.sh(f"sed -i '/{tid} /{{s/^- \\[ \\]/- [x]/;s/\\[review\\]/[done]/}}' TODO.md")
    a.sh(f"printf '%s\\n' '' '### {tid} done-note' 'Shipped; proof in proof/{tid}.txt.' >> DONE.md")
    a.sh(f"git add -A && git commit -qm 'todo: close {tid}'")
    a.sh("git push -q")


def t5_find_decision(a):
    # The agent does not know the id; it greps by topic, then reads git history for the why.
    hit = a.sh("grep -n -i -A1 'rate-limiter' DECISIONS.md").stdout
    a.sh("git log -S'token bucket' --format='%h %s' -- DECISIONS.md")
    return "D-999" in hit


def t7_handoff(a, b, tid):
    a.sh(f"sed -i '/{tid} /s/(owner: {a.name})/(owner: {b.name}) handoff: see HANDOFF.md/' TODO.md")
    a.sh(f"printf '%s\\n' '## {tid} handoff {a.name} -> {b.name}' 'Done: parser. Next: wire CLI flag. Branch: feat/{tid.lower()}' >> HANDOFF.md")
    a.sh(f"git add -A && git commit -qm 'handoff {tid}' && git push -q")
    b.sh("git pull -q --rebase")
    b.sh(f"grep -n '{tid} ' TODO.md")
    out = b.sh(f"grep -A2 '## {tid} handoff' HANDOFF.md").stdout
    return "Next:" in out


def t8_resume(a):
    """A fresh session with no memory: read the task file, the newest session log, recent git history."""
    a.sh("git pull -q --rebase")
    a.sh("cat TODO.md")
    newest = a.sh("ls -t logs | head -1").stdout.strip()
    a.sh(f"cat logs/{newest}")
    a.sh("git log -10 --format='%h %s'")
    a.sh("cat HANDOFF.md 2>/dev/null || true", check=False)
    return bool(newest)


# ---- runners ---------------------------------------------------------------

def run_tasks(root, n, n_tasks, n_decisions):
    results = {k: [] for k in ["T1", "T2", "T3", "T4", "T5", "T7", "T8"]}
    for trial in range(n):
        d = Path(tempfile.mkdtemp(dir=root))
        bare = seed_repo(d, n_tasks, n_decisions)
        wa, wb = clone(bare, d / "a"), clone(bare, d / "b")

        def timed(key, fn, *args, agents):
            before = [ag.stats() for ag in agents]
            t0 = time.perf_counter()
            ok = fn(*args)
            ms = (time.perf_counter() - t0) * 1000
            after = [ag.stats() for ag in agents]
            row = {"trial": trial, "ms": round(ms, 2), "ok": ok if isinstance(ok, bool) else True}
            for f in ("commands", "bytes_read", "errors"):
                row[f] = sum(x[f] - y[f] for x, y in zip(after, before))
            results[key].append(row)
            return ok

        a, b = Agent("agent-a", wa), Agent("agent-b", wb)
        timed("T1", t1_create, a, agents=[a])
        tid = timed("T2", t2_pickup, a, agents=[a])
        timed("T3", t3_status_proof, a, tid, agents=[a])
        timed("T4", t4_close, a, tid, agents=[a])
        timed("T5", t5_find_decision, a, agents=[a])
        tid2 = t2_pickup(a)
        timed("T7", t7_handoff, a, b, tid2, agents=[a, b])
        fresh = Agent("agent-c", clone(bare, d / "c"))
        timed("T8", t8_resume, fresh, agents=[fresh])
        shutil.rmtree(d)
    summary = {}
    for k, rows in results.items():
        ms = [r["ms"] for r in rows]
        summary[k] = {"n": len(rows), "median_ms": round(statistics.median(ms), 2), "p10_ms": round(pct(ms, .1), 2),
                      "p90_ms": round(pct(ms, .9), 2), "commands": rows[0]["commands"],
                      "context_bytes_median": statistics.median(r["bytes_read"] for r in rows),
                      "errors_total": sum(r["errors"] for r in rows), "ok_all": all(r["ok"] for r in rows)}
    return {"summary": summary, "trials": results}


def claim_race_shared_checkout(root, n):
    """Two agents in ONE working directory (no git sync between them), each does read-pick-write on TODO.md
    at the same moment. Measures lost updates / double claims."""
    out = []
    for trial in range(n):
        d = Path(tempfile.mkdtemp(dir=root))
        bare = seed_repo(d, 20, 5)
        w = clone(bare, d / "w")
        barrier = threading.Barrier(2)
        picked = {}

        def agent(name):
            todo = w / "TODO.md"
            barrier.wait()
            text = todo.read_text()
            lines = text.splitlines()
            for i, l in enumerate(lines):
                if l.startswith("- [ ]") and "(owner: -)" in l:
                    picked[name] = l.split()[3]
                    lines[i] = l.replace("(owner: -) [todo]", f"(owner: {name}) [in-progress]")
                    break
            time.sleep(random.uniform(0, 0.005))  # think time between read and write
            todo.write_text("\n".join(lines) + "\n")

        ts = [threading.Thread(target=agent, args=(nm,)) for nm in ("agent-a", "agent-b")]
        [t.start() for t in ts]
        [t.join() for t in ts]
        final = (w / "TODO.md").read_text()
        # An agent "silently lost" when it believes it owns a task but the file names someone else on that line.
        line_of = {nm: next(l for l in final.splitlines() if f" {tid} " in l) for nm, tid in picked.items()}
        silent_losers = [nm for nm, l in line_of.items() if f"(owner: {nm})" not in l]
        out.append({"trial": trial, "picked": picked, "same_task": len(set(picked.values())) == 1,
                    "final_lines": line_of, "silent_losers": silent_losers, "lost_update": bool(silent_losers)})
        shutil.rmtree(d)
    return out


def claim_race_git(root, n):
    """Two agents in separate clones claim the next task concurrently and push. Measures: both picked the same
    task, push rejections, rebase conflicts, and whether the loser can detect the double claim."""
    out = []
    for trial in range(n):
        d = Path(tempfile.mkdtemp(dir=root))
        bare = seed_repo(d, 20, 5)
        agents = [Agent("agent-a", clone(bare, d / "a")), Agent("agent-b", clone(bare, d / "b"))]
        barrier = threading.Barrier(2)
        res = {}

        def run(ag):
            line = ag.sh("grep -m1 -n '^- \\[ \\] T-[0-9]* .*(owner: -)' TODO.md").stdout.strip()
            lineno, rest = line.split(":", 1)
            tid = rest.split()[3]
            ag.sh(f"sed -i '{lineno}s/(owner: -) \\[todo\\]/(owner: {ag.name}) [in-progress]/' TODO.md")
            ag.sh(f"git commit -qam 'claim {tid}'")
            barrier.wait()
            p = ag.sh("git push -q", check=False)
            r = {"tid": tid, "push_rejected": p.returncode != 0}
            if p.returncode != 0:
                rb = ag.sh("git pull -q --rebase", check=False)
                r["rebase_conflict"] = rb.returncode != 0
                if rb.returncode != 0:
                    ag.sh("git rebase --abort", check=False)
            res[ag.name] = r

        ts = [threading.Thread(target=run, args=(ag,)) for ag in agents]
        [t.start() for t in ts]
        [t.join() for t in ts]
        same = res["agent-a"]["tid"] == res["agent-b"]["tid"]
        out.append({"trial": trial, "same_task": same, **{k: v for k, v in res.items()},
                    "extra_commands_for_loser": max(a.commands for a in agents) - min(a.commands for a in agents)})
        shutil.rmtree(d)
    return out


def merge_conflicts(root, n):
    """Two branches edit TODO.md, then merge. Three patterns, n trials each, randomised task positions."""
    patterns = {
        "both_append_new_task": lambda la, lb: ("append", "append"),
        "close_far_apart_tasks": lambda la, lb: ("edit", "edit_far"),
        "close_adjacent_tasks": lambda la, lb: ("edit", "edit_adjacent"),
    }
    out = {}
    rnd = random.Random(7)
    for pname in patterns:
        rows = []
        for trial in range(n):
            d = Path(tempfile.mkdtemp(dir=root))
            bare = seed_repo(d, 40, 5)
            w = clone(bare, d / "w")
            base = 30 + rnd.randint(0, 8)  # an open task index (tasks 21-40 are open)
            git(w, "checkout", "-qb", "agent-a")
            todo = w / "TODO.md"

            def edit(task_no):
                todo.write_text(todo.read_text().replace(f"- [ ] T-{task_no:03d}", f"- [x] T-{task_no:03d}"))

            if pname == "both_append_new_task":
                with open(todo, "a") as f: f.write("- [ ] T-041 from agent-a (owner: -) [todo]\n")
            else:
                edit(base)
            git(w, "commit", "-qam", "a")
            git(w, "checkout", "-q", "main")
            git(w, "checkout", "-qb", "agent-b")
            if pname == "both_append_new_task":
                with open(todo, "a") as f: f.write("- [ ] T-041 from agent-b (owner: -) [todo]\n")
            elif pname == "close_far_apart_tasks":
                edit(base - 8)
            else:
                edit(base + 1)
            git(w, "commit", "-qam", "b")
            git(w, "checkout", "-q", "agent-a")
            m = git(w, "merge", "-q", "--no-edit", "agent-b")
            rows.append({"trial": trial, "conflict": m.returncode != 0, "base_task": base})
            shutil.rmtree(d)
        out[pname] = {"n": n, "conflicts": sum(r["conflict"] for r in rows), "trials": rows}
    return out


def t5_scaling(root):
    """Context bytes an agent re-reads to find a decision or resume, as the project grows."""
    rows = []
    for n_dec in (50, 200, 1000):
        d = Path(tempfile.mkdtemp(dir=root))
        bare = seed_repo(d, n_dec // 4, n_dec)
        w = clone(bare, d / "w")
        size = (w / "DECISIONS.md").stat().st_size
        todo = (w / "TODO.md").stat().st_size
        rows.append({"decisions": n_dec, "tasks": n_dec // 4, "DECISIONS_md_bytes": size, "TODO_md_bytes": todo,
                     "full_read_bytes_if_agent_cats_both": size + todo})
        shutil.rmtree(d)
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--n", type=int, default=10)
    ap.add_argument("--seed-only", action="store_true", help="seed one project into <out>/repo and exit")
    args = ap.parse_args()
    out = Path(args.out)
    if args.seed_only:
        out.mkdir(parents=True, exist_ok=True)
        clone(seed_repo(out, 50, 200), out / "repo")
        print(out / "repo")
        return
    out.mkdir(parents=True, exist_ok=True)
    root = Path(tempfile.mkdtemp(prefix="bench-baseline-"))
    random.seed(1)
    meta = {"git": subprocess.run(["git", "--version"], capture_output=True, text=True).stdout.strip(),
            "python": subprocess.run(["python3", "--version"], capture_output=True, text=True).stdout.strip(),
            "n": args.n, "started": time.strftime("%Y-%m-%dT%H:%M:%S%z")}
    tasks = run_tasks(root, args.n, 50, 200)
    (out / "tasks.json").write_text(json.dumps(tasks, indent=1))
    shared = claim_race_shared_checkout(root, max(args.n, 20))
    (out / "claim-race-shared-checkout.json").write_text(json.dumps(shared, indent=1))
    gitrace = claim_race_git(root, max(args.n, 20))
    (out / "claim-race-git.json").write_text(json.dumps(gitrace, indent=1))
    merges = merge_conflicts(root, args.n)
    (out / "merge-conflicts.json").write_text(json.dumps(merges, indent=1))
    scaling = t5_scaling(root)
    (out / "context-scaling.json").write_text(json.dumps(scaling, indent=1))
    shutil.rmtree(root)
    summary = {
        "meta": meta,
        "tasks": tasks["summary"],
        "claim_race_shared_checkout": {"n": len(shared), "same_task": sum(r["same_task"] for r in shared),
                                       "lost_update": sum(r["lost_update"] for r in shared)},
        "claim_race_git": {"n": len(gitrace), "same_task": sum(r["same_task"] for r in gitrace),
                           "push_rejected": sum(r["agent-a"]["push_rejected"] or r["agent-b"]["push_rejected"] for r in gitrace),
                           "rebase_conflict": sum(bool(r["agent-a"].get("rebase_conflict") or r["agent-b"].get("rebase_conflict")) for r in gitrace)},
        "merge_conflicts": {k: {"n": v["n"], "conflicts": v["conflicts"]} for k, v in merges.items()},
        "context_scaling": scaling,
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=1))
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
