# Third-Party Notices

RouteFilm does not redistribute map tiles, route caches, fonts, or downloaded music. It includes generated marker and landmark assets; those images are workflow assets rather than geographic data.

## OpenStreetMap

Default raster maps and geocoding use OpenStreetMap-related services. OpenStreetMap data is available under ODbL and requires attribution: `© OpenStreetMap contributors`. Review the [copyright page](https://www.openstreetmap.org/copyright), [tile usage policy](https://operations.osmfoundation.org/policies/tiles/), and [Nominatim usage policy](https://operations.osmfoundation.org/policies/nominatim/). The public services are defaults for low-volume development, not bulk rendering.

## OSRM

The default routing endpoint is the public OSRM demonstration server. OSRM software is BSD licensed. The public endpoint has no production SLA; use an appropriate hosted or self-managed router for sustained workloads.

## FFmpeg

FFmpeg is invoked as an external executable and is not bundled. Its effective license depends on the build and codecs installed by the user.

## rembg

`rembg` is an optional local background-removal dependency. It may download model weights governed by their own terms.

## Openverse And Wikimedia Commons

Search results point to third-party audio. A result's Creative Commons or public-domain metadata remains subject to the source record. RouteFilm's allowlist and sidecar are workflow aids, not legal advice.

## OpenAI GPT Image 2

Optional custom marker generation calls a user-configured Image API with model `gpt-image-2`. Generated assets and API use remain subject to the provider terms and applicable law. No API credentials are bundled.

The bundled arrow, black vehicle, and ferry were created for RouteFilm with GPT Image 2 and processed locally into transparent PNGs. Their SHA-256 checksums are:

- arrow: `9e3420de14ae8eddf17befbeb8114e3f1182b21d1e50c207fe538090083a7942`
- unbranded black electric SUV: `0216fd997f57740ae44c4f340106246c1df20aa08dab8f15d3bddbc30d731115`
- ferry: `745669ccd78a304ba1eb778c4c1184206757ea37caa588c423543d25ecd9e40c`

The black SUV preset is an original fictional design requested without badges, logos, trademarks, or identifiable manufacturer styling. Generated assets and API use remain subject to the provider terms and applicable law.

## Bundled Landmark Library

The 63 original AI-assisted RouteFilm landmark assets under `src/routefilm/data/landmarks/` are released under CC BY 4.0, with attribution to RouteFilm contributors. Their catalog and retained generation records identify the represented city and landmark, packaged WebP hash, byte size, and dimensions. These illustrations are creative miniatures, not authoritative geographic, architectural, cultural, or political records.

## Demonstration Media

The original RouteFilm contributions in `docs/media/` are licensed under CC BY 4.0. OpenStreetMap content visible within those files remains subject to OSM attribution and applicable ODbL terms; the media license does not relicense third-party map content. See `docs/media/LICENSE.md` for the attribution wording.
