# Workflow

## Contents

1. Intake
2. Route verification
3. Review gates
4. Full render
5. Delivery

## Intake

Ask exactly one question at a time. Prefer the agent product's native structured-choice UI; otherwise use a numbered list with 2-3 choices, recommended first, one-line descriptions, and a free-form Other path.

1. If missing, ask for the ordered place list as free text.
2. Ask only: “路线上的移动标记用什么？”
   - `质感箭头（推荐）`: bundled, readable, no generation cost.
   - `黑色电动 SUV`: bundled, logo-free vehicle with warm-gold map-readable accents.
   - `自定义载具`: user image or GPT Image 2 after configuration and prompt review.
3. When `自定义载具` is selected, ask one source question. Put `使用已有图片` first. Include GPT Image 2 generation only when the capability check passes; otherwise offer `先配置生图服务` as a non-generation path.
4. Run `routefilm image status`, then ask only: “到站时需要展示城市地标吗？”

Do not treat the ferry as a whole-route marker choice; mention after marker selection that recognized ferry legs switch automatically. Infer other sensible defaults. Ask one follow-up at a time only when a place-name ambiguity or external cost blocks progress.

## Route verification

Treat repeated stops as meaningful events. Preserve them in order and count unique cities separately from arrivals.

Create the project directly from names:

```yaml
route: [海口, 徐闻, 湛江, 南宁]
```

Running `fetch`, `poster`, or `render` resolves coordinates automatically, caches Nominatim candidates, and writes a technical resolution report. Never ask the user to enter coordinates. When two candidates are genuinely indistinguishable, show their readable location descriptions and ask which place they intended; then qualify the name with its city or province.

Fetch route geometry and inspect fallback legs. The Haikou-Xuwen pair is classified as ferry automatically in either direction. Preserve explicit `driving` or `ferry` overrides for exceptional routes. A fallback is a visual warning, not a substitute for a confirmed road route.

## Landmark decision

Adapt the choices to actual capability:

- When `generation_enabled` is true: `智能推荐并生成（推荐）`, `不展示`, `使用已有图片`.
- When `generation_enabled` is false: `不展示（推荐）`, `使用已有图片`, `先配置生图服务`.

Never offer automatic generation when no image-generation system is available. Generate one asset per unique city and reuse it for repeated visits. Before paid generation, show the landmark list and prompts for approval.

When the user chooses `先配置生图服务`, pause all image-dependent work and stay in setup:

1. Run `routefilm image status` and identify whether the URL, key, or both are missing.
2. If the URL is missing, ask one endpoint question: official OpenAI, a custom compatible endpoint, or leave setup. After the answer, run `routefilm image configure --base-url URL`. If the URL is already configured but the key is missing, run `routefilm image configure` without a URL so it prepares the private file from the existing endpoint. The default user-level file is reusable across projects.
3. Show only the config path printed by the command. If the key is missing, ask the user to place `ROUTEFILM_IMAGE_API_KEY` there locally or set `OPENAI_API_KEY` in the process, then confirm. Never ask for the value in chat and never pass it as a command argument.
4. After confirmation, rerun `routefilm image status`. If enabled, ask the landmark question again with the generation option. If still disabled, explain only the remaining missing category and stay in setup.

Do not prepare an arbitrary config format, do not assume a default endpoint, and do not continue rendering a no-landmark version while setup is active. Only leave setup when generation becomes available or the user explicitly chooses an existing-image or no-landmark path.

## Review gates

Use these gates in order:

1. National poster: route order, national framing, map proportions, Taiwan visibility when relevant, status-panel separation.
2. Opening sample: national hold, smooth dive, first city arrival.
3. Dense sample: label collisions and close zoom in the shortest cluster.
4. Ferry sample: spatially clear car/ship handoff in both route directions.
5. Repeated-stop sample: first visit showcases; later visit pulses only.
6. Silent master: verify the map before adding audio.
7. Music branch: after the silent master passes, ask only whether to keep it silent, search licensed music, or use user-supplied audio.

## Full render

Render from YAML:

```bash
routefilm fetch examples/china-coastal-demo.yaml
routefilm poster examples/china-coastal-demo.yaml --output build/poster.jpg
routefilm render examples/china-coastal-demo.yaml
routefilm qa output/road-trip.mp4 --output build/qa.json
```

Expect public OSM and OSRM services to be unsuitable for bulk production. Use a hosted or self-managed provider and configure the URLs for repeated or commercial workloads.

## Delivery

Keep these outputs:

- project YAML and route cache identifier;
- poster and representative keyframes;
- silent master;
- music mix plan and licensed audio sidecars;
- optional music mux;
- QA JSON;
- credits and map attribution.

Do not deliver tile caches, frame caches, API keys, generated raw requests containing secrets, or third-party music without redistribution rights.
