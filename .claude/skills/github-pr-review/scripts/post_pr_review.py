"""Posts one AI review as a single top-level PR comment.

Reads the review markdown from --review-file (written with the Write tool, never inline shell
strings - review text quotes code and shells expand), validates the header, verdict and
length, then POSTs one issue comment on the PR. GitHub issue comments carry no status, so the
verdict lives in the text only. The reviewed head sha is appended as a hidden HTML comment so
a later merge can label the round with the head it was actually written against. The review
file is deleted after a successful post, and a file older than an hour is refused, so a later
round cannot post a leftover.

Usage: python3 post_pr_review.py --pr <n> --model <sonnet|opus> --head <sha> --review-file <path>
Prints JSON: prNumber, model, commentId, url, verdict, head.
"""

import argparse
import re
import sys
import time
from pathlib import Path

from github_common import (
    AI_REVIEW_HEAD_PATTERN,
    COMMENT_MAX_LENGTH,
    GitHubError,
    api,
    get_review_verdict,
    print_json,
    repo_path,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pr", type=int, required=True, help="GitHub pull request number")
    parser.add_argument("--model", required=True, choices=["sonnet", "opus"],
                        help="reviewer label; the file's first line must be '## AI review - <model>'")
    parser.add_argument("--head", required=True,
                        help="PR head the review was written against - from the reviewer's prompt")
    parser.add_argument("--review-file", required=True,
                        help="path of the review markdown written by the reviewer")
    args = parser.parse_args()

    if not re.fullmatch(r"[0-9a-fA-F]{7,40}", args.head):
        raise GitHubError(f"--head '{args.head}' is not a 7-40 char hex sha.")
    review_file = Path(args.review_file)
    if not review_file.is_file():
        raise GitHubError(f"Review file not found: {review_file}")
    age_min = (time.time() - review_file.stat().st_mtime) / 60
    if age_min > 60:
        raise GitHubError(
            f"Review file {review_file} was written {int(age_min)} min ago - stale; "
            "write this round's review first."
        )
    markdown = review_file.read_text(encoding="utf-8").rstrip()
    if not markdown:
        raise GitHubError(f"Review file is empty: {review_file}")

    first_line = re.split(r"\r?\n", markdown, maxsplit=1)[0].strip()
    if first_line != f"## AI review - {args.model}":
        raise GitHubError(
            f"First line must be exactly '## AI review - {args.model}', got '{first_line}'."
        )
    verdict = get_review_verdict(markdown)
    if AI_REVIEW_HEAD_PATTERN.search(markdown):
        raise GitHubError(
            "Review file already carries an ai-review head marker - the script adds it, "
            "do not write it yourself."
        )
    short_sha = args.head[:7].lower()
    markdown = f"{markdown}\n\n<!-- ai-review head:{short_sha} -->"
    # Checked after the marker so the length tested is the length posted.
    if len(markdown) > COMMENT_MAX_LENGTH:
        raise GitHubError(
            f"Review is {len(markdown)} chars incl. head marker; GitHub comments max "
            f"{COMMENT_MAX_LENGTH}. Trim the findings."
        )

    comment = api("POST", repo_path(f"/issues/{args.pr}/comments"), {"body": markdown})
    if not comment or not comment.get("id"):
        raise GitHubError("GitHub returned no comment id.")
    review_file.unlink()  # posted; a stale file must not be picked up by a later round

    print_json(
        {
            "prNumber": args.pr,
            "model": args.model,
            "commentId": comment["id"],
            "url": comment["html_url"],
            "verdict": verdict,
            "head": short_sha,
        }
    )


if __name__ == "__main__":
    try:
        main()
    except GitHubError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)
