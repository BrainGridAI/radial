#!/usr/bin/env python3
"""Run a shell command N times, record wall-clock per trial, print median/p10/p90 as JSON.

Usage: timeit.py <n> <out.json> -- <command...>
RADIAL_KEY is always removed from the child environment.
"""
import json, os, statistics, subprocess, sys, time

def pct(xs, p):
    xs = sorted(xs)
    if len(xs) == 1:
        return xs[0]
    k = (len(xs) - 1) * p
    lo, hi = int(k), min(int(k) + 1, len(xs) - 1)
    return xs[lo] + (xs[hi] - xs[lo]) * (k - lo)

def main():
    n, out = int(sys.argv[1]), sys.argv[2]
    cmd = sys.argv[sys.argv.index("--") + 1:]
    env = {k: v for k, v in os.environ.items() if k != "RADIAL_KEY"}
    trials = []
    for i in range(n):
        t0 = time.perf_counter()
        p = subprocess.run(cmd, env=env, capture_output=True)
        dt = (time.perf_counter() - t0) * 1000
        trials.append({"i": i, "ms": round(dt, 2), "rc": p.returncode, "stdout_bytes": len(p.stdout), "stderr_bytes": len(p.stderr)})
    ms = [t["ms"] for t in trials]
    res = {"cmd": cmd, "n": n, "median_ms": round(statistics.median(ms), 2), "p10_ms": round(pct(ms, 0.1), 2), "p90_ms": round(pct(ms, 0.9), 2), "trials": trials}
    with open(out, "w") as f:
        json.dump(res, f, indent=1)
    print(json.dumps({k: res[k] for k in ("n", "median_ms", "p10_ms", "p90_ms")}))

if __name__ == "__main__":
    main()
