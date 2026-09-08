"""Reads every kind of feedback on a pull request, as one JSON object.

Three sources, all fetched:
  - conversation comments (issue comments) - includes the AI review comments, flagged
  - reviews (approve / request changes / comment verdicts with their summary body)
  - inline review comments, grouped into threads by their reply chain, with file and line

Usage: python3 get_pr_comments.py --pr <number> [--since 2026-01-31T00:00:00Z] [--no-ai]
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "github-pr-review" / "scripts"))

from github_common import (  # noqa: E402
    AI_REVIEW_HEADER_PATTERN,
    GitHubError,
    api,
    paged,
    print_json,
    repo_path,
)


def is_ai_review(body: str) -> bool:
    first = (body or "").split("\n", 1)[0].strip().rstrip("\r")
    return bool(AI_REVIEW_HEADER_PATTERN.match(first))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pr", type=int, required=True, help="GitHub pull request number")
    parser.add_argument("--since", help="only comments created/updated at or after this ISO timestamp")
    parser.add_argument("--no-ai", action="store_true",
                        help="drop the AI review comments (they are read via the review skill)")
    args = parser.parse_args()

    pr = api("GET", repo_path(f"/pulls/{args.pr}"))
    since = f"?since={args.since}" if args.since else ""

    issue_comments = []
    for c in paged(repo_path(f"/issues/{args.pr}/comments{since}")):
        ai = is_ai_review(c.get("body") or "")
        if ai and args.no_ai:
            continue
        issue_comments.append(
            {
                "id": c["id"],
                "author": c["user"]["login"],
                "createdAt": c["created_at"],
                "updatedAt": c["updated_at"],
                "url": c["html_url"],
                "isAiReview": ai,
                "body": c.get("body") or "",
            }
        )

    reviews = [
        {
            "id": r["id"],
            "author": r["user"]["login"] if r.get("user") else None,
            "state": r["state"],  # APPROVED | CHANGES_REQUESTED | COMMENTED | DISMISSED | PENDING
            "submittedAt": r.get("submitted_at"),
            "commit": (r.get("commit_id") or "")[:7],
            "url": r["html_url"],
            "body": r.get("body") or "",
        }
        for r in paged(repo_path(f"/pulls/{args.pr}/reviews"))
        if r["state"] != "PENDING"  # unsubmitted drafts are visible only to their author
    ]

    # Inline comments, grouped into threads: a comment with in_reply_to_id belongs to the
    # thread rooted at that id. REST carries no resolved flag (GraphQL only) - every thread
    # that still exists is listed.
    inline = sorted(paged(repo_path(f"/pulls/{args.pr}/comments{since}")), key=lambda c: c["id"])
    threads: dict[int, dict] = {}
    for c in inline:
        entry = {
            "id": c["id"],
            "author": c["user"]["login"],
            "createdAt": c["created_at"],
            "url": c["html_url"],
            "body": c.get("body") or "",
        }
        root_id = c.get("in_reply_to_id")
        if root_id and root_id in threads:
            threads[root_id]["comments"].append(entry)
        else:
            threads[c["id"]] = {
                "path": c.get("path"),
                "line": c.get("line") or c.get("original_line"),
                "outdated": c.get("line") is None,  # position lost after a newer push
                "diffHunk": c.get("diff_hunk"),
                "comments": [entry],
            }

    print_json(
        {
            "prNumber": args.pr,
            "title": pr["title"],
            "state": pr["state"],
            "url": pr["html_url"],
            "head": pr["head"]["sha"][:7],
            "issueComments": issue_comments,
            "reviews": reviews,
            "inlineThreads": list(threads.values()),
        }
    )


if __name__ == "__main__":
    try:
        main()
    except GitHubError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)
