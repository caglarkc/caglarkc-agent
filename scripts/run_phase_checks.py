#!/usr/bin/env python3
"""Run all phased acceptance scripts in order; single exit summary for CI / local QA."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

# Order reflects delivery dependency; keep in sync with docs/PHASE_ACCEPTANCE.md
PHASE_SCRIPTS: list[tuple[str, Path]] = [
    ("Phase 1 (connections)", ROOT / "scripts" / "check_connections.py"),
    ("Phase 1.5 (contract)", ROOT / "scripts" / "check_phase1_5.py"),
    ("Phase 2 (graph)", ROOT / "scripts" / "check_phase2.py"),
    ("Phase 3 (workers)", ROOT / "scripts" / "check_phase3.py"),
    ("Phase 4 (review)", ROOT / "scripts" / "check_phase4.py"),
    ("Phase 5 (CLI)", ROOT / "scripts" / "check_phase5.py"),
    ("Phase 6 (Telegram)", ROOT / "scripts" / "check_phase6.py"),
    ("Phase 7 (daemon)", ROOT / "scripts" / "check_phase7.py"),
    ("Phase 8 (projects)", ROOT / "scripts" / "check_phase8.py"),
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Run phased acceptance scripts sequentially.")
    parser.add_argument("--stop-on-fail", action="store_true", help="Stop after first nonzero exit.")
    args = parser.parse_args()

    env = os.environ.copy()
    roots = str(ROOT)
    env["PYTHONPATH"] = roots + os.pathsep + env.get("PYTHONPATH", "") if env.get("PYTHONPATH") else roots
    cwd = str(ROOT)

    failed: list[str] = []
    for label, script in PHASE_SCRIPTS:
        if not script.is_file():
            print(f"[SKIP] {label}: missing {script}", flush=True)
            failed.append(label)
            if args.stop_on_fail:
                break
            continue
        print(f"\n>>> {label}: {script.name}\n", flush=True)
        rc = subprocess.call([sys.executable, str(script)], cwd=cwd, env=env)
        if rc != 0:
            failed.append(label)
            if args.stop_on_fail:
                break

    print("\n=== RUN_PHASE_CHECKS SUMMARY ===", flush=True)
    print(f"TOTAL: {len(PHASE_SCRIPTS)} | FAIL_COUNT: {len(failed)}", flush=True)
    if failed:
        print("FAILED:", flush=True)
        for item in failed:
            print(f"  - {item}", flush=True)
        return 1
    print("OVERALL_PHASE_STATUS: READY", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
