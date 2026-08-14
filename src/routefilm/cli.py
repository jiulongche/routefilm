"""RouteFilm command line interface."""

from __future__ import annotations

import argparse
import json
import shutil
import urllib.error
from pathlib import Path

from .assets import (
    cutout_file,
    generate_landmark,
    generate_vehicle,
    image_api_status,
    landmark_prompt,
    save_default_arrow,
    vehicle_prompt,
)
from .config import MapSettings, load_project
from .geocoding import geocode_route
from .image_config import configure_image_environment
from .music import (
    DEFAULT_ALLOWED_LICENSES,
    analyze_audio,
    download_from_manifest,
    mix_plan,
    mux_audio,
    search_music,
    write_search_manifest,
)
from .qa import inspect
from .renderer import render_poster, render_video
from .routing import fetch_routes

PROJECT_TEMPLATE = """# Just list the places in travel order. Coordinates resolve automatically.
route:
  - 海口
  - 徐闻
  - 湛江
  - 南宁

video:
  title: 暑假快乐行
  output: output/road-trip.mp4
  width: 720
  height: 1280
  fps: 15
  # marker: arrow        # arrow or black-suv
  # show_ferry: true     # automatic on recognized ferry legs
  # vehicle_asset: assets/custom-vehicle.png  # overrides marker
  # ferry_asset: assets/ferry.png             # overrides bundled ferry
  # font_path: /path/to/a/CJK-font.ttc
"""


def _path(value: str) -> Path:
    return Path(value).expanduser().resolve()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="routefilm", description="Cinematic videos on real maps")
    commands = parser.add_subparsers(dest="command", required=True)
    init = commands.add_parser("init", help="write a documented starter project")
    init.add_argument("output")

    fetch = commands.add_parser("fetch", help="fetch/cache OSRM geometry")
    fetch.add_argument("project")
    fetch.add_argument("--refresh", action="store_true")

    geocode = commands.add_parser("geocode", help="resolve an ordered place list for human review")
    geocode.add_argument("route", help="comma- or pipe-separated place names")
    geocode.add_argument("--country-code", default="cn")
    geocode.add_argument("--user-agent", default=MapSettings.user_agent)
    geocode.add_argument("--output", default="build/geocoding-review.json")

    poster = commands.add_parser("poster", help="render the full-route overview still")
    poster.add_argument("project")
    poster.add_argument("--output", required=True)
    poster.add_argument("--refresh", action="store_true")

    render = commands.add_parser("render", help="render a silent H.264 route video")
    render.add_argument("project")
    render.add_argument("--refresh", action="store_true")

    vehicle = commands.add_parser("vehicle", help="create route marker assets")
    vehicle_commands = vehicle.add_subparsers(dest="vehicle_command", required=True)
    default = vehicle_commands.add_parser("default", help="save the built-in arrow")
    default.add_argument("--output", required=True)
    prompt = vehicle_commands.add_parser("prompt", help="print the GPT Image 2 prompt for review")
    prompt.add_argument("description")
    generate = vehicle_commands.add_parser("generate", help="generate a custom vehicle with GPT Image 2")
    generate.add_argument("description")
    generate.add_argument("--output", required=True)
    generate.add_argument("--quality", choices=["low", "medium", "high"], default="high")
    cutout = vehicle_commands.add_parser("cutout", help="remove a sprite background locally")
    cutout.add_argument("input")
    cutout.add_argument("--output", required=True)
    cutout.add_argument("--method", choices=["auto", "rembg", "chroma"], default="auto")

    image = commands.add_parser("image", help="inspect GPT Image 2 configuration")
    image_commands = image.add_subparsers(dest="image_command", required=True)
    image_commands.add_parser("status", help="report URL/key readiness without showing values")
    image_configure = image_commands.add_parser(
        "configure", help="prepare a private dotenv file without accepting a key on the command line"
    )
    image_configure.add_argument(
        "--base-url", help="required only when no endpoint is already configured"
    )
    image_configure.add_argument("--scope", choices=["user", "project"], default="user")

    landmark = commands.add_parser("landmark", help="create city landmark assets")
    landmark_commands = landmark.add_subparsers(dest="landmark_command", required=True)
    landmark_prompt_command = landmark_commands.add_parser(
        "prompt", help="print a GPT Image 2 landmark prompt for review"
    )
    landmark_prompt_command.add_argument("city")
    landmark_prompt_command.add_argument("landmark")
    landmark_generate = landmark_commands.add_parser(
        "generate", help="generate a landmark with GPT Image 2"
    )
    landmark_generate.add_argument("city")
    landmark_generate.add_argument("landmark")
    landmark_generate.add_argument("--output", required=True)
    landmark_generate.add_argument(
        "--quality", choices=["low", "medium", "high"], default="high"
    )

    music = commands.add_parser("music", help="licensed music discovery and editing")
    music_commands = music.add_subparsers(dest="music_command", required=True)
    search = music_commands.add_parser("search")
    search.add_argument("query")
    search.add_argument("--provider", choices=["openverse", "wikimedia"], default="openverse")
    search.add_argument("--limit", type=int, default=12)
    search.add_argument("--output", required=True)
    download = music_commands.add_parser("download")
    download.add_argument("manifest")
    download.add_argument("result_id")
    download.add_argument("--output-dir", required=True)
    download.add_argument("--allow-license", action="append")
    analyze = music_commands.add_parser("analyze")
    analyze.add_argument("audio")
    analyze.add_argument("--output")
    mix = music_commands.add_parser("mix")
    mix.add_argument("plan")
    mix.add_argument("--output", required=True)
    mux = music_commands.add_parser("mux")
    mux.add_argument("video")
    mux.add_argument("audio")
    mux.add_argument("--output", required=True)

    qa = commands.add_parser("qa", help="decode and inspect a rendered video")
    qa.add_argument("video")
    qa.add_argument("--output")
    return parser


