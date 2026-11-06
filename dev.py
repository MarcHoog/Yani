#!/usr/bin/env python3
"""Repo helper script: dev.py [up|down|logs|test|seed] [extra args...]"""

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
COMPOSE = ROOT / "compose.yaml"
# Zitadel's first start writes the bootstrap service user's token here (bind mount).
ZITADEL_BOOTSTRAP = ROOT / ".zitadel"
COMMANDS = ("up", "down", "logs", "test", "seed")
PACKAGES = ("shared", "ssot-api", "todo-api")
# Isolation tests run against real databases. They use unique customer ids and clean up after
# themselves, so the dev databases are fine. Set these yourself to point at other databases.
TEST_DB_ENV = {
    "TEST_DATABASE_URL": "postgresql://yani:{pg}@localhost:5432/yani",
    "TEST_NEO4J_URI": "bolt://localhost:7687",
    "TEST_NEO4J_USER": "neo4j",
    "TEST_NEO4J_PASSWORD": "{neo}",
}


def run(cmd: list[str], cwd: Path = ROOT) -> int:
    try:
        return subprocess.run(cmd, cwd=cwd).returncode
    except KeyboardInterrupt:
        return 130


def main() -> int:
    args = sys.argv[1:]
    command = args[0] if args else "up"
    rest = args[1:]

    if command not in COMMANDS:
        expected = ", ".join(COMMANDS)
        print(f"Unknown command '{command}'. Expected one of: {expected}", file=sys.stderr)
        return 2

    compose = ["docker", "compose", "-f", str(COMPOSE)]
    if command == "up":
        ZITADEL_BOOTSTRAP.mkdir(exist_ok=True)
        if hasattr(os, "getuid"):
            # Zitadel runs as this user so it can write the token into the bind mount.
            os.environ.setdefault("UID", str(os.getuid()))
        return run([*compose, "up", "-d", "--build", *rest])
    if command == "down":
        if "-v" in rest or "--volumes" in rest:
            # A fresh Zitadel writes a fresh token; the old one would only confuse seed.
            (ZITADEL_BOOTSTRAP / "bootstrap.pat").unlink(missing_ok=True)
        return run([*compose, "down", *rest])
    if command == "logs":
        return run([*compose, "logs", "-f", *rest])
    if command == "test":
        if not (os.environ.get("TEST_DATABASE_URL") and os.environ.get("TEST_NEO4J_URI")):
            code = run([*compose, "up", "-d", "--wait", "postgres", "neo4j"])
            if code != 0:
                return code
            secrets = {
                "pg": os.environ.get("POSTGRES_PASSWORD", "yani-dev"),
                "neo": os.environ.get("NEO4J_PASSWORD", "yani-dev"),
            }
            for key, value in TEST_DB_ENV.items():
                os.environ.setdefault(key, value.format(**secrets))
        for package in PACKAGES:
            code = run(["uv", "run", "pytest", *rest], cwd=ROOT / package)
            if code != 0:
                return code
        return 0
    # seed: bootstrap Zitadel (orgs, project, app, test users), then restart the APIs and the
    # portal so they pick up AUTH_AUDIENCE, AUTH_OPERATOR_ORG and PORTAL_CLIENT_ID from .env.
    code = run([sys.executable, str(ROOT / "seed_zitadel.py"), *rest])
    if code != 0:
        return code
    return run([*compose, "up", "-d", "ssot-api", "todo-api", "portal"])


if __name__ == "__main__":
    sys.exit(main())
