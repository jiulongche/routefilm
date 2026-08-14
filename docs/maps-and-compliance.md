# Maps, Projection, And Compliance

RouteFilm's public defaults are development conveniences, not a production map entitlement.

## Attribution and service use

Keep `© OpenStreetMap contributors` visible in outputs that use OSM data or tiles. Review ODbL attribution requirements separately from the operational tile policy. The standard OSM raster endpoint forbids heavy bulk use; sustained rendering should use a provider whose plan permits it or a self-hosted stack.

The public OSRM endpoint is a demonstration service. Cache route geometry, rate-limit requests, and configure another router for repeated workloads. Nominatim likewise requires an identifying User-Agent and low request frequency.

## Coordinate systems in China

OSM and OSRM generally use WGS84-like longitude/latitude. Some licensed Chinese providers expose GCJ-02 or BD-09 coordinates and impose provider-specific display rules. Never overlay coordinates from different systems without an explicit adapter and validation. For public or commercial distribution in China, consult a qualified local map provider and applicable surveying/map-publication requirements.

## Boundaries and labels

Tile providers determine base-map boundaries and labels. RouteFilm adds route and city overlays but does not certify political boundary representation. Review national overview frames at the intended publication size and against the requirements that apply to the release.

## Privacy

An ordered city list may be harmless, while precise homes, hotels, dates, or customer routes may be personal data. Use generalized public examples, keep private YAML out of the repository, and remove route caches before sharing a project archive.
