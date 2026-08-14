# Security Policy

Report security issues through the repository's [private security-advisory flow](https://github.com/jiulongche/routefilm/security/advisories/new) rather than opening a public issue containing credentials or private route data.

RouteFilm reads optional image credentials only from `ROUTEFILM_IMAGE_API_KEY` or `OPENAI_API_KEY`. Do not place keys in project YAML, Markdown, source code, command examples with real values, or generated manifests.

Generation records intentionally omit credential values, endpoint URLs, and absolute local paths. Keep raw prompts and generated records private unless they have been reviewed for publication.

Before publishing a fork, scan for:

- `.env` files and API keys;
- personal itineraries or precise private locations;
- OSM tile and OSRM caches;
- full frame directories and videos;
- downloaded music and license-restricted assets;
- generated request records that contain private prompts.

The music downloader limits files to 200 MiB, requires HTTP(S), and rejects unknown or non-allowlisted licenses by default. Users must still review remote content and license claims.
