"""Creates a detached git worktree at the PR head for one AI reviewer.

Worktree lands under <main repo>/.claude/worktrees/ai-review-<pr>-<model>-<head7>, checked
out detached at --head, so the reviewer reads the PR version of every file straight from disk
and never has to move the checkout itself. A leftover worktree from an aborted run at the
same head is removed first when it is clean; a dirty one aborts.

Usage: python3 new_reviewer_worktree.py --pr <number> --head <sha> --model <sonnet|opus>
Prints the worktree path.
"""

import argparse
import subprocess
import sys

from github_common import GitHubError, main_repo_root, registered_worktrees, run_git


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pr", type=int, required=True, help="PR number, used only to name the path")
    parser.add_argument("--head", required=True, help="commit the worktree is detached at")
    parser.add_argument("--model", required=True, choices=["sonnet", "opus"],
                        help="reviewer label, used only to name the path")
    args = parser.parse_args()

    repo_root = main_repo_root()

    resolve = subprocess.run(
        ["git", "-C", str(repo_root), "rev-parse", "--verify", "--quiet", f"{args.head}^{{commit}}"],
        capture_output=True, text=True, encoding="utf-8",
    )
    if resolve.returncode != 0 or not resolve.stdout.strip():
        raise GitHubError(
            f"head '{args.head}' does not resolve to a commit - run get_pr_review_context.py "
            "first so it is fetched."
        )
    head_sha = resolve.stdout.strip()

    # Head sha in the name: a re-run on a new push never shares a path with a round still reviewing.
    path = repo_root / ".claude" / "worktrees" / f"ai-review-{args.pr}-{args.model}-{head_sha[:7]}"

    if str(path) in registered_worktrees(repo_root):
        if run_git("-C", str(path), "status", "--porcelain"):
            raise GitHubError(f"Stale reviewer worktree at {path} has local changes - not removing it.")
        run_git("-C", str(repo_root), "worktree", "remove", str(path), "--force")
    elif path.exists():
        raise GitHubError(f"Path {path} exists but is not a registered worktree - remove it manually.")

    run_git("-C", str(repo_root), "worktree", "add", "--quiet", "--detach", str(path), head_sha)

    actual = run_git("-C", str(path), "rev-parse", "HEAD")
    problem = None
    if actual != head_sha:
        problem = f"Worktree HEAD {actual} does not match requested {head_sha}."
    elif run_git("-C", str(path), "status", "--porcelain"):
        problem = f"Fresh worktree at {path} is not clean."
    if problem:
        # do not leak a registered worktree the caller never learned about
        run_git("-C", str(repo_root), "worktree", "remove", str(path), "--force")
        raise GitHubError(problem)

    print(path)


if __name__ == "__main__":
    try:
        main()
    except GitHubError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)
