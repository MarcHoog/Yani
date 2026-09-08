"""Authenticated GitHub REST calls from the shell - the CLI face of github_common.py.

Path forms:
  pulls?state=open          repo-relative: prefixed with /repos/<owner>/<repo>/
  /repos/x/y/pulls          absolute API path, used as-is
  https://api.github.com/…  full URL (api.github.com only; the token never leaves it)

Body (POST/PATCH/PUT): --body-file <json file> is the safe default - PR bodies quote code and
shell strings mangle it. --body '<json>' works for trivial payloads.

Usage:
  python3 gh_api.py GET pulls?state=open
  python3 gh_api.py GET pulls --paginate
  python3 gh_api.py POST pulls --body-file pr.json
  python3 gh_api.py PATCH pulls/12 --body-file body.json
  python3 gh_api.py GET actions/jobs/123/logs --download job-log.txt

Prints the JSON response (pretty), nothing on 204.
"""

import argparse
import json
import sys

from github_common import GitHubError, api, download, paged, print_json, repo_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("method", choices=["GET", "POST", "PATCH", "PUT", "DELETE"])
    parser.add_argument("path", help="repo-relative path, absolute API path, or full URL")
    parser.add_argument("--body", help="inline JSON body")
    parser.add_argument("--body-file", help="file containing the JSON body")
    parser.add_argument("--paginate", action="store_true",
                        help="GET all pages of a list endpoint (per_page=100)")
    parser.add_argument("--download", metavar="FILE",
                        help="save the raw response to FILE (follows GitHub's signed redirect "
                             "without the auth header); for logs and archives")
    args = parser.parse_args()

    path = args.path
    if not path.startswith(("/", "http://", "https://")):
        path = repo_path("/" + path)

    if args.download:
        if args.method != "GET":
            raise GitHubError("--download only supports GET.")
        download(path, args.download)
        print_json({"saved": args.download})
        return

    body = None
    if args.body_file:
        with open(args.body_file, encoding="utf-8") as f:
            body = json.load(f)
    elif args.body:
        body = json.loads(args.body)

    if args.paginate:
        if args.method != "GET":
            raise GitHubError("--paginate only supports GET.")
        print_json(paged(path))
        return

    result = api(args.method, path, body)
    if result is not None:
        print_json(result)


if __name__ == "__main__":
    try:
        main()
    except GitHubError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)
