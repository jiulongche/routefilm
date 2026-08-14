import json
from pathlib import Path

from routefilm.config import load_project
from routefilm.runs import begin_run, complete_run, list_runs, versioned_path


def _project(tmp_path: Path):
    project = tmp_path / "trip.yaml"
    project.write_text(
        "stops: [{name: A, lon: 1, lat: 1}, {name: B, lon: 2, lat: 2}]\n"
        "video: {output: output/trip.mp4}\n",
        encoding="utf-8",
    )
    return load_project(project)


def test_run_preserves_previous_output_and_publishes_latest_pointer(tmp_path: Path):
    config = _project(tmp_path)
    requested = config.video.output
    requested.parent.mkdir(parents=True)
    requested.write_bytes(b"previous")
    run = begin_run(config, "render", requested)
    artifact = run.output_dir / "trip.mp4"
    artifact.write_bytes(b"current")

    complete_run(run, artifact, requested, qa_report={"decode_ok": True})

    manifest = json.loads(run.manifest.read_text(encoding="utf-8"))
    assert manifest["status"] == "complete"
    assert (run.path / manifest["previous_output"]["path"]).read_bytes() == b"previous"
    assert requested.read_bytes() == b"current"
    assert json.loads((run.root / "latest.json").read_text())["run_id"] == run.run_id
    assert list_runs(tmp_path)[0]["run_id"] == run.run_id


def test_second_run_does_not_follow_or_mutate_latest_symlink_target(tmp_path: Path):
    first_config = _project(tmp_path)
    first = begin_run(first_config, "render", first_config.video.output)
    first_artifact = first.output_dir / "trip.mp4"
    first_artifact.write_bytes(b"first")
    complete_run(first, first_artifact, first_config.video.output)

    second_config = load_project(first_config.source_path)
    assert second_config.video.output == tmp_path / "output/trip.mp4"
    second = begin_run(second_config, "render", second_config.video.output)
    second_artifact = second.output_dir / "trip.mp4"
    second_artifact.write_bytes(b"second")
    complete_run(second, second_artifact, second_config.video.output)

    assert first_artifact.is_file() and not first_artifact.is_symlink()
    assert first_artifact.read_bytes() == b"first"
    assert second_config.video.output.read_bytes() == b"second"


def test_versioned_path_never_reuses_an_existing_asset_name(tmp_path: Path):
    output = tmp_path / "landmark.png"
    output.write_bytes(b"one")

    candidate = versioned_path(output)

    assert candidate != output
    assert candidate.name.startswith("landmark-")
    assert candidate.suffix == ".png"
