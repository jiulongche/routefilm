---
name: build-route-map-video
description: Build polished route animations and travel videos on real Chinese or global maps. Use when a user provides an ordered city/stop list and wants a dynamic map, driving route, road-trip video, ferry transition, city landmark arrival, licensed soundtrack, GIF/MP4, or route-film production plan. Also use to diagnose camera zoom, map distortion, label collisions, vehicle side-slip, repeated stops, music timing, or black frames in an existing route animation.
---

# Build Route Map Video

Create a reviewable route project before rendering expensive outputs. Use the repository's `routefilm` CLI for deterministic work and keep generated assets, caches, and final outputs outside the skill directory.

## Keep the user experience simple

Operate the CLI and files for the user. Do not ask the user to run commands, edit YAML, choose technical parameters, or read the internal checklist unless they explicitly request manual control.

Ask exactly one question at a time. Use the product's native structured-choice UI when available, such as Codex `request_user_input` or Claude Code `AskUserQuestion`; otherwise show a short numbered list. Never combine route, marker, landmark, music, or ambiguity decisions in one message. Put the recommended option first, provide 2-3 mutually exclusive choices with one-line consequences, and preserve the UI's free-form “Other” choice.

Ask in this order and skip any decision the user already answered:

1. Ask for the ordered route as one free-text question, preserving repeated places.
2. Ask “路线上的移动标记用什么？” with `质感箭头（推荐）`, `黑色电动 SUV`, and `自定义载具`.
3. If the user selects a custom marker, resolve its source with one separate question. Offer an existing image first. Offer GPT Image 2 only when `routefilm image status` reports `generation_enabled: true`; otherwise offer configuration as a separate path, never as an executable generation choice.
4. Check built-in landmark coverage, then ask one landmark-source question. Put `使用内置全国地标（推荐）` first when the route is covered, followed by `自定义地标` and `不展示`. If coverage is partial, state the covered count in the option consequence.
5. Only after `自定义地标` is selected, run `routefilm image status` and ask one source question. Offer `使用已有图片`; offer GPT Image 2 only when generation is enabled. When it is disabled, do not offer generation; offer `先配置生图服务` instead.
6. After the landmark branch is fully resolved, infer one short, specific title from the route and known trip context. Ask “片名怎么设置？” with `采用推荐标题《具体标题》（推荐）`, `自定义标题`, and `Road Trip`. Do not show a placeholder such as “自动生成标题”; the recommendation itself must be visible. If the user chooses custom, ask for the exact title as the next single free-text question. Write the result to `video.title` before the first poster.

Present poster, pilot, and final outputs as reviewable results rather than exposing every internal step.

## Collect the brief

Require one input:

1. Obtain the ordered place names, including repeated visits.

Never ask the user for longitude or latitude. Resolve coordinates automatically and use the cache on later runs. If the resolver reports equally plausible matches, ask which named place they mean and show human-readable candidate locations. Do not expose coordinates as the requested answer.

Offer the bundled generated arrow and unbranded black electric SUV. Use the arrow when the user has no preference. Automatically use the bundled roll-on/roll-off ferry for detected ferry legs; do not present the ferry as a whole-route marker. Infer portrait `720x1280`, `15 fps`, real map, distance-aware timing, and a silent first render. Resolve the title through the single-question choice above; `Road Trip` remains the fallback only when the user explicitly leaves the title unspecified. Ask about music, aspect ratio, and visual theme only when the answer materially changes the first review.

Always resolve the landmark choice before building arrivals. RouteFilm includes an offline curated library of 63 unique cities, covering the 34 provincial-level representative cities plus the original 35-city production route. Use `video.landmarks: auto` for built-in assets with explicit stop assets taking precedence; use `video.landmarks: none` only after the user chooses no landmarks. Treat repeated cities as one asset. Do not generate landmark images until the proposed landmark list and complete prompts are approved.

If the user selects `先配置生图服务`, enter a blocking setup state. Do not create an ad hoc empty file and continue a no-landmark branch in parallel. Do not render a poster, sample, silent master, or alternate no-landmark branch while setup is active. Read the image-service setup in [assets.md](references/assets.md), determine which category is missing, and ask only the next required setup question. Use `routefilm image configure` for the URL, never accept a key in chat or a command argument, and wait while the user places the key locally in the reported private config file or process environment. Rerun `routefilm image status` after confirmation. Return to the landmark question only when `generation_enabled` becomes true; remain in setup or explicitly let the user choose to leave setup otherwise.

## Build in review gates

