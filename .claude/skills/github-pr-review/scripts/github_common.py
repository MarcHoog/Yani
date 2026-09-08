"""Shared helpers for the GitHub skills. Import, do not run.

Repo coordinates (derived from the origin remote), authenticated GitHub REST wrapper, and
AI-review comment discovery for pull requests. Auth uses the token git's credential helper
already caches for github.com (the same one that lets you push). No gh CLI required.
Stdlib only - runs on any platform with Python 3.10+.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

API_BASE = "https://api.github.com"
API_VERSION = "2022-11-28"
COMMENT_MAX_LENGTH = 65536
AI_REVIEW_HEADER_PATTERN = re.compile(r"^## AI review - (sonnet|opus)\b")
AI_REVIEW_HEAD_PATTERN = re.compile(r"<!-- ai-review head:([0-9a-f]{7,40}) -->")

_owner: str | None = None
_repo: str | None = None
_headers: dict[str, str] | None = None
_login: str | None = None


class GitHubError(RuntimeError):
    """Raised for any GitHub REST or git failure. Message is user-facing."""


def run_git(*args: str, cwd: str | Path | None = None) -> str:
    """Run git, return stripped stdout. Raises GitHubError on non-zero exit."""
    result = subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, encoding="utf-8"
    )
    if result.returncode != 0:
        raise GitHubError(
            f"git {' '.join(args)} failed ({result.returncode}): {result.stderr.strip()}"
        )
    return result.stdout.strip()


def main_repo_root() -> Path:
    """Root of the primary checkout, even when invoked from inside a linked worktree."""
    script_dir = Path(__file__).resolve().parent
    common = run_git(
        "-C", str(script_dir), "rev-parse", "--path-format=absolute", "--git-common-dir"
    )
    if not common:
        raise GitHubError("Not inside a git repository.")
    return Path(common).parent.resolve()


def _init_repo() -> None:
    """Fills owner/repo from the origin remote once. Accepts https and ssh remotes."""
    global _owner, _repo
    if _owner:
        return
    remote = run_git("-C", str(main_repo_root()), "remote", "get-url", "origin")
    m = re.search(r"github\.com[:/](?P<owner>[^/]+)/(?P<repo>[^/]+?)(\.git)?/?$", remote)
    if not m:
        raise GitHubError(f"origin remote is not a GitHub URL: {remote}")
    _owner = m.group("owner")
    _repo = m.group("repo")


def repo_path(path: str = "") -> str:
    """'/repos/<owner>/<repo>' plus path (starts with '/' or is empty)."""
    _init_repo()
    return f"/repos/{_owner}/{_repo}{path}"


def get_headers() -> dict[str, str]:
    """Returns a copy of the cached auth headers. Token comes from the git credential helper."""
    global _headers
    if _headers:
        return dict(_headers)

    # interactive=never: a cache miss must fail fast, not open a credential prompt.
    result = subprocess.run(
        ["git", "-c", "credential.interactive=never", "credential", "fill"],
        input="protocol=https\nhost=github.com\n\n",
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    token = ""
    for line in result.stdout.splitlines():
        if line.startswith("password="):
            token = line[len("password=") :]
            break
    if not token:
        raise GitHubError(
            "No GitHub credential: git credential helper returned no token for github.com. "
            "Push once over https to cache one."
        )

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": API_VERSION,
        "User-Agent": "yani-pr-review",
    }
    status, _ = _request("GET", API_BASE + repo_path(), headers)
    if status != 200:
        raise GitHubError(f"GitHub REST rejected the git-cached token ({status}) for {repo_path()}.")
    _headers = headers
    return dict(headers)


def _request(
    method: str, url: str, headers: dict[str, str], body: bytes | None = None
) -> tuple[int, bytes]:
    """One HTTP round trip, no exceptions on HTTP error status."""
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


def api(method: str, uri: str, body: object | None = None):
    """Authenticated REST call. uri may be a path ('/repos/...') or a full URL. body is
    JSON-encoded. JSON replies are parsed; empty replies (204) return None. Non-2xx raises
    GitHubError with the GitHub message and status code in the text."""
    if method not in ("GET", "POST", "PATCH", "PUT", "DELETE"):
        raise GitHubError(f"Unsupported method {method}.")
    if not re.match(r"^https?://", uri):
        uri = API_BASE + uri
    # The bearer token pushes to the repo; never let a URL taken from payload data carry it elsewhere.
    host = urllib.parse.urlparse(uri).hostname
    if host != urllib.parse.urlparse(API_BASE).hostname:
        raise GitHubError(f"Refusing to send GitHub credentials to host '{host}' ({uri}).")
    headers = get_headers()
    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    status, content = _request(method, uri, headers, data)
    if status >= 400:
        try:
            msg = json.loads(content).get("message", content.decode("utf-8", "replace"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            msg = content.decode("utf-8", "replace")
        raise GitHubError(f"GitHub {status} for {method} {uri} : {msg}")
    if not content:
        return None
    return json.loads(content)


def download(uri: str, out_file: str | Path) -> None:
    """GET a raw endpoint (e.g. Actions job logs) to a file. GitHub replies 302 to a signed
    URL; the redirect is followed WITHOUT the auth header so the token never leaves
    api.github.com."""
    if not re.match(r"^https?://", uri):
        uri = API_BASE + uri
    host = urllib.parse.urlparse(uri).hostname
    if host != urllib.parse.urlparse(API_BASE).hostname:
        raise GitHubError(f"Refusing to send GitHub credentials to host '{host}' ({uri}).")

    class _NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None

    opener = urllib.request.build_opener(_NoRedirect)
    req = urllib.request.Request(uri, headers=get_headers(), method="GET")
    try:
        with opener.open(req) as resp:
            status, content, location = resp.status, resp.read(), None
    except urllib.error.HTTPError as e:
        status, content, location = e.code, e.read(), e.headers.get("Location")
    if status in (301, 302, 303, 307, 308) and location:
        with urllib.request.urlopen(
            urllib.request.Request(location, headers={"User-Agent": "yani-pr-review"})
        ) as resp:
            content = resp.read()
    elif status >= 400:
        raise GitHubError(f"GitHub {status} for GET {uri} : {content.decode('utf-8', 'replace')}")
    Path(out_file).write_bytes(content)


def paged(path: str) -> list:
    """GET every page of a list endpoint (per_page=100, follows until a short page)."""
    sep = "&" if "?" in path else "?"
    page = 1
    items: list = []
    while True:
        chunk = api("GET", f"{path}{sep}per_page=100&page={page}")
        items.extend(chunk)
        if len(chunk) < 100:
            return items
        page += 1


def get_login() -> str:
    """Login of the user the cached token belongs to - the author of every AI review comment."""
    global _login
    if not _login:
        _login = api("GET", "/user")["login"]
    return _login


def get_ai_review_comments(pr_number: int) -> list[dict]:
    """Returns the PR's AI review comments: issue comments authored by the token's own user
    whose body starts with '## AI review - <model>', oldest first. Each dict gains a 'model'
    key. A human comment that happens to start with the header is never picked up (it would
    otherwise be merged and deleted)."""
    login = get_login()
    comments = paged(repo_path(f"/issues/{pr_number}/comments"))
    out = []
    for c in sorted(comments, key=lambda c: c["id"]):
        if c["user"]["login"] != login:
            continue
        first = (c.get("body") or "").split("\n", 1)[0].strip().rstrip("\r")
        m = AI_REVIEW_HEADER_PATTERN.match(first)
        if m:
            c["model"] = m.group(1)
            out.append(c)
    return out


def get_review_verdict(markdown: str) -> str:
    """Extracts approve|comment|needs-work from the review header (first 6 lines, so a verdict
    line quoted inside a finding cannot win). Raises when absent, unfilled, or present more
    than once."""
    header = "\n".join(re.split(r"\r?\n", markdown)[:6])
    # Anchored to end of line so the unfilled template "approve | comment | needs-work" fails.
    matches = re.findall(
        r"(?m)^\*\*Verdict:\*\*\s*`?(approve|comment|needs-work)`?\s*$", header
    )
    if len(matches) != 1:
        raise GitHubError(
            "Review header (first 6 lines) must carry exactly one "
            f"'**Verdict:** <approve|comment|needs-work>' line, found {len(matches)}."
        )
    return matches[0]


def get_review_head(markdown: str) -> str | None:
    """Returns the 7-char head sha a review was written against, read from the hidden
    '<!-- ai-review head:<sha> -->' line post_pr_review.py appends. None when absent."""
    m = AI_REVIEW_HEAD_PATTERN.search(markdown)
    return m.group(1)[:7].lower() if m else None


def registered_worktrees(repo_root: str | Path) -> list[str]:
    """Absolute, normalised paths of every worktree git knows about for this repo."""
    lines = run_git("-C", str(repo_root), "worktree", "list", "--porcelain").splitlines()
    return [
        os.path.normpath(line[len("worktree ") :])
        for line in lines
        if line.startswith("worktree ")
    ]


def print_json(obj: object) -> None:
    """Emit one JSON document to stdout, the contract of every script here."""
    print(json.dumps(obj, indent=2))
