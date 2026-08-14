# Contributing

Open an issue before a large behavior or provider change. Keep provider adapters optional and keep the deterministic geometry, camera, ferry, timeline, and QA modules independent of any single agent vendor.

Useful first contributions include improving a city's bundled landmark and provenance, adding a public route fixture, clarifying installation on a supported platform, or turning a reproducible visual edge case into a small offline test. Comment on an existing issue before starting so two people do not solve the same problem.

Set up a development environment:

```bash
python -m pip install -e ".[dev]"
python -m pytest
ruff check .
```

Do not add network-dependent unit tests. Use small synthetic fixtures. Never commit API keys, caches, downloaded audio, rendered frames, customer routes, or unclear-license assets.

Changes to the Skill must preserve `skills/build-route-map-video/SKILL.md` as the canonical source and pass the Skill validator.

When sharing screenshots or videos, use only routes and media you can publish. Include the RouteFilm version, ordered city names, output dimensions, and whether the result used bundled or custom assets. A short before/after clip is more useful than a large render archive.
