# RouteFilm

[![CI](https://github.com/jiulongche/routefilm/actions/workflows/ci.yml/badge.svg)](https://github.com/jiulongche/routefilm/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/jiulongche/routefilm?display_name=tag&sort=semver)](https://github.com/jiulongche/routefilm/releases)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-2f855a.svg)](LICENSE)
[![Agent Skills](https://img.shields.io/badge/Agent_Skills-Codex_%7C_Claude_Code-f2b84b)](docs/agent-compatibility.md)

**Give an agent any ordered city list and get a cinematic travel video on real maps.** No coordinates are required: RouteFilm resolves routed roads and handles distance-aware cameras, marker motion, ferry handoffs, city landmarks, and optional music.

![RouteFilm animated preview](https://raw.githubusercontent.com/jiulongche/routefilm/main/docs/media/routefilm-preview.gif)

RouteFilm includes 63 offline city landmarks, so image generation is optional. Codex and Claude Code are first-class Skill targets. Routes always come from user input; the included examples are replaceable starting points, never fixed defaults.

## Fastest path

RouteFilm requires Python 3.10+, FFmpeg, and a CJK-capable font. Install the local package and run the preflight once:

```bash
git clone https://github.com/jiulongche/routefilm.git
cd routefilm
python -m pip install -e ".[cutout]"
python skills/build-route-map-video/scripts/preflight.py
```

Then ask Codex:

```text
$build-route-map-video Turn Haikou, Xuwen, Zhanjiang, and Nanning into a portrait road-trip video. Use the default arrow.
```

Or ask Claude Code:

```text
/build-route-map-video Turn Haikou, Xuwen, Zhanjiang, and Nanning into a portrait road-trip video. Use the default arrow.
```

The agent asks exactly one question at a time: ordered stops first, then a structured marker choice, then an offline built-in/custom/no-landmark choice, and finally a concrete recommended or custom title. RouteFilm bundles 63 unique city landmarks covering all provincial-level representative cities plus the original 35-city production route. Recommended options appear first with short consequences and a free-form Other path. Recognized ferry legs switch to the bundled roll-on/roll-off ferry automatically.

Before asking about generated landmarks, RouteFilm verifies that both the image API URL and key are configured without displaying either value. It offers automatic generation only when the capability is actually available. Choosing setup pauses poster, sample, and full rendering, uses a private user or project dotenv file, and returns to the landmark choice only after the capability check passes or the user explicitly leaves setup.

RouteFilm resolves, ranks, and caches coordinates automatically; users never enter longitude or latitude. The agent asks which named place was intended only when equally plausible matches remain.

The agent handles setup, map configuration, distance-aware cameras, adaptive regional or national overview framing, persistent map/status landmarks, poster and pilot review, ferry logic, rendering, and QA. Every poster or render receives an immutable run directory with config, hashes, code revision, and QA; the requested output path is only an atomic latest pointer.

## Example routes

- [Dense Jiangnan city cluster](examples/jiangnan-city-cluster.yaml): close camera work for nearby stops and labels
- [Cross-province road trip](examples/cross-province-road-trip.yaml): higher, faster long legs with readable regional sections
- [Haikou ferry route](examples/haikou-ferry-route.yaml): automatic five-stage vehicle/ferry handoff

Copy an example and replace only the ordered names under `route`, or skip YAML entirely and give your own route directly to the Skill.

## Production detail

[Watch the first five arrivals from the production master](https://github.com/jiulongche/routefilm/raw/refs/heads/main/docs/media/routefilm-five-stops-demo.mp4) · 40 seconds · 720×1280 · silent master

![Full arrival storyboard](https://raw.githubusercontent.com/jiulongche/routefilm/main/docs/media/routefilm-full-storyboard.jpg)

Codex and Claude Code are first-class targets. Agent Skills-compatible tools and agents that read `AGENTS.md` receive best-effort support.

See the [Chinese README](README.md), [manual CLI reference](docs/cli-reference.md), [map/compliance notes](docs/maps-and-compliance.md), and [bilingual launch kit](docs/launch-kit.md).

Code is MIT licensed. Original demonstration media in `docs/media/` is CC BY 4.0. Map data, tiles, fonts, audio, generated assets, and external services retain their own terms.
