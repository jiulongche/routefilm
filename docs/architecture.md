# Architecture

```text
ordered stops
    │
    ├─ automatic geocoding ── candidate cache + resolution report
    │
    ├─ OSRM geometry ── route cache
    │       │
    │       ├─ Web Mercator camera planner
    │       ├─ distance sampler + shared tangent heading
    │       └─ ferry boundary + five-stage handoff
    │
    ├─ OSM tile compositor ── tile cache
    │       │
    │       └─ labels + landmarks + marker + external status panel
    │
    └─ raw RGB frames ── FFmpeg partial ── decode check ── immutable run master
                                      │
licensed music manifest ── mix ───────┴─ muxed edition
                                      │
                                  QA report
```

## Module boundaries

- `config.py`: strict YAML loading and path resolution.
- `geocoding.py`: rate-limited, ranked and cached Nominatim resolver with narrow ambiguity handling.
- `routing.py`: OSRM fetch, deterministic cache key, automatic known-ferry classification, explicit fallback.
- `geo.py`: Web Mercator, distance sampling, smoothing, heading invariant.
- `camera.py`: geometry fit, distance zoom rules, projected interpolation.
- `ferry.py`: direction-neutral sea-gap detection and stage timing.
- `tiles.py`: small raster tile cache and compositor.
- `renderer.py`: frame composition and FFmpeg streaming.
- `landmarks.py`: bundled offline landmark catalog and asset resolution.
- `runs.py`: immutable run manifests, asset hashes, atomic latest publication, and comparisons.
- `assets.py`: bundled arrow/unbranded black SUV/ferry presets, protected GPT Image 2 vehicle/landmark generation, cutout.
- `music.py`: licensed search, provenance download, analysis, mix, mux.
- `qa.py`: stream probe, full decode, and black-frame detection.

Provider URLs live in YAML or RouteFilm's environment/dotenv configuration resolver. Core motion logic has no network dependency and is unit tested with synthetic routes.

## Extension points

Add a tile or router provider behind the existing URL templates. Add music search providers by returning `MusicResult`. Keep credentials in process environment or ignored private dotenv files, and return source/license metadata with every remote asset.

Vector tiles, MapLibre, GCJ-02 provider adapters, richer collision solving, and automated storyboard extraction are appropriate future modules. They should not weaken the simple Pillow/FFmpeg reference implementation.
