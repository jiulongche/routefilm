# RouteFilm

Give an agent an ordered city list and receive a real-map road-trip video with routed roads, automatic cameras, marker motion, ferry handoffs, landmarks, and optional music.

![RouteFilm poster](https://raw.githubusercontent.com/jiulongche/routefilm/main/docs/media/routefilm-poster.jpg)

[Watch the first five arrivals from the production master](https://github.com/jiulongche/routefilm/raw/refs/heads/main/docs/media/routefilm-five-stops-demo.mp4).

![Full arrival storyboard](https://raw.githubusercontent.com/jiulongche/routefilm/main/docs/media/routefilm-full-storyboard.jpg)

## Fastest path

RouteFilm requires Python 3.10+, FFmpeg, and a CJK-capable font. Install the local package and run the preflight once:

```bash
git clone https://github.com/jiulongche/routefilm.git
cd routefilm
python -m pip install -e .
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

The agent asks exactly one question at a time: ordered stops first, then a structured marker choice, then a landmark choice adapted to the available image-generation capability. Recommended options appear first with short consequences and a free-form Other path. Recognized ferry legs switch to the bundled roll-on/roll-off ferry automatically.

Before asking about generated landmarks, RouteFilm verifies that both the image API URL and key are configured without displaying either value. It offers automatic generation only when the capability is actually available.

RouteFilm resolves, ranks, and caches coordinates automatically; users never enter longitude or latitude. The agent asks which named place was intended only when equally plausible matches remain.

The agent handles setup, map configuration, distance-aware cameras, poster and pilot review, ferry logic, rendering, and QA.

Codex and Claude Code are first-class targets. Agent Skills-compatible tools and agents that read `AGENTS.md` receive best-effort support.

See the [Chinese README](README.md), [manual CLI reference](docs/cli-reference.md), and [map/compliance notes](docs/maps-and-compliance.md).

Code is MIT licensed. Original demonstration media in `docs/media/` is CC BY 4.0. Map data, tiles, fonts, audio, generated assets, and external services retain their own terms.
