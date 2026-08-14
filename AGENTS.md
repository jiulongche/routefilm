# RouteFilm Agent Guidance

Use `skills/build-route-map-video/SKILL.md` for any task involving route maps, road-trip videos, vehicle/ferry movement, city landmarks, or route soundtracks.

Keep `SKILL.md` as the single behavioral source. Do not copy its full content into vendor instruction files. Preserve API keys, map caches, frame caches, downloaded audio, and private itinerary data outside version control.

Run focused tests after code changes:

```bash
python -m pytest
python /path/to/skill-creator/scripts/quick_validate.py skills/build-route-map-video
```

Do not run network render or image-generation commands in tests. Use public OSM/OSRM/Nominatim endpoints only for low-volume manual validation with an identifying User-Agent.