def _dispatch(args: argparse.Namespace) -> int:
    if args.command == "init":
        destination = _path(args.output)
        if destination.exists():
            raise FileExistsError(destination)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(PROJECT_TEMPLATE, encoding="utf-8")
        print(destination)
    elif args.command == "fetch":
        routes = fetch_routes(load_project(args.project), refresh=args.refresh)
        print(json.dumps([route.__dict__ for route in routes], ensure_ascii=False, indent=2))
    elif args.command == "geocode":
        separator = "|" if "|" in args.route else ","
        names = [name.strip() for name in args.route.split(separator) if name.strip()]
        if len(names) < 2:
            raise ValueError("route must contain at least two place names")
        print(geocode_route(names, _path(args.output), country_code=args.country_code, user_agent=args.user_agent))
    elif args.command == "poster":
        print(render_poster(load_project(args.project), _path(args.output), args.refresh))
    elif args.command == "render":
        if not shutil.which("ffmpeg"):
            raise RuntimeError("ffmpeg is required")
        print(render_video(load_project(args.project), args.refresh))
    elif args.command == "vehicle":
        if args.vehicle_command == "default":
            print(save_default_arrow(_path(args.output)))
        elif args.vehicle_command == "prompt":
            print(vehicle_prompt(args.description))
        elif args.vehicle_command == "generate":
            output, record = generate_vehicle(args.description, _path(args.output), quality=args.quality)
            print(output)
            print(record)
        else:
            print(cutout_file(_path(args.input), _path(args.output), args.method))
    elif args.command == "image":
        if args.image_command == "status":
            print(json.dumps(image_api_status(), ensure_ascii=False, indent=2))
        else:
            path = configure_image_environment(args.base_url, scope=args.scope)
            status = image_api_status()
            print(
                json.dumps(
                    {
                        "config_path": str(path),
                        **status,
                        "next_step": (
                            "configuration ready"
                            if status["generation_enabled"]
                            else "set ROUTEFILM_IMAGE_API_KEY in this file locally, then rerun status"
                        ),
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
    elif args.command == "landmark":
        if args.landmark_command == "prompt":
            print(landmark_prompt(args.city, args.landmark))
        else:
            output, record = generate_landmark(
                args.city,
                args.landmark,
                _path(args.output),
                quality=args.quality,
            )
            print(output)
            print(record)
    elif args.command == "music":
        if args.music_command == "search":
            results = search_music(args.query, args.provider, args.limit)
            write_search_manifest(_path(args.output), args.query, args.provider, results)
            print(json.dumps([item.__dict__ for item in results], ensure_ascii=False, indent=2))
        elif args.music_command == "download":
            allowed = set(args.allow_license) if args.allow_license else DEFAULT_ALLOWED_LICENSES
            audio, record = download_from_manifest(_path(args.manifest), args.result_id, _path(args.output_dir), allowed)
            print(audio)
            print(record)
        elif args.music_command == "analyze":
            print(json.dumps(analyze_audio(_path(args.audio), _path(args.output) if args.output else None), indent=2))
        elif args.music_command == "mix":
            print(mix_plan(_path(args.plan), _path(args.output)))
        else:
            print(mux_audio(_path(args.video), _path(args.audio), _path(args.output)))
    elif args.command == "qa":
        report = inspect(_path(args.video))
        text = json.dumps(report, ensure_ascii=False, indent=2)
        if args.output:
            _path(args.output).write_text(text, encoding="utf-8")
        print(text)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return _dispatch(args)
    except (
        FileNotFoundError,
        KeyError,
        PermissionError,
        RuntimeError,
        TypeError,
        ValueError,
        urllib.error.URLError,
    ) as error:
        parser.exit(2, f"routefilm: error: {error}\n")


if __name__ == "__main__":
    raise SystemExit(main())
