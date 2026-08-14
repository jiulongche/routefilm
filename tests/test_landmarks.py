import hashlib
import json

from routefilm.landmarks import (
    LANDMARK_DIR,
    builtin_landmark_path,
    landmark_catalog,
    landmark_preset,
)


def test_catalog_covers_provincial_representatives_and_original_route():
    catalog = landmark_catalog()

    assert len(catalog) >= 63
    for city in ("海口", "北京", "上海", "广州", "拉萨", "香港", "澳门", "台北"):
        assert landmark_preset(city) is not None
        assert builtin_landmark_path(city) is not None


def test_catalog_assets_are_unique_and_present():
    records = list(landmark_catalog().values())
    assets = [record["asset"] for record in records]

    assert len(assets) == len(set(assets))
    assert all(builtin_landmark_path(record["city"]) for record in records)


def test_every_builtin_asset_has_matching_packaged_provenance():
    for record in landmark_catalog().values():
        asset = LANDMARK_DIR / record["asset"]
        provenance = LANDMARK_DIR / "records" / f"{asset.stem}.json"
        metadata = json.loads(provenance.read_text(encoding="utf-8"))
        packaged = metadata["packaged_asset"]

        assert packaged["sha256"] == hashlib.sha256(asset.read_bytes()).hexdigest()
        assert packaged["bytes"] == asset.stat().st_size
        assert packaged["format"] == "WEBP"
        assert packaged["width"] <= 768
        assert packaged["height"] <= 768