1. Run the preflight script in `scripts/preflight.py`.
2. Create a YAML project with `routefilm init` and replace `route` with the ordered place names. Let `fetch`, `poster`, or `render` resolve coordinates automatically.
3. If automatic resolution raises an ambiguity, ask one structured candidate-choice question for one ambiguous name at a time, update that name with city/province context, and retry.
4. Fully resolve landmark mode, including any requested image-service setup, then resolve and write the title. These are hard gates before visual rendering.
5. Fetch and inspect OSRM route geometry. Keep automatic ferry classification unless a genuine exception needs an explicit override.
6. Render a full-route overview poster with `routefilm poster` before a video. Regional routes use a fitted overview; only geographically broad China routes use the full-country camera.
7. Render a short opening and one representative dense-city leg when making a new style.
8. Render the silent full video only after the poster and sample pass review.
9. Add music as a separate branch so map revisions never silently invalidate a music edit.
10. Run `routefilm qa` and inspect ferry, repeated-stop, dense-city, opening, and ending keyframes.
11. After the silent master passes review, ask one music question: keep the silent master, search licensed music, or use audio supplied by the user. Do not combine this with another decision.
12. Run `routefilm runs list --workspace PROJECT_DIRECTORY` before delivery and report the immutable run ID. Use `routefilm runs compare` when more than one review version exists. Never delete or overwrite an earlier run unless the user explicitly chooses a cleanup target.

Read [workflow.md](references/workflow.md) for the complete decision sequence. Read [motion-and-camera.md](references/motion-and-camera.md) when tuning movement. Read [assets.md](references/assets.md) before generating or cutting out vehicles, ferries, or landmarks. Read [music.md](references/music.md) before searching or downloading audio. Read [release-checklist.md](references/release-checklist.md) before final delivery.

## Apply production rules

- Keep Web Mercator from tiles through final composition. Never stretch a geographic bounding box into the viewport.
- Keep the status panel outside the map rectangle.
- Use actual route geometry instead of straight lines when a router is available.
- Sample the moving marker by traveled distance. Derive heading from the tangent of the same smoothed position series.
- Give routes above 420 km a higher camera and slightly faster traversal. Give routes below 55 km a closer camera and longer traversal.
- Keep city labels visible while useful. Drop labels only on collision or when the overview scale cannot hold them.
- Keep pending destination landmarks gray, unlock them in color at arrival, retain small visited landmarks by their cities, and show the active thumbnail in the external status panel.
- Enlarge a first-arrival landmark from its city to map center, hold, then return it to the city. Pulse a repeated arrival in place instead of replaying the full showcase.
- Use a staged ferry handoff: approach, board, sail, exit, continue. Do not morph a car into a ferry.
- Start with a fitted full-route hold, visible complete route, route summary, and smooth camera dive. Keep the direction arrow in the status panel while traveling. End with a slow pullback to the same overview and hold the complete route. Reserve the full-China camera for geographically broad routes or an explicit YAML override.

## Choose the marker

Set `video.marker` to `arrow` or `black-suv`; both are bundled and require no generation call. Keep `video.show_ferry` enabled unless the user explicitly disables ferry visuals. For custom generation:

1. Draft the exact prompt with `routefilm vehicle prompt` and show it for approval.
2. State that generation uses only `gpt-image-2` and may incur API cost.
3. Run `routefilm image status`. Require both `url_configured` and `key_configured`; if either is false, do not call image generation. Explain which configuration category is missing without displaying values, then ask whether to enter the blocking setup flow, use a bundled/user-provided asset, or skip generation.
4. Read the endpoint and key through RouteFilm's configuration resolver. It checks explicit process environment first, then a selected dotenv file, the nearest project `.env`, and the private user config. Never request that a key be pasted into chat, YAML, Markdown, shell history, or source code.
5. Run `routefilm vehicle generate` only after approval.
6. Require `rembg`, `onnxruntime`, and a ready model cache for production cutout. Fall back to border-sampled chroma keying only when a clean background exists, retain every raw/cutout stage, and inspect the alpha edge at full size.

Do not substitute another image model. Do not call image generation merely because the default arrow is available.

For generated landmarks, first propose one recognizable landmark per unique city. Use `routefilm landmark prompt` for review, then check `routefilm image status` and run `routefilm landmark generate` only when both configuration checks pass and the user approves every complete prompt. Keep summer daylight, terrain-island composition, restrained route colors, no flags, and no generated text consistent across the batch. Add city and landmark names in the renderer, never in the generated image.

## Handle music safely

Search Openverse or Wikimedia Commons through `routefilm music search`. Download only a selected manifest item with an allowed license. Keep the generated `.license.json` beside the audio. Default to CC0, Public Domain Mark, CC BY, and CC BY-SA; require the user to make an explicit licensing decision for anything else.

Analyze BPM and beat candidates before building regional segments. Use equal-power crossfades and arrival accents, then mux without re-encoding the video. Never commit downloaded music to the repository.

## Finish

Report the project YAML, immutable run directory and ID, poster/sample, silent master, optional music edition, QA report, attribution records, and any unresolved map or music licensing constraints. Do not claim geographic, political-boundary, copyright, or public-map-service compliance on the user's behalf.
