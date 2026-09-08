"""Folds this round's AI review comments into the PR's canonical sonnet and opus comments.

A PR keeps exactly one '## AI review - sonnet' and one '## AI review - opus' comment, forever.
Per model, the lowest comment id is canonical; every higher-id AI comment is a duplicate a
reviewer posted. Each duplicate is appended to the canonical comment's body as
'### Round N - head <sha>' (header line and hidden head marker stripped) via PATCH, then the
duplicate is deleted, then verified. The head in the round marker is the one embedded in the
duplicate itself by post_pr_review.py, so a leftover from an older round keeps its own sha;
--head is only the fallback for comments posted without a marker. After each append a
'**Latest:** round N (head <sha>) - <verdict>' line directly under the heading is inserted or
replaced, so the headline never contradicts the newest round. Review wording is never changed.

Always safe to run: a first round with nothing to merge is a reported no-op. Safe to re-run
after a partial failure: a duplicate whose head marker and content already sit in the
canonical body is not appended again, only deleted. Every verdict is validated before the
first write, and a failure mid-way still prints the report of what landed.

Usage: python3 merge_pr_review_comments.py --pr <n> --head <sha>
Prints a JSON report per model: canonical id and url, rounds appended (with head), duplicates
deleted, verification result, this round's verdict, error if the model's merge aborted.
Exit code 1 when any model's merge aborted.
"""

import argparse
import re
import sys

from github_common import (
    AI_REVIEW_HEAD_PATTERN,
    COMMENT_MAX_LENGTH,
    GitHubError,
    api,
    get_ai_review_comments,
    get_review_head,
    get_review_verdict,
    print_json,
    repo_path,
)

ROUND_MARKER_PATTERN = re.compile(r"(?m)^### Round \d+ - head `[0-9a-f]{7}`\s*$")
LATEST_LINE_PATTERN = re.compile(r"(?m)^\*\*Latest:\*\* .*$")


def round_marker(round_no: int, head: str) -> str:
    return f"### Round {round_no} - head `{head}`"


