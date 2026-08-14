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
4. Run `routefilm image status`, then ask one landmark question using only options the current environment can execute.

Present poster, pilot, and final outputs as reviewable results rather than exposing every internal step.

## Collect the brief

Require one input:

1. Obtain the ordered place names, including repeated visits.

Never ask the user for longitude or latitude. Resolve coordinates automatically and use the cache on later runs. If the resolver reports equally plausible matches, ask which named place they mean and show human-readable candidate locations. Do not expose coordinates as the requested answer.

Offer the bundled generated arrow and unbranded black electric SUV. Use the arrow when the user has no preference. Automatically use the bundled roll-on/roll-off ferry for detected ferry legs; do not present the ferry as a whole-route marker. Infer portrait `720x1280`, `15 fps`, real map, distance-aware timing, silent first render, and title `Road Trip` when the user has no preference. Ask about title, music, aspect ratio, and visual theme only when the answer materially changes the first review.

Always resolve the landmark choice before building arrivals. Read the `generation_enabled` field from `routefilm image status`. If true, ask “到站时需要展示城市地标吗？” with `智能推荐并生成（推荐）`, `不展示`, and `使用已有图片`. If false, do not offer generation; use `不展示（推荐）`, `使用已有图片`, and `先配置生图服务`. Treat repeated cities as one generated landmark asset. Do not generate landmark images until the proposed landmark list and prompts are approved.

If the user selects `先配置生图服务`, enter a blocking setup state. Do not create an ad hoc empty file and continue a no-landmark branch in parallel. Read the image-service setup in [assets.md](references/assets.md), determine which category is missing, and ask only the next required setup question. Use `routefilm image configure` for the URL, never accept a key in chat or a command argument, and wait while the user places the key locally in the reported private config file or process environment. Rerun `routefilm image status` after confirmation. Return to the landmark question only when `generation_enabled` becomes true; remain in setup or explicitly let the user choose to leave setup otherwise.

## Build in review gates

1. Run the preflight script in `scripts/preflight.py`.
2. Create a YAML project with `routefilm init` and replace `route` with the ordered place names. Let `fetch`, `poster`, or `render` resolve coordinates automatically.
3. If automatic resolution raises an ambiguity, ask one structured candidate-choice question for one ambiguous name at a time, update that name with city/province context, and retry.
4. Render a national poster with `routefilm poster` before a video.
5. Fetch and inspect OSRM route geometry. Keep automatic ferry classification unless a genuine exception needs an explicit override.
6. Render a short opening and one representative dense-city leg when making a new style.
7. Render the silent full video only after the poster and sample pass review.
8. Add music as a separate branch so map revisions never silently invalidate a music edit.
9. Run `routefilm qa` and inspect ferry, repeated-stop, dense-city, opening, and ending keyframes.
10. After the silent master passes review, ask one music question: keep the silent master, search licensed music, or use audio supplied by the user. Do not combine this with another decision.

Read [workflow.md](references/workflow.md) for the complete decision sequence. Read [motion-and-camera.md](references/motion-and-camera.md) when tuning movement. Read [assets.md](references/assets.md) before generating or cutting out vehicles, ferries, or landmarks. Read [music.md](references/music.md) before searching or downloading audio. Read [release-checklist.md](references/release-checklist.md) before final delivery.

## Apply production rules

- Keep Web Mercator from tiles through final composition. Never stretch a geographic bounding box into the viewport.
- Keep the status panel outside the map rectangle.
- Use actual route geometry instead of straight lines when a router is available.
- Sample the moving marker by traveled distance. Derive heading from the tangent of the same smoothed position series.
- Give routes above 420 km a higher camera and slightly faster traversal. Give routes below 55 km a closer camera and longer traversal.
- Keep city labels visible while useful. Drop labels only on collision or when the national scale cannot hold them.
- Enlarge a first-arrival landmark at map center. Pulse a repeated arrival in place instead of replaying the full showcase.
- Use a staged ferry handoff: approach, board, sail, exit, continue. Do not morph a car into a ferry.
- Start with a national route hold and smooth camera dive. End with a slow national pullback and hold the complete route.

## Choose the marker

Set `video.marker` to `arrow` or `black-suv`; both are bundled and require no generation call. Keep `video.show_ferry` enabled unless the user explicitly disables ferry visuals. For custom generation:

1. Draft the exact prompt with `routefilm vehicle prompt` and show it for approval.
2. State that generation uses only `gpt-image-2` and may incur API cost.
3. Run `routefilm image status`. Require both `url_configured` and `key_configured`; if either is false, do not call image generation. Explain which configuration category is missing without displaying values, then ask whether to enter the blocking setup flow, use a bundled/user-provided asset, or skip generation.
4. Read the endpoint and key through RouteFilm's configuration resolver. It checks explicit process environment first, then a selected dotenv file, the nearest project `.env`, and the private user config. Never request that a key be pasted into chat, YAML, Markdown, shell history, or source code.
5. Run `routefilm vehicle generate` only after approval.
6. Prefer local `rembg` cutout. Fall back to chroma keying, retain the raw image, and inspect the alpha edge at full size.

Do not substitute another image model. Do not call image generation merely because the default arrow is available.

For generated landmarks, first propose one recognizable landmark per unique city. Use `routefilm landmark prompt` for review, then check `routefilm image status` and run `routefilm landmark generate` only when both configuration checks pass and the user approves the prompts. Add city names in the renderer, never in the generated image.

## Handle music safely

Search Openverse or Wikimedia Commons through `routefilm music search`. Download only a selected manifest item with an allowed license. Keep the generated `.license.json` beside the audio. Default to CC0, Public Domain Mark, CC BY, and CC BY-SA; require the user to make an explicit licensing decision for anything else.

Analyze BPM and beat candidates before building regional segments. Use equal-power crossfades and arrival accents, then mux without re-encoding the video. Never commit downloaded music to the repository.

## Finish

Report the project YAML, poster/sample, silent master, optional music edition, QA report, attribution records, and any unresolved map or music licensing constraints. Do not claim geographic, political-boundary, copyright, or public-map-service compliance on the user's behalf.
