#!/usr/bin/env python3
"""Bootstraps yani's Zitadel for dev. Run through `python dev.py seed`. Idempotent.

Creates (or finds):
- operator organization: `yani-operators`, made by Zitadel's first-instance setup
- project `yani` in the operator org, roles `operator` and `customer`, role assertion on
- OIDC app `portal` (PKCE, JWT access tokens with roles) for the operator console, redirect
  URIs for the container (8080) and the vite dev server (5174)
- one test customer organization, granted the project with role `customer` only
- an operator user (role operator) and a customer user (role customer), fixed dev passwords

Then writes AUTH_AUDIENCE (the project ID), AUTH_OPERATOR_ORG (the operator organization ID) and
PORTAL_CLIENT_ID to .env and prints the test credentials.

Talks to Zitadel's v1 management/admin REST API with the bootstrap service user's token, which
first-instance setup writes to .zitadel/bootstrap.pat. Stdlib only.
"""

import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
PAT_FILE = ROOT / ".zitadel" / "bootstrap.pat"
ENV_FILE = ROOT / ".env"

# The container listens on localhost:8081; Zitadel picks the instance by host name, so every
# call names the instance domain explicitly.
BASE_URL = os.environ.get("ZITADEL_URL", "http://localhost:8081")
INSTANCE_HOST = "zitadel.localhost:8081"
ISSUER = f"http://{INSTANCE_HOST}"

PROJECT = "yani"
ROLES = {"operator": "Operator", "customer": "Customer"}
PORTAL_APP = "portal"
# The container (nginx) and the vite dev server.
PORTAL_URLS = ("http://localhost:8080", "http://localhost:5174")
CUSTOMER_ORG = "Contoso (test customer)"
PASSWORD = os.environ.get("YANI_SEED_PASSWORD", "Yani-dev-pass-1!")
ADMIN_PASSWORD = os.environ.get("ZITADEL_ADMIN_PASSWORD", "Yani-dev-admin-1!")

EQUALS = "TEXT_QUERY_METHOD_EQUALS"


class ZitadelError(Exception):
    pass


