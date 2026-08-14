# Music Workflow

## Principles

1. Search metadata before downloading media.
2. Review the source landing page and license.
3. Download a selected manifest item and keep its sidecar.
4. Analyze tempo and event candidates.
5. Build a declarative regional mix plan.
6. Mux audio into the silent master without video re-encoding.
7. Check clipping, silence, transitions, attribution, and end fade.

## Providers

Openverse aggregates openly licensed audio metadata. Wikimedia Commons exposes direct file and license metadata. Both can contain inaccurate upstream records; the tool therefore preserves links and does not claim a license is valid.

The downloader blocks unknown, noncommercial, no-derivatives, and other unapproved licenses by default. A user can extend the allowlist, but that action is an explicit licensing decision.

## Regional plan

See `examples/music-plan.example.yaml`. Region boundaries should follow geography, mood, or chapter changes. Keep adjacent regions contiguous. The mixer overlaps them around boundaries with sine/cosine envelopes, adds optional synthetic arrival accents, applies opening and ending fades, and peak-limits to `0.96`.

The beat analyzer is intentionally lightweight. Use it to suggest tempo and onset times, then listen and adjust. It is not a substitute for a DAW when musical phrasing matters.
