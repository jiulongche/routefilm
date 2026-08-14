# Motion And Camera

## Contents

1. Projection
2. Distance tiers
3. Vehicle motion
4. Ferry motion
5. Labels and landmarks

## Projection

Project tiles, route geometry, camera centers, and labels in normalized Web Mercator. Interpolate camera centers in projected space and zoom in log space. This prevents the map from changing shape during pullback.

## Distance tiers

Use route distance as the primary heuristic, then override after visual review:

| Distance | Baseline travel | Camera rule |
| --- | ---: | --- |
| under 55 km | 4.0 s | closest; preserve local road context |
| 55–120 km | 3.6 s | close |
| 120–280 km | 3.3 s | normal |
| 280–420 km | 3.15 s | slightly higher |
| above 420 km | 3.0 s | higher and slightly faster |
| ferry | 11.0 s | port close-ups plus strait view |

Dense metro clusters may need more time than the table. Long legs should not remain at city-block zoom.

## Vehicle motion

Resample polyline geometry by cumulative traveled distance. Smooth projected positions. Derive each heading from the forward tangent of that exact smoothed series. Add only subtle lateral suspension and turn lean after the heading is correct.

Never smooth raw heading independently from position. Never point directly from the start city to the end city.

## Ferry motion

Infer the likely sea span from the longest gap in route geometry, then verify it visually. Hold the ferry at the embarkation point while the vehicle approaches. Switch to a ferry-with-deck-vehicle composition only after the boarding beat. Mirror the same stages on a reverse crossing.

## Labels and landmarks

Place labels greedily with four candidate anchors. Avoid the active marker, ports, status panel, and already placed labels. Keep names persistent in close views.

Keep pending landmarks gray or hidden. On first arrival, move the landmark to map center at up to 70% map width and hold long enough to inspect it. On repeat arrival, use a small pulse or wobble at the city point.
