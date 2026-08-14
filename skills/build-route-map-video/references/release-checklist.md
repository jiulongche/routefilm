# Release Checklist

- Confirm stop order, repeat visits, leg count, unique city count, and displayed distance.
- Confirm every routed leg; investigate straight-line fallbacks.
- Confirm Web Mercator proportions from opening through ending.
- Confirm the full-route overview contains all required geography without clipping or excessive empty space.
- Confirm labels appear, remain readable, and do not cover the active marker unnecessarily.
- Confirm long legs use a higher camera and dense clusters use close views.
- Confirm heading follows displacement without side-slip.
- Confirm ferry boarding and exiting are readable in both directions.
- Confirm first landmarks enlarge and repeat landmarks do not replay.
- Confirm the status panel remains outside the map.
- Decode the entire video and inspect black-frame results.
- Inspect opening, first arrival, shortest leg, longest leg, ferry, repeat visit, and ending keyframes.
- Keep `© OpenStreetMap contributors` visible when OSM data or tiles are used.
- Keep music source and license sidecars; verify attribution text.
- Remove secrets, tile caches, frame caches, downloaded audio, and unclear-license assets before publishing.
