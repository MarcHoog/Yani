"""Collects everything the AI reviewers need about a pull request, as one JSON object.

Resolves head/base branches, fetches both, computes the merge base and PR head, lists the
changed files, and checks whether the PR already carries AI review comments (which makes
this a re-review that needs merge_pr_review_comments.py afterwards).

Usage: python3 get_pr_review_context.py --pr <number>
"""

import argparse
import sys

from github_common import (
    GitHubError,
    api,
    get_ai_review_comments,
    main_repo_root,
    print_json,
    repo_path,
    run_git,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pr", type=int, required=True, help="GitHub pull request number")
    args = parser.parse_args()

    repo_root = main_repo_root()

    pr = api("GET", repo_path(f"/pulls/{args.pr}"))
    if not pr["head"]["repo"]:
        raise GitHubError(
            f"PR #{args.pr} head repository no longer exists (deleted fork or repo) - nothing to review."
        )
    if pr["head"]["repo"]["full_name"] != pr["base"]["repo"]["full_name"]:
        raise GitHubError(
            f"PR #{args.pr} comes from a fork ({pr['head']['repo']['full_name']}) - "
            "fork PRs are not supported by this review flow."
        )
    source = pr["head"]["ref"]
    target = pr["base"]["ref"]

    run_git("-C", str(repo_root), "fetch", "--quiet", "origin", source, target)

    merge_base = run_git("-C", str(repo_root), "merge-base", f"origin/{target}", f"origin/{source}")
    if not merge_base:
        raise GitHubError(f"No merge base between origin/{target} and origin/{source}.")
    head = run_git("-C", str(repo_root), "rev-parse", f"origin/{source}")
    if head != pr["head"]["sha"]:
        raise GitHubError(
            f"origin/{source} is at {head} but GitHub reports PR head {pr['head']['sha']} - "
            "fetch race, re-run."
        )
    files = run_git("-C", str(repo_root), "diff", "--name-only", merge_base, f"origin/{source}")
    stat = run_git("-C", str(repo_root), "diff", "--shortstat", merge_base, f"origin/{source}")

    ai_comments = get_ai_review_comments(args.pr)

    print_json(
        {
            "prNumber": args.pr,
            "title": pr["title"],
            "state": pr["state"],
            "draft": pr["draft"],
            "url": pr["html_url"],
            "source": source,
            "target": target,
            "mergeBase": merge_base,
            "head": head,
            "headShort": head[:7],
            "shortStat": stat,
            "changedFiles": files.splitlines() if files else [],
            "hasPriorAiComment": len(ai_comments) > 0,
            "aiComments": [
                {"id": c["id"], "model": c["model"], "url": c["html_url"]} for c in ai_comments
            ],
            "repoRoot": str(repo_root),
        }
    )


if __name__ == "__main__":
    try:
        main()
    except GitHubError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)
