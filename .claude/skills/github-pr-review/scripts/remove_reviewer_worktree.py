"""Removes reviewer worktrees created by new_reviewer_worktree.py - by exact path, or stale ones.

--path: each path must be a registered ai-review-* worktree with no local changes; anything
else is skipped and reported, never forced.
--stale: every registered ai-review-* worktree under <repo>/.claude/worktrees older than
--older-than-hours (default 2) and clean is removed - the reclaim path for runs whose parent
session died before cleanup. A round in progress is younger than that and untouched.
Other sessions run their own worktrees under the same directory - this never sweeps outside
the ai-review-* name, never by wildcard beyond it, and never prunes. Reviewer worktrees are
detached, so there is no branch to delete.

Usage: python3 remove_reviewer_worktree.py --path <p> [--path <p> ...]
       python3 remove_reviewer_worktree.py --stale [--older-than-hours 2]
Prints JSON: removed and skipped paths with reasons.
"""

import argparse
import fnmatch
import os
import subprocess
import sys
import time
from pathlib import Path

from github_common import GitHubError, main_repo_root, print_json, registered_worktrees, run_git


def created_at(path: str) -> float:
    """Creation time where the platform records one (macOS, Windows), else last change time."""
    st = os.stat(path)
    return getattr(st, "st_birthtime", st.st_ctime)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--path", action="append", default=None,
                       help="worktree path to remove; repeat for several")
    group.add_argument("--stale", action="store_true",
                       help="remove clean ai-review-* worktrees older than --older-than-hours")
    parser.add_argument("--older-than-hours", type=float, default=2.0)
    args = parser.parse_args()

    repo_root = main_repo_root()
    registered = registered_worktrees(repo_root)
    pattern = str(Path(repo_root) / ".claude" / "worktrees" / "ai-review-*")

    if args.stale:
        cutoff = time.time() - args.older_than_hours * 3600
        # A registered worktree whose directory is already gone is the classic leftover: always stale.
        paths = [
            p for p in registered
            if fnmatch.fnmatch(p, pattern)
            and (not os.path.exists(p) or created_at(p) < cutoff)
        ]
        mode = "stale"
    else:
        paths = args.path
        mode = "path"

    removed, skipped = [], []
    for p in paths:
        full = os.path.normpath(os.path.abspath(p))
        if full not in registered:
            skipped.append({"path": full, "reason": "not a registered worktree"})
            continue
        if not fnmatch.fnmatch(full, pattern):
            skipped.append({"path": full, "reason": "not an ai-review worktree"})
            continue
        if os.path.exists(full) and run_git("-C", full, "status", "--porcelain"):
            skipped.append({"path": full, "reason": "local changes"})
            continue
        result = subprocess.run(
            ["git", "-C", str(repo_root), "worktree", "remove", full, "--force"],
            capture_output=True, text=True, encoding="utf-8",
        )
        if result.returncode != 0:
            skipped.append(
                {"path": full, "reason": f"git worktree remove failed ({result.returncode})"}
            )
            continue
        removed.append(full)
    # No `git worktree prune`: it is repo-wide and would unregister other sessions' worktrees.

    print_json({"mode": mode, "removed": removed, "skipped": skipped})


if __name__ == "__main__":
    try:
        main()
    except GitHubError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)
