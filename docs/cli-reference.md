# Manual CLI Reference

Most users should invoke the Agent Skill and let Codex or Claude Code operate these commands. Use this page only for manual or automated pipelines.

## Install and preflight

```bash
python -m pip install -e ".[dev]"
python skills/build-route-map-video/scripts/preflight.py
```

## Create a project

```bash
routefilm init my-trip.yaml
```

The generated file only needs an ordered name list:

```yaml
route: [海口, 徐闻, 湛江, 南宁]
video:
  title: 暑假快乐行
  marker: arrow # or black-suv
  show_ferry: true
```

`fetch`, `poster`, and `render` resolve and cache coordinates automatically. Users never need to enter longitude or latitude.

The standalone geocoder is an optional diagnostic when investigating an ambiguous place name:

```bash
routefilm geocode "海口|徐闻|湛江|南宁" \
  --country-code cn \
  --output build/geocoding-review.json
```

Only results marked `needs_review` require clarification. Clarify them by making the place name more specific, for example `临平区，杭州市`; do not ask users for coordinates. Explicit `lon` and `lat` fields remain available only as an advanced offline override.

## Map and video

```bash
routefilm fetch my-trip.yaml
routefilm poster my-trip.yaml --output build/poster.jpg
routefilm render my-trip.yaml
routefilm qa output/road-trip.mp4 --output build/qa.json
```

## Marker assets

`arrow` and `black-suv` are bundled marker presets. With `show_ferry: true`, recognized ferry legs automatically use the bundled ferry and staged vehicle handoff.

Save the no-cost bundled arrow:

```bash
routefilm vehicle default --output assets/default-arrow.png
```

Check whether paid image generation is enabled without printing credentials:

```bash
routefilm image status
```

The result must report both `url_configured: true` and `key_configured: true`. The generator refuses to run when either value is missing.

Prepare a reusable user-level config when a value is missing:

```bash
routefilm image configure --base-url https://api.openai.com/v1
routefilm image status
```

The configure command prints the private config path and never accepts an API key argument. Put `ROUTEFILM_IMAGE_API_KEY` in that file locally, or keep using `OPENAI_API_KEY` from the process environment. RouteFilm automatically reads the nearest project `.env` and `~/.config/routefilm/.env`; use `--scope project` to prepare the former. Process environment values take precedence.

Review a GPT Image 2 prompt before generating:

```bash
routefilm vehicle prompt "一辆黑色电动跨界 SUV，车顶玻璃清晰"
```

After the status check passes, generate:

```bash
routefilm vehicle generate "一辆黑色电动跨界 SUV，车顶玻璃清晰" \
  --output assets/vehicle.png
```

Review and generate a city landmark through the same protected image configuration:

```bash
routefilm landmark prompt "杭州" "西湖"
routefilm landmark generate "杭州" "西湖" \
  --output assets/landmarks/hangzhou-west-lake.png
```

Cut out an existing asset locally:

```bash
python -m pip install -e ".[cutout]"
routefilm vehicle cutout raw.png --method rembg --output transparent.png
```

## Licensed music

```bash
routefilm music search "upbeat road trip" \
  --provider openverse --output build/music-search.json
routefilm music download build/music-search.json RESULT_ID \
  --output-dir build/licensed-audio
routefilm music analyze build/licensed-audio/track.mp3 \
  --output build/track-analysis.json
routefilm music mix examples/music-plan.example.yaml --output build/score.wav
routefilm music mux output/silent.mp4 build/score.wav \
  --output output/music-edition.mp4
```

The downloader allows CC0, Public Domain Mark, CC BY, and CC BY-SA by default and writes a `.license.json` sidecar. Verify the source page and attribution requirements before publication.
