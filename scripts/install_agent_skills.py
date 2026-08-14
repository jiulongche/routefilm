#!/usr/bin/env python3
"""Install the canonical RouteFilm Skill for Codex, Claude Code, or both."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


def install(source: Path, destination: Path, force: bool) -> None:
    if destination.exists() or destination.is_symlink():
        if not force:
            raise FileExistsError(f"already exists: {destination}; pass --force to replace")
        if destination.is_dir() and not destination.is_symlink():
            shutil.rmtree(destination)
        else:
            destination.unlink()
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, destination)
    print(destination)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--agent", choices=["codex", "claude", "both"], default="both")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    source = root / "skills" / "build-route-map-video"
    destinations = []
    if args.agent in {"codex", "both"}:
        destinations.append(Path.home() / ".agents" / "skills" / source.name)
    if args.agent in {"claude", "both"}:
        destinations.append(Path.home() / ".claude" / "skills" / source.name)
    for destination in destinations:
        install(source, destination, args.force)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
