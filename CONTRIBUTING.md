# Contributing

Open an issue before a large behavior or provider change. Keep provider adapters optional and keep the deterministic geometry, camera, ferry, timeline, and QA modules independent of any single agent vendor.

Set up a development environment:

```bash
python -m pip install -e ".[dev]"
python -m pytest
ruff check .
```

Do not add network-dependent unit tests. Use small synthetic fixtures. Never commit API keys, caches, downloaded audio, rendered frames, customer routes, or unclear-license assets.

Changes to the Skill must preserve `skills/build-route-map-video/SKILL.md` as the canonical source and pass the Skill validator.
