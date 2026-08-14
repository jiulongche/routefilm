# Music

## Search and provenance

Search only providers whose results expose source and license metadata:

```bash
routefilm music search "upbeat travel electronic" \
  --provider openverse --output build/music-search.json
routefilm music search "cinematic road trip" \
  --provider wikimedia --output build/music-search-wikimedia.json
```

Review the landing page and license before downloading a selected result:

```bash
routefilm music download build/music-search.json RESULT_ID \
  --output-dir build/licensed-audio
```

Keep the `.license.json` sidecar. The downloader allows `cc0`, `pdm`, `by`, and `by-sa` by default. A technical allowlist does not replace human license review or attribution.

## Beat analysis and mix

```bash
routefilm music analyze build/licensed-audio/track.mp3 \
  --output build/track-analysis.json
routefilm music mix examples/music-plan.example.yaml --output build/score.wav
routefilm music mux output/silent.mp4 build/score.wav --output output/music-edition.mp4
```

Split long journeys by geographic or emotional region. Use 1.5–2.0 second equal-power crossfades. Add restrained arrival accents at major cities and ferry beats. Avoid an accent on every event when it makes the mix mechanical.

Validate loudness, clipping, silence, transition timing, and end fade. Do not commit downloaded tracks.
