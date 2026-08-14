# RouteFilm

For route-map or travel-video work, invoke `/build-route-map-video` and follow the canonical Skill linked from `.claude/skills/build-route-map-video`.

Ask exactly one question at a time, using Claude Code's structured choice UI when available. Collect the route first, then marker choice, then run the image capability check and offer only executable landmark choices. Default to the arrow and switch to the bundled ferry automatically on ferry legs. Resolve coordinates automatically and ask one structured human-readable candidate question per true ambiguity. Review the poster and a short sample before a full render. Never place credentials, downloaded music, tile caches, or private route data in the repository.

Treat `先配置生图服务` as a blocking setup state. Follow the canonical Skill's configure-and-recheck loop; do not prepare an ad hoc file and continue a no-landmark branch in parallel.
