#!/usr/bin/env python3
"""Generate missing curated landmark presets while retaining every source stage."""

from __future__ import annotations

import argparse
import hashlib
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from PIL import Image

from routefilm.assets import generate_landmark
from routefilm.landmarks import CATALOG_PATH, LANDMARK_DIR


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _audit_assets(catalog: list[dict[str, str]], asset_dir: Path) -> dict[str, object]:
    """Verify every packaged landmark and persist its release identity."""
    missing_assets: list[str] = []
    missing_records: list[str] = []
    audited: list[dict[str, object]] = []
    records_dir = asset_dir / "records"
    for item in catalog:
        asset = asset_dir / item["asset"]
        stem = Path(item["asset"]).stem
        record_path = records_dir / f"{stem}.json"
        if not asset.is_file():
            missing_assets.append(item["city"])
            continue
        if not record_path.is_file():
            missing_records.append(item["city"])
            continue
        with Image.open(asset) as image:
            width, height = image.size
            if image.mode != "RGBA":
                raise RuntimeError(f"{item['city']}: packaged asset must use RGBA")
            alpha = image.getchannel("A")
            if alpha.getbbox() is None or alpha.getextrema() == (255, 255):
                raise RuntimeError(f"{item['city']}: packaged asset has no usable transparency")
        packaged = {
            "sha256": _sha256(asset),
            "bytes": asset.stat().st_size,
            "width": width,
            "height": height,
            "format": "WEBP",
        }
        metadata = json.loads(record_path.read_text(encoding="utf-8"))
        metadata["packaged_asset"] = packaged
        record_path.write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        audited.append({"city": item["city"], "asset": item["asset"], **packaged})
    if missing_assets or missing_records:
        raise RuntimeError(
            "landmark audit failed: "
            f"missing assets={missing_assets}, missing records={missing_records}"
        )
    return {"count": len(audited), "assets": audited}


def _generate(
    record: dict[str, str],
    asset_dir: Path,
    work_dir: Path,
    quality: str,
) -> tuple[str, Path]:
    asset_path = asset_dir / record["asset"]
    if asset_path.is_file():
        return record["city"], asset_path
    stem = Path(record["asset"]).stem
    cutout = work_dir / "cutout" / f"{stem}.png"
    cutout, generation_record = generate_landmark(
        record["city"], record["landmark"], cutout, quality=quality
    )
    image = Image.open(cutout).convert("RGBA")
    alpha = image.getchannel("A")
    if alpha.getbbox() is None or alpha.getextrema() == (255, 255):
        raise RuntimeError(f"{record['city']}: cutout has no usable transparency")
    image.thumbnail((768, 768), Image.Resampling.LANCZOS)
    asset_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(asset_path, "WEBP", quality=92, method=3, exact=True)
    records = asset_dir / "records"
    records.mkdir(parents=True, exist_ok=True)
    metadata = json.loads(generation_record.read_text(encoding="utf-8"))
    metadata.update(
        {
            "city": record["city"],
            "landmark": record["landmark"],
            "builtin_asset": record["asset"],
        }
    )
    (records / f"{stem}.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return record["city"], asset_path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", type=Path, default=CATALOG_PATH)
    parser.add_argument("--asset-dir", type=Path, default=LANDMARK_DIR)
    parser.add_argument("--work-dir", type=Path, default=Path("build/builtin-landmarks"))
    parser.add_argument("--quality", choices=["low", "medium", "high"], default="high")
    parser.add_argument("--jobs", type=int, default=3)
    parser.add_argument("--city", action="append", help="generate only selected exact city names")
    args = parser.parse_args()

    catalog = json.loads(args.catalog.read_text(encoding="utf-8"))
    selected = set(args.city or [])
    pending = [
        item
        for item in catalog
        if (not selected or item["city"] in selected)
        and not (args.asset_dir / item["asset"]).is_file()
    ]
    args.work_dir.mkdir(parents=True, exist_ok=True)
    failures: dict[str, str] = {}
    with ThreadPoolExecutor(max_workers=max(1, args.jobs)) as executor:
        futures = {
            executor.submit(_generate, item, args.asset_dir, args.work_dir, args.quality): item
            for item in pending
        }
        for future in as_completed(futures):
            item = futures[future]
            try:
                city, path = future.result()
                print(f"OK  {city}  {path}", flush=True)
            except Exception as error:  # noqa: BLE001 - keep other paid generations reviewable
                failures[item["city"]] = str(error)
                print(f"FAILED  {item['city']}  {error}", flush=True)
    audit: dict[str, object] | None = None
    if not failures:
        try:
            audit = _audit_assets(catalog, args.asset_dir)
        except Exception as error:  # noqa: BLE001 - include audit failures in the report
            failures["asset_audit"] = str(error)
    report = args.work_dir / "generation-report.json"
    report.write_text(
        json.dumps(
            {
                "requested": [item["city"] for item in pending],
                "failures": failures,
                "raw_and_cutout_dir": str(args.work_dir.resolve()),
                "asset_audit": audit,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(report)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
