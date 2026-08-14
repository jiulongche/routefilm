# Assets

## Default marker

Choose one bundled marker preset:

- `arrow`: generated warm-gold route arrow; default.
- `black-suv`: unbranded black top-down electric SUV with warm-gold accents.

Recognized ferry legs automatically use the bundled top-down roll-on/roll-off ferry. The vehicle approaches, boards, sails, exits, and continues; never select the ferry as the whole-route marker.

Save the default arrow for another project with:

```bash
routefilm vehicle default --output assets/default-arrow.png
```

In YAML, use:

```yaml
video:
  marker: black-suv  # arrow or black-suv
  show_ferry: true
```

## Custom vehicle or ferry

Use strict top-down orthographic composition, one object, nose/bow pointing right, generous padding, and no text or shadow. Review the prompt before generation:

```bash
routefilm vehicle prompt "a black electric crossover with falcon-wing silhouette"
```

## Image service setup

RouteFilm resolves image settings in this order without mutating the process environment:

1. explicit function arguments used by integrations;
2. `ROUTEFILM_IMAGE_BASE_URL` plus `ROUTEFILM_IMAGE_API_KEY` or `OPENAI_API_KEY` in the process;
3. the file named by `ROUTEFILM_ENV_FILE` when set;
4. the nearest `.env` from the current directory upward;
5. `~/.config/routefilm/.env` or the matching `XDG_CONFIG_HOME` location.

Prepare the user-level config, which is reusable and kept outside the repository:

```bash
routefilm image configure --base-url https://api.openai.com/v1
```

Omit `--base-url` when an endpoint is already available and only the key is missing. Use `--scope project` only when the setting should stay with one checkout. The command prints the exact file path, writes the URL and an empty key slot, preserves unrelated dotenv values, and restricts the file to the current user. It deliberately has no key argument so credentials cannot enter shell history. The user must place the key in the reported file locally or expose it through the process environment; never ask them to paste it into chat.

The resulting values are equivalent to:

```text
ROUTEFILM_IMAGE_BASE_URL=https://api.openai.com/v1
ROUTEFILM_IMAGE_API_KEY=...
```

Check readiness without exposing values:

```bash
routefilm image status
```

Both `url_configured` and `key_configured` must be true. Missing either value disables every image-generation command. Do not fall back to an assumed public endpoint.

The generator is intentionally locked to `gpt-image-2`. It writes the chroma source, transparent output, and a `.generation.json` record. GPT Image 2 does not currently support transparent output, so cutout is a separate local step.

Install the optional cutout dependency and process any source:

```bash
python -m pip install -e ".[cutout]"
routefilm vehicle cutout raw.png --method rembg --output transparent.png
```

Use `--method chroma` when a clean `#00FF00` background is available. If the model adds a green gradient, use the imagegen Skill's `remove_chroma_key.py` with border sampling, soft matte, despill, and a one-pixel edge contraction. Inspect windows, roof rails, mirrors, ferry deck openings, and thin edges at 100% zoom.

## Landmarks

Prefer a recognizable single structure with a simple silhouette. Propose the complete city-to-landmark list before generating and create only one image per unique city. Review a prompt with `routefilm landmark prompt CITY LANDMARK`; after the image configuration check and approval, use `routefilm landmark generate CITY LANDMARK --output FILE`. Do not ask the image model to render the city name; add names with the renderer for spelling and style consistency. Retain provenance for generated and third-party landmark assets.
