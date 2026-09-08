#!/usr/bin/env python3
"""Repo helper script: dev.py [up|down|logs|test|seed] [extra args...]"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
COMPOSE = ROOT / "compose.yaml"
COMMANDS = ("up", "down", "logs", "test", "seed")


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
        return run([*compose, "up", "-d", "--build", *rest])
    if command == "down":
        return run([*compose, "down", *rest])
    if command == "logs":
        return run([*compose, "logs", "-f", *rest])
    if command == "test":
        return run(["uv", "run", "pytest", *rest], cwd=ROOT / "ssot-api")
    print("No seeder yet.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
