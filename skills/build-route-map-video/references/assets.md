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

Configure credentials only through the environment:

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
