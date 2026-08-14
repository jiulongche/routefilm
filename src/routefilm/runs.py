"""Immutable render runs, atomic publication, and comparison helpers."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw

from .config import ProjectConfig


@dataclass(frozen=True)
class RunContext:
    run_id: str
    root: Path
    path: Path
    manifest: Path

    @property
    def output_dir(self) -> Path:
        return self.path / "output"

    @property
    def qa_dir(self) -> Path:
        return self.path / "qa"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def versioned_path(path: Path) -> Path:
    """Return the requested path or a timestamped sibling when it already exists."""
    if not path.exists() and not path.is_symlink():
        return path
    timestamp = datetime.now().astimezone().strftime("%Y%m%d-%H%M%S")
    candidate = path.with_name(f"{path.stem}-{timestamp}{path.suffix}")
    suffix = 2
    while candidate.exists() or candidate.is_symlink():
        candidate = path.with_name(f"{path.stem}-{timestamp}-{suffix:02d}{path.suffix}")
        suffix += 1
    return candidate


def _atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.partial")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    os.replace(temporary, path)


def _git_commit() -> str | None:
    root = Path(__file__).resolve().parents[2]
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None
    return result.stdout.strip() or None


def _asset_records(config: ProjectConfig) -> list[dict[str, Any]]:
    paths: list[tuple[str, Path]] = []
    for stop in config.stops:
        if stop.landmark_asset:
            paths.append((f"landmark:{stop.name}", stop.landmark_asset))
    if config.video.vehicle_asset:
        paths.append(("vehicle", config.video.vehicle_asset))
    if config.video.ferry_asset:
        paths.append(("ferry", config.video.ferry_asset))
    return [
        {
            "kind": kind,
            "path": str(path),
            "sha256": _sha256(path),
            "bytes": path.stat().st_size,
        }
        for kind, path in paths
        if path.is_file()
    ]


def begin_run(config: ProjectConfig, action: str, requested_output: Path) -> RunContext:
    workspace = config.source_path.parent if config.source_path else requested_output.parent.parent
    root = workspace / "runs"
    root.mkdir(parents=True, exist_ok=True)
    source_bytes = config.source_path.read_bytes() if config.source_path else repr(config).encode()
    config_hash = hashlib.sha256(source_bytes).hexdigest()
    slug_source = config.source_path.stem if config.source_path else config.video.title
    slug = re.sub(r"[^\w.-]+", "-", slug_source, flags=re.UNICODE).strip("-") or "route"
    timestamp = datetime.now().astimezone().strftime("%Y%m%d-%H%M%S")
    base_id = f"{timestamp}-{slug}-{config_hash[:8]}"
    run_id = base_id
    suffix = 2
    while (root / run_id).exists():
        run_id = f"{base_id}-{suffix:02d}"
        suffix += 1
    run_path = root / run_id
    for relative in (
        "output",
        "qa",
        "previews",
        "prompts",
        "assets/raw",
        "assets/cutout",
        "assets/final",
        "previous",
    ):
        (run_path / relative).mkdir(parents=True, exist_ok=False)
    if config.source_path:
        shutil.copy2(config.source_path, run_path / "config.yaml")

    previous: dict[str, Any] | None = None
    if requested_output.is_symlink():
        previous = {"type": "symlink", "target": os.readlink(requested_output)}
    elif requested_output.is_file():
        archived = run_path / "previous" / requested_output.name
        try:
            os.link(requested_output, archived)
            method = "hardlink"
        except OSError:
            shutil.copy2(requested_output, archived)
            method = "copy"
        previous = {
            "type": method,
            "path": str(archived.relative_to(run_path)),
            "sha256": _sha256(archived),
        }

    manifest = run_path / "manifest.json"
    _atomic_json(
        manifest,
        {
            "schema_version": 1,
            "run_id": run_id,
            "status": "running",
            "action": action,
            "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
            "title": config.video.title,
            "project": str(config.source_path) if config.source_path else None,
            "config_sha256": config_hash,
            "git_commit": _git_commit(),
            "route": [stop.name for stop in config.stops],
            "requested_output": str(requested_output),
            "previous_output": previous,
            "assets": _asset_records(config),
        },
    )
    return RunContext(run_id, root, run_path, manifest)


def _publish_pointer(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(f".{destination.name}.partial")
    if temporary.exists() or temporary.is_symlink():
        temporary.unlink()
    try:
        relative = os.path.relpath(source, destination.parent)
        temporary.symlink_to(relative)
    except OSError:
        shutil.copy2(source, temporary)
    os.replace(temporary, destination)


def complete_run(
    run: RunContext,
    artifact: Path,
    requested_output: Path,
    *,
    qa_report: dict[str, Any] | None = None,
) -> Path:
    payload = json.loads(run.manifest.read_text(encoding="utf-8"))
    payload.update(
        {
            "status": "complete",
            "completed_at": datetime.now().astimezone().isoformat(timespec="seconds"),
            "artifact": {
                "path": str(artifact.relative_to(run.path)),
                "sha256": _sha256(artifact),
                "bytes": artifact.stat().st_size,
            },
        }
    )
    if qa_report is not None:
        report = run.qa_dir / "report.json"
        _atomic_json(report, qa_report)
        payload["qa"] = str(report.relative_to(run.path))
    _atomic_json(run.manifest, payload)
    _publish_pointer(artifact, requested_output)
    _atomic_json(
        run.root / "latest.json",
        {
            "run_id": run.run_id,
            "run_path": str(run.path),
            "artifact": str(artifact),
            "published_output": str(requested_output),
        },
    )
    return requested_output


def fail_run(run: RunContext, error: Exception) -> None:
    payload = json.loads(run.manifest.read_text(encoding="utf-8"))
    payload.update(
        {
            "status": "failed",
            "completed_at": datetime.now().astimezone().isoformat(timespec="seconds"),
            "error": f"{type(error).__name__}: {error}",
        }
    )
    _atomic_json(run.manifest, payload)


def list_runs(workspace: Path) -> list[dict[str, Any]]:
    root = workspace / "runs"
    result: list[dict[str, Any]] = []
    if not root.is_dir():
        return result
    for manifest in sorted(root.glob("*/manifest.json"), reverse=True):
        try:
            result.append(json.loads(manifest.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, OSError):
            continue
    return result


def _comparison_frame(run_path: Path, manifest: dict[str, Any], temporary: Path) -> Image.Image:
    for pattern in ("previews/*", "output/*.jpg", "output/*.png"):
        candidate = next(run_path.glob(pattern), None)
        if candidate:
            return Image.open(candidate).convert("RGB")
    artifact = manifest.get("artifact", {}).get("path")
    if not artifact:
        raise ValueError(f"run has no comparable artifact: {run_path.name}")
    video = run_path / artifact
    frame = temporary / f"{run_path.name}.jpg"
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-ss", "1", "-i", str(video), "-frames:v", "1", str(frame)],
        check=True,
    )
    return Image.open(frame).convert("RGB")


def compare_runs(workspace: Path, run_ids: list[str], output: Path) -> Path:
    if len(run_ids) < 2:
        raise ValueError("compare needs at least two run IDs")
    cards: list[tuple[str, Image.Image]] = []
    with tempfile.TemporaryDirectory(prefix="routefilm-compare-") as temporary:
        temp_path = Path(temporary)
        for run_id in run_ids:
            run_path = workspace / "runs" / run_id
            manifest_path = run_path / "manifest.json"
            if not manifest_path.is_file():
                raise FileNotFoundError(manifest_path)
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            cards.append((run_id, _comparison_frame(run_path, manifest, temp_path)))
    thumb_w, thumb_h = 360, 640
    canvas = Image.new("RGB", (thumb_w * len(cards), thumb_h + 44), (18, 24, 28))
    draw = ImageDraw.Draw(canvas)
    for index, (run_id, image) in enumerate(cards):
        image.thumbnail((thumb_w, thumb_h), Image.Resampling.LANCZOS)
        left = index * thumb_w + (thumb_w - image.width) // 2
        canvas.paste(image, (left, 0))
        draw.text((index * thumb_w + 10, thumb_h + 12), run_id, fill=(255, 249, 232))
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary_output = output.with_name(f".{output.stem}.partial{output.suffix}")
    canvas.save(temporary_output, quality=94)
    os.replace(temporary_output, output)
    return output