class Zitadel:
    def __init__(self, token: str) -> None:
        self._token = token

    def call(
        self, method: str, path: str, body: dict[str, Any] | None = None, org: str | None = None
    ) -> dict[str, Any]:
        headers = {
            "Host": INSTANCE_HOST,
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if org:
            headers["x-zitadel-orgid"] = org
        data = json.dumps(body).encode() if body is not None else None
        request = urllib.request.Request(BASE_URL + path, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                raw = response.read()
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode(errors="replace")
            raise ZitadelError(f"{method} {path} -> {exc.code}: {detail}") from exc
        return json.loads(raw) if raw else {}

    def search(
        self, path: str, queries: list[dict[str, Any]], org: str | None = None
    ) -> list[dict[str, Any]]:
        return self.call("POST", path, {"queries": queries}, org).get("result", [])


def wait_until_ready(timeout: float = 180) -> str:
    """Waits for Zitadel and the bootstrap token written by first-instance setup."""
    deadline = time.monotonic() + timeout
    last = "not started"
    while time.monotonic() < deadline:
        try:
            request = urllib.request.Request(
                BASE_URL + "/debug/ready", headers={"Host": INSTANCE_HOST}
            )
            with urllib.request.urlopen(request, timeout=5):
                pass
            if PAT_FILE.exists() and PAT_FILE.read_text().strip():
                return PAT_FILE.read_text().strip()
            last = f"{PAT_FILE} not written yet"
        except PermissionError as exc:
            raise ZitadelError(
                f"Cannot read {PAT_FILE} ({exc}). Zitadel wrote it as another user: start the "
                "stack with `python dev.py up` (it runs Zitadel as you), or fix the file owner."
            ) from exc
        except (urllib.error.URLError, OSError) as exc:
            last = str(exc)
        time.sleep(2)
    raise ZitadelError(
        f"Zitadel not ready at {BASE_URL} after {timeout:.0f}s ({last}). "
        "Is `python dev.py up` running (plain `docker compose up` may leave .zitadel/ unwritable "
        "for Zitadel)? The token is only written on the very first start; if .zitadel/ was "
        "cleared, reset with `python dev.py down -v`."
    )


def ensure_project(z: Zitadel) -> str:
    found = z.search(
        "/management/v1/projects/_search", [{"nameQuery": {"name": PROJECT, "method": EQUALS}}]
    )
    if found:
        project_id = found[0]["id"]
    else:
        project_id = z.call(
            "POST",
            "/management/v1/projects",
            {
                "name": PROJECT,
                # Put the user's roles into tokens, and only let users with a role sign in.
                "projectRoleAssertion": True,
                "projectRoleCheck": True,
            },
        )["id"]
    existing = {
        r["key"] for r in z.search(f"/management/v1/projects/{project_id}/roles/_search", [])
    }
    for key, name in ROLES.items():
        if key not in existing:
            z.call(
                "POST",
                f"/management/v1/projects/{project_id}/roles",
                {"roleKey": key, "displayName": name},
            )
    return project_id


def portal_oidc_config() -> dict[str, Any]:
    return {
        "redirectUris": [f"{url}/auth/callback" for url in PORTAL_URLS],
        "postLogoutRedirectUris": [f"{url}/" for url in PORTAL_URLS],
        "responseTypes": ["OIDC_RESPONSE_TYPE_CODE"],
        "grantTypes": ["OIDC_GRANT_TYPE_AUTHORIZATION_CODE", "OIDC_GRANT_TYPE_REFRESH_TOKEN"],
        "appType": "OIDC_APP_TYPE_USER_AGENT",
        "authMethodType": "OIDC_AUTH_METHOD_TYPE_NONE",
        "accessTokenType": "OIDC_TOKEN_TYPE_JWT",
        "accessTokenRoleAssertion": True,
        "idTokenRoleAssertion": True,
        # http redirect URIs are only allowed in dev mode.
        "devMode": True,
    }


def ensure_portal_app(z: Zitadel, project_id: str) -> str:
    """Creates the portal app, or brings the redirect URIs of an existing one up to date."""
    config = portal_oidc_config()
    found = z.search(
        f"/management/v1/projects/{project_id}/apps/_search",
        [{"nameQuery": {"name": PORTAL_APP, "method": EQUALS}}],
    )
    if not found:
        app = z.call(
            "POST",
            f"/management/v1/projects/{project_id}/apps/oidc",
            {"name": PORTAL_APP, **config},
        )
        return app["clientId"]
    current = found[0]["oidcConfig"]
    stale = any(
        sorted(current.get(key, [])) != sorted(config[key])
        for key in ("redirectUris", "postLogoutRedirectUris")
    )
    if stale:
        z.call(
            "PUT",
            f"/management/v1/projects/{project_id}/apps/{found[0]['id']}/oidc_config",
            config,
        )
    return current["clientId"]


def ensure_customer_org(z: Zitadel) -> str:
    found = z.search(
        "/admin/v1/orgs/_search", [{"nameQuery": {"name": CUSTOMER_ORG, "method": EQUALS}}]
    )
    if found:
        return found[0]["id"]
    return z.call("POST", "/management/v1/orgs", {"name": CUSTOMER_ORG})["id"]


def ensure_project_grant(z: Zitadel, project_id: str, org_id: str) -> str:
    """Grants the project to a customer org with the `customer` role only."""
    for grant in z.search(f"/management/v1/projects/{project_id}/grants/_search", []):
        if grant.get("grantedOrgId") == org_id:
            return grant["grantId"]
    grant = z.call(
        "POST",
        f"/management/v1/projects/{project_id}/grants",
        {"grantedOrgId": org_id, "roleKeys": ["customer"]},
    )
    return grant["grantId"]


def ensure_user(z: Zitadel, org_id: str, username: str, first: str, last: str) -> tuple[str, str]:
    """Human user with a fixed dev password (reset on every run). Returns (id, login name)."""
    found = z.search(
        "/management/v1/users/_search",
        [{"userNameQuery": {"userName": username, "method": EQUALS}}],
        org=org_id,
    )
    if found:
        user_id = found[0]["id"]
        z.call(
            "POST",
            f"/management/v1/users/{user_id}/password",
            {"password": PASSWORD, "noChangeRequired": True},
            org=org_id,
        )
    else:
        user_id = z.call(
            "POST",
            "/management/v1/users/human/_import",
            {
                "userName": username,
                "profile": {"firstName": first, "lastName": last, "displayName": f"{first} {last}"},
                "email": {"email": f"{username}@yani.test", "isEmailVerified": True},
                "password": PASSWORD,
                "passwordChangeRequired": False,
            },
            org=org_id,
        )["userId"]
    user = z.call("GET", f"/management/v1/users/{user_id}", org=org_id)["user"]
    return user_id, user.get("preferredLoginName", username)


def ensure_user_grant(
    z: Zitadel,
    org_id: str,
    user_id: str,
    project_id: str,
    role: str,
    project_grant_id: str | None = None,
) -> None:
    grants = z.search(
        "/management/v1/users/grants/_search",
        [{"userIdQuery": {"userId": user_id}}, {"projectIdQuery": {"projectId": project_id}}],
        org=org_id,
    )
    if grants:
        return
    body: dict[str, Any] = {"projectId": project_id, "roleKeys": [role]}
    if project_grant_id:
        body["projectGrantId"] = project_grant_id
    z.call("POST", f"/management/v1/users/{user_id}/grants", body, org=org_id)


def write_env(key: str, value: str) -> None:
    lines = ENV_FILE.read_text().splitlines() if ENV_FILE.exists() else []
    lines = [line for line in lines if not line.startswith(f"{key}=")]
    lines.append(f"{key}={value}")
    ENV_FILE.write_text("\n".join(lines) + "\n")


def main() -> int:
    try:
        z = Zitadel(wait_until_ready())
        operator_org = z.call("GET", "/management/v1/orgs/me")["org"]["id"]
        project_id = ensure_project(z)
        client_id = ensure_portal_app(z, project_id)
        customer_org = ensure_customer_org(z)
        grant_id = ensure_project_grant(z, project_id, customer_org)
        op_id, op_login = ensure_user(z, operator_org, "operator", "Olivia", "Operator")
        ensure_user_grant(z, operator_org, op_id, project_id, "operator")
        cu_id, cu_login = ensure_user(z, customer_org, "customer", "Chris", "Customer")
        ensure_user_grant(z, customer_org, cu_id, project_id, "customer", grant_id)
    except ZitadelError as exc:
        print(f"seed failed: {exc}", file=sys.stderr)
        return 1

    write_env("AUTH_AUDIENCE", project_id)
    write_env("AUTH_OPERATOR_ORG", operator_org)
    write_env("PORTAL_CLIENT_ID", client_id)
    print(
        f"""
Zitadel seeded.

  console          {ISSUER}/ui/console
  issuer           {ISSUER}
  project (aud)    {project_id}   -> written to .env as AUTH_AUDIENCE
  portal client id {client_id}   -> written to .env as PORTAL_CLIENT_ID
  operator org     {operator_org}   -> written to .env as AUTH_OPERATOR_ORG
  customer org     {customer_org}   = customer_id of the test customer

  admin            admin@yani-operators.zitadel.localhost / {ADMIN_PASSWORD}  (Zitadel admin)
  operator         {op_login} / {PASSWORD}  (role operator)
  customer         {cu_login} / {PASSWORD}  (role customer)

Dev passwords. MFA can be enabled per user in the Zitadel account page.
"""
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