def set_latest_line(body: str, round_no: int, head: str, verdict: str) -> str:
    """Inserts or replaces the '**Latest:**' line directly under the '## AI review' heading."""
    line = f"**Latest:** round {round_no} (head `{head}`) - {verdict}"
    if LATEST_LINE_PATTERN.search(body):
        return LATEST_LINE_PATTERN.sub(line, body, count=1)
    parts = re.split(r"\r?\n", body, maxsplit=1)
    return f"{parts[0]}\n{line}\n{parts[1] if len(parts) > 1 else ''}"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pr", type=int, required=True, help="GitHub pull request number")
    parser.add_argument("--head", required=True,
                        help="PR head for this round; fallback for a duplicate with no embedded marker")
    args = parser.parse_args()

    if not re.fullmatch(r"[0-9a-fA-F]{7,40}", args.head):
        raise GitHubError(f"--head '{args.head}' is not a 7-40 char hex sha.")
    fallback_sha = args.head[:7].lower()
    comments = get_ai_review_comments(args.pr)
    report: dict[str, dict] = {}

    for model in ("sonnet", "opus"):
        group = sorted((c for c in comments if c["model"] == model), key=lambda c: c["id"])
        if not group:
            report[model] = {"canonical": None, "note": "no AI comment for this model"}
            continue

        canonical = group[0]
        dupes = group[1:]
        entry: dict = {
            "canonical": canonical["id"],
            "url": canonical["html_url"],
            "appended": [],
            "deleted": [],
            "verified": True,
            "verdict": None,
            "error": None,
        }
        report[model] = entry  # registered before any write so a failure still reports partial state

        try:
            canon_text = (canonical.get("body") or "").rstrip()
            # Only the exact shape this script emits, so reviewer prose quoting a marker is not counted.
            rounds = len(ROUND_MARKER_PATTERN.findall(canon_text))
            verdict = None

            # Validate every duplicate before touching the PR.
            work = []
            for dupe in dupes:
                content = dupe.get("body") or ""
                head = get_review_head(content) or fallback_sha
                stripped = re.sub(rf"^## AI review - {model}[^\r\n]*\r?\n", "", content)
                stripped = re.sub(
                    rf"(?:\r?\n)*{AI_REVIEW_HEAD_PATTERN.pattern}\s*$", "", stripped
                ).strip()
                work.append(
                    {
                        "dupe": dupe,
                        "head": head,
                        "verdict": get_review_verdict(content),
                        "stripped": stripped,
                    }
                )

            for w in work:
                verdict = w["verdict"]
                already_merged = f"head `{w['head']}`" in canon_text and w["stripped"] in canon_text
                if already_merged:
                    # Same head, same text: an earlier run appended it and failed on the delete.
                    entry["appended"].append(
                        {
                            "round": None,
                            "head": w["head"],
                            "from": w["dupe"]["id"],
                            "note": "already present in canonical comment",
                        }
                    )
                else:
                    round_no = rounds + 2
                    new_body = (
                        f"{canon_text}\n\n{round_marker(round_no, w['head'])}\n\n{w['stripped']}"
                    )
                    new_body = set_latest_line(new_body, round_no, w["head"], w["verdict"])
                    if len(new_body) > COMMENT_MAX_LENGTH:
                        raise GitHubError(
                            f"Canonical comment {canonical['id']} would grow to {len(new_body)} "
                            f"chars (max {COMMENT_MAX_LENGTH}) - duplicate {w['dupe']['id']} "
                            "left in place."
                        )
                    patched = api(
                        "PATCH",
                        repo_path(f"/issues/comments/{canonical['id']}"),
                        {"body": new_body},
                    )
                    # The duplicate is the only surviving copy of this round: delete it only once
                    # the returned body proves the append landed. A concurrent overwrite shows up here.
                    landed = patched.get("body") or ""
                    if not (
                        round_marker(round_no, w["head"]) in landed and w["stripped"] in landed
                    ):
                        raise GitHubError(
                            f"PATCH of canonical comment {canonical['id']} did not return the "
                            f"appended round {round_no} - duplicate {w['dupe']['id']} left in place."
                        )
                    entry["appended"].append(
                        {"round": round_no, "head": w["head"], "from": w["dupe"]["id"]}
                    )
                    canon_text = landed.rstrip()
                    rounds += 1

                api("DELETE", repo_path(f"/issues/comments/{w['dupe']['id']}"))
                entry["deleted"].append(w["dupe"]["id"])

            if verdict:
                entry["verdict"] = verdict
            else:
                entry["note"] = "nothing merged this round"
        except GitHubError as e:
            entry["error"] = str(e)
            entry["verified"] = False

    # Verify: deleted duplicates now 404; canonical body carries every round marker (with its
    # head) appended this run and the Latest line names the newest one. A failure here must not
    # swallow the report of what already landed.
    for model in ("sonnet", "opus"):
        entry = report[model]
        if not entry.get("canonical") or entry.get("error"):
            continue
        try:
            canon = api("GET", repo_path(f"/issues/comments/{entry['canonical']}"))
            body = canon.get("body") or ""
            last = None
            for a in entry["appended"]:
                if not a["round"]:
                    continue
                if round_marker(a["round"], a["head"]) not in body:
                    entry["verified"] = False
                last = a
            if last and f"**Latest:** round {last['round']} (head `{last['head']}`)" not in body:
                entry["verified"] = False
            for comment_id in entry["deleted"]:
                gone = False
                try:
                    api("GET", repo_path(f"/issues/comments/{comment_id}"))
                except GitHubError as e:
                    if "GitHub 404" in str(e):
                        gone = True
                if not gone:
                    entry["verified"] = False
        except GitHubError as e:
            # Per model: a transient failure verifying one must not mark the other unverified.
            entry["verified"] = None
            entry["verifyError"] = str(e)

    print_json(report)
    if any(entry.get("error") for entry in report.values()):
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except GitHubError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)
