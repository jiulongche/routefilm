# Security Policy

Report security issues through the repository's [private security-advisory flow](https://github.com/jiulongche/routefilm/security/advisories/new) rather than opening a public issue containing credentials or private route data.

RouteFilm reads optional image credentials from the process or parsed dotenv files: the selected `ROUTEFILM_ENV_FILE`, the nearest project `.env`, or the private user config at `~/.config/routefilm/.env`. Process values take precedence. Do not place keys in project YAML, Markdown, source code, command arguments, examples with real values, or generated manifests. Project `.env` files are ignored by Git; user-level files created by `routefilm image configure` are restricted to the current user.

Generation records intentionally omit credential values, endpoint URLs, and absolute local paths. Keep raw prompts and generated records private unless they have been reviewed for publication.

Before publishing a fork, scan for:

- `.env` files and API keys;
- personal itineraries or precise private locations;
- OSM tile and OSRM caches;
- full frame directories and videos;
- downloaded music and license-restricted assets;
- generated request records that contain private prompts.

The music downloader limits files to 200 MiB, requires HTTP(S), and rejects unknown or non-allowlisted licenses by default. Users must still review remote content and license claims.
