"""Pillow/FFmpeg renderer for a real-map route film."""

from __future__ import annotations

import math
import subprocess
from collections import Counter
from collections.abc import Iterable
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from .assets import builtin_ferry, builtin_marker
from .camera import Camera, fit_geometry, interpolate, route_overview_camera
from .config import ProjectConfig, Stop
from .ferry import boundary_positions, ferry_state
from .geo import Point, smoothstep, vehicle_motion_series
from .geocoding import resolve_project
from .routing import RoutedLeg, fetch_routes
from .tiles import TileStore, render_basemap, screen_point
from .timeline import leg_seconds

PALETTE = {
    "background": (18, 24, 28, 255),
    "panel": (26, 36, 39, 255),
    "paper": (255, 249, 232, 255),
    "muted": (174, 192, 188, 255),
    "coral": (239, 83, 73, 255),
    "gold": (247, 184, 61, 255),
    "cyan": (78, 191, 202, 255),
    "border": (77, 103, 103, 255),
}


def _font_path(configured: Path | None) -> Path:
    candidates = [
        configured,
        Path("/System/Library/Fonts/PingFang.ttc"),
        Path("/System/Library/Fonts/STHeiti Medium.ttc"),
        Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
        Path("/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc"),
        Path("C:/Windows/Fonts/msyh.ttc"),
    ]
    for path in candidates:
        if path and path.exists():
            return path
    raise FileNotFoundError("No CJK font found. Set video.font_path in the project YAML.")


class Fonts:
    def __init__(self, path: Path, scale: float) -> None:
        self.hero = ImageFont.truetype(str(path), round(42 * scale))
        self.city = ImageFont.truetype(str(path), round(31 * scale))
        self.body = ImageFont.truetype(str(path), round(20 * scale))
        self.small = ImageFont.truetype(str(path), round(15 * scale))
        self.tiny = ImageFont.truetype(str(path), round(12 * scale))


class Renderer:
    def __init__(self, config: ProjectConfig, routes: list[RoutedLeg]) -> None:
        self.config = config
        self.routes = routes
        self.width = config.video.width
        self.height = config.video.height
        self.scale = self.width / 720
        margin = round(24 * self.scale)
        header = round(132 * self.scale)
        panel = round(220 * self.scale)
        self.map_rect = (margin, header, self.width - margin, self.height - panel - margin)
        self.map_size = (self.map_rect[2] - self.map_rect[0], self.map_rect[3] - self.map_rect[1])
        self.fonts = Fonts(_font_path(config.video.font_path), self.scale)
        self.tiles = TileStore(
            config.map.cache_dir, config.map.tile_url, config.map.user_agent
        )
        self.cameras = [
            fit_geometry(leg.coordinates, leg.distance_km, self.map_size) for leg in routes
        ]
        all_points = [point for leg in routes for point in leg.coordinates]
        self.overview = route_overview_camera(
            all_points,
            self.map_size,
            override_center=config.map.national_center,
            override_zoom=config.map.national_zoom,
        )
        self.vehicle_asset = (
            self._asset(config.video.vehicle_asset)
            if config.video.vehicle_asset
            else self._crop(builtin_marker(config.video.marker))
        )
        if config.video.ferry_asset:
            self.ferry_asset = self._asset(config.video.ferry_asset)
        elif config.video.show_ferry:
            self.ferry_asset = self._crop(builtin_ferry())
        else:
            self.ferry_asset = None
        self.landmarks = {
            stop.name: self._asset(stop.landmark_asset) for stop in config.stops if stop.landmark_asset
        }
        self.stop_by_name = {stop.name: stop for stop in config.stops}
        self.total_km = round(sum(route.distance_km for route in routes))

    @staticmethod
    def _crop(image: Image.Image) -> Image.Image:
        bbox = image.getchannel("A").getbbox()
        return image.crop(bbox) if bbox else image

    @classmethod
    def _asset(cls, path: Path | None) -> Image.Image | None:
        if path is None:
            return None
        return cls._crop(Image.open(path).convert("RGBA"))

    def _base(self, camera: Camera) -> tuple[Image.Image, Image.Image]:
        canvas = Image.new("RGBA", (self.width, self.height), PALETTE["background"])
        draw = ImageDraw.Draw(canvas, "RGBA")
        draw.text(
            (round(32 * self.scale), round(34 * self.scale)),
            self.config.video.title,
            font=self.fonts.hero,
            fill=PALETTE["paper"],
        )
        map_image = render_basemap(self.tiles, camera.center, camera.zoom, self.map_size).convert("RGBA")
        glaze = Image.new("RGBA", map_image.size, (27, 61, 49, 13 if camera.zoom > 4.4 else 24))
        map_image = Image.alpha_composite(map_image, glaze)
        layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        layer.alpha_composite(map_image, (self.map_rect[0], self.map_rect[1]))
        return canvas, layer

    def _route_points(self, leg: RoutedLeg, camera: Camera, limit: int | None = None) -> list[Point]:
        coords = leg.coordinates if limit is None else leg.coordinates[:limit]
        stride = max(1, math.ceil(len(coords) / 700))
        sampled = coords[::stride]
        if coords and sampled[-1] != coords[-1]:
            sampled.append(coords[-1])
        return [screen_point(point, camera.center, camera.zoom, self.map_rect) for point in sampled]

    def _line(self, layer: Image.Image, points: list[Point], color: tuple[int, ...], width: int, dashed: bool = False) -> None:
        if len(points) < 2:
            return
        glow = Image.new("RGBA", layer.size, (0, 0, 0, 0))
        gd = ImageDraw.Draw(glow, "RGBA")
        gd.line(points, fill=(*color[:3], 90), width=width * 3, joint="curve")
        layer.alpha_composite(glow.filter(ImageFilter.GaussianBlur(width * 1.2)))
        draw = ImageDraw.Draw(layer, "RGBA")
        if dashed:
            for index in range(0, len(points) - 1, 2):
                draw.line(points[index:index + 2], fill=color, width=width)
        else:
            draw.line(points, fill=color, width=width, joint="curve")
        draw.line(points, fill=(255, 248, 225, 150), width=max(1, width // 3), joint="curve")

    def _labels(self, layer: Image.Image, camera: Camera, names: Iterable[str]) -> None:
        draw = ImageDraw.Draw(layer, "RGBA")
        occupied: list[tuple[float, float, float, float]] = []
        for name in dict.fromkeys(names):
            stop = self.stop_by_name.get(name)
            if not stop:
                continue
            x, y = screen_point((stop.lon, stop.lat), camera.center, camera.zoom, self.map_rect)
            if not (self.map_rect[0] + 8 < x < self.map_rect[2] - 8 and self.map_rect[1] + 8 < y < self.map_rect[3] - 8):
                continue
            box = draw.textbbox((0, 0), name, font=self.fonts.small, stroke_width=2)
            tw, th = box[2] - box[0], box[3] - box[1]
            chosen = None
            for dx, dy, anchor in ((12, -12, "ls"), (-12, -12, "rs"), (12, 18, "la"), (-12, 18, "ra")):
                left = x + dx if "l" in anchor else x + dx - tw
                top = y + dy - th if "s" in anchor else y + dy
                candidate = (left - 3, top - 2, left + tw + 3, top + th + 2)
                if all(candidate[2] < item[0] or candidate[0] > item[2] or candidate[3] < item[1] or candidate[1] > item[3] for item in occupied):
                    chosen = x + dx, y + dy, anchor, candidate
                    break
            if not chosen:
                continue
            draw.ellipse((x - 4, y - 4, x + 4, y + 4), fill=PALETTE["coral"], outline=PALETTE["paper"], width=1)
            draw.text(
                chosen[:2], name, font=self.fonts.small, fill=PALETTE["paper"],
                stroke_width=2, stroke_fill=(12, 24, 26, 220), anchor=chosen[2],
            )
            occupied.append(chosen[3])

    def _sprite(self, layer: Image.Image, image: Image.Image, point: Point, angle: float, size: int) -> None:
        sprite = image.copy()
        sprite.thumbnail((size, size), Image.Resampling.LANCZOS)
        sprite = sprite.rotate(-math.degrees(angle), resample=Image.Resampling.BICUBIC, expand=True)
        layer.alpha_composite(sprite, (round(point[0] - sprite.width / 2), round(point[1] - sprite.height / 2)))

    def _vehicle(self, layer: Image.Image, leg: RoutedLeg, camera: Camera, local: float, position: Point, heading: float) -> None:
        point = screen_point(position, camera.center, camera.zoom, self.map_rect)
        size = round((55 + max(0, camera.zoom - 5) * 2.5) * self.scale)
        if leg.kind != "ferry" or self.ferry_asset is None:
            self._sprite(layer, self.vehicle_asset, point, heading, size)
            return
        state = ferry_state(leg.coordinates, local)
        embark, disembark = boundary_positions(leg.coordinates)
        embark_point = screen_point(embark, camera.center, camera.zoom, self.map_rect)
        disembark_point = screen_point(disembark, camera.center, camera.zoom, self.map_rect)
        ferry_angle = math.atan2(disembark_point[1] - embark_point[1], disembark_point[0] - embark_point[0])
        ferry_size = round(size * 1.55)
        if state.stage == "approach":
            self._sprite(layer, self.ferry_asset, embark_point, ferry_angle, ferry_size)
            self._sprite(layer, self.vehicle_asset, point, heading, size)
        elif state.stage in {"boarding", "sailing"}:
            ferry_point = embark_point if state.stage == "boarding" else point
            self._sprite(layer, self.ferry_asset, ferry_point, ferry_angle, ferry_size)
            self._sprite(layer, self.vehicle_asset, ferry_point, ferry_angle, round(size * 0.42))
        elif state.stage == "exiting":
            self._sprite(layer, self.ferry_asset, disembark_point, ferry_angle, ferry_size)
            if state.stage_progress > 0.45:
                self._sprite(layer, self.vehicle_asset, point, heading, size)
        else:
            if state.stage_progress < 0.4:
                self._sprite(layer, self.ferry_asset, disembark_point, ferry_angle, ferry_size)
            self._sprite(layer, self.vehicle_asset, point, heading, size)

    def _landmark(self, layer: Image.Image, stop: Stop, phase: float, repeated: bool) -> None:
        image = self.landmarks.get(stop.name)
        if image is None or repeated:
            return
        enter = smoothstep(min(1.0, phase / 0.28))
        exit_amount = smoothstep(max(0.0, (phase - 0.78) / 0.22))
        scale = (0.72 + 0.28 * enter) * (1.0 - 0.45 * exit_amount)
        max_width = round(self.map_size[0] * 0.70 * scale)
        max_height = round(self.map_size[1] * 0.60 * scale)
        sprite = image.copy()
        sprite.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
        x = (self.map_rect[0] + self.map_rect[2]) // 2 - sprite.width // 2
        y = (self.map_rect[1] + self.map_rect[3]) // 2 - sprite.height // 2
        shadow = Image.new("RGBA", sprite.size, (0, 0, 0, 0))
        shadow.putalpha(sprite.getchannel("A").filter(ImageFilter.GaussianBlur(round(8 * self.scale))))
        layer.alpha_composite(shadow, (x + round(5 * self.scale), y + round(8 * self.scale)))
        layer.alpha_composite(sprite, (x, y))

    def _status(self, canvas: Image.Image, leg_index: int, progress: float, arrival: bool = False) -> None:
        left, right = round(26 * self.scale), self.width - round(26 * self.scale)
        top, bottom = self.map_rect[3] + round(20 * self.scale), self.height - round(24 * self.scale)
        draw = ImageDraw.Draw(canvas, "RGBA")
        draw.rounded_rectangle((left, top, right, bottom), radius=round(7 * self.scale), fill=PALETTE["panel"], outline=PALETTE["border"], width=max(1, round(2 * self.scale)))
        leg = self.routes[min(leg_index, len(self.routes) - 1)]
        draw.text((left + 24 * self.scale, top + 20 * self.scale), f"LEG {leg_index + 1:02d} / {len(self.routes):02d}", font=self.fonts.tiny, fill=PALETTE["coral"])
        draw.text((left + 24 * self.scale, top + 52 * self.scale), leg.origin, font=self.fonts.city, fill=PALETTE["paper"])
        draw.text((right - 24 * self.scale, top + 52 * self.scale), leg.destination, font=self.fonts.city, fill=(255, 165, 143, 255), anchor="ra")
        prefix = "渡轮约" if leg.kind == "ferry" else "约"
        draw.text((right - 24 * self.scale, top + 23 * self.scale), f"{prefix} {round(leg.distance_km)} km", font=self.fonts.small, fill=PALETTE["muted"], anchor="ra")
        y = bottom - round(38 * self.scale)
        x1, x2 = left + round(24 * self.scale), right - round(24 * self.scale)
        draw.line((x1, y, x2, y), fill=(74, 94, 99, 255), width=max(3, round(7 * self.scale)))
        done = x1 + (x2 - x1) * progress
        draw.line((x1, y, done, y), fill=PALETTE["coral"], width=max(3, round(7 * self.scale)))
        draw.ellipse((done - 5 * self.scale, y - 5 * self.scale, done + 5 * self.scale, y + 5 * self.scale), fill=PALETTE["paper"])
        if arrival:
            draw.text(((left + right) / 2, top + 112 * self.scale), "到达", font=self.fonts.small, fill=PALETTE["gold"], anchor="ma")

    def frame(
        self,
        camera: Camera,
        leg_index: int,
        local: float,
        overall: float,
        *,
        mode: str = "travel",
        arrival_phase: float | None = None,
        visit_counts: Counter[str] | None = None,
        vehicle_position: Point | None = None,
        vehicle_heading: float = 0.0,
        arrival_stop: Stop | None = None,
    ) -> Image.Image:
        canvas, layer = self._base(camera)
        if mode in {"opening", "outro"}:
            for leg in self.routes:
                self._line(layer, self._route_points(leg, camera), PALETTE["coral"], max(2, round(4 * self.scale)), leg.kind == "ferry")
            names = [stop.name for stop in self.config.stops]
            self._labels(layer, camera, names)
        else:
            for index, leg in enumerate(self.routes):
                if index < leg_index:
                    self._line(layer, self._route_points(leg, camera), PALETTE["coral"], max(3, round(5 * self.scale)), leg.kind == "ferry")
                elif index == leg_index:
                    positions, headings = vehicle_motion_series(leg.coordinates, 180)
                    point_index = min(179, max(0, round(local * 179)))
                    route_progress = ferry_state(leg.coordinates, local).route_progress if leg.kind == "ferry" else local
                    partial_count = max(2, round(len(leg.coordinates) * route_progress))
                    self._line(layer, self._route_points(leg, camera, partial_count), PALETTE["gold"], max(4, round(7 * self.scale)), leg.kind == "ferry")
                    if arrival_phase is None:
                        self._vehicle(layer, leg, camera, local, vehicle_position or tuple(positions[point_index]), vehicle_heading or float(headings[point_index]))
                    break
            visited_names = [self.routes[index].origin for index in range(min(leg_index + 1, len(self.routes)))]
            visited_names.append(self.routes[leg_index].destination)
            self._labels(layer, camera, visited_names)
            if arrival_phase is not None:
                destination = arrival_stop or self.stop_by_name[self.routes[leg_index].destination]
                repeated = bool(visit_counts and visit_counts[destination.name] > 1)
                self._landmark(layer, destination, arrival_phase, repeated)
        draw = ImageDraw.Draw(layer, "RGBA")
        draw.text((self.map_rect[2] - 8 * self.scale, self.map_rect[3] - 10 * self.scale), "© OpenStreetMap contributors", font=self.fonts.tiny, fill=(22, 38, 40, 205), anchor="rs")
        mask = Image.new("L", canvas.size, 0)
        ImageDraw.Draw(mask).rounded_rectangle(self.map_rect, radius=round(8 * self.scale), fill=255)
        canvas.alpha_composite(Image.composite(layer, Image.new("RGBA", canvas.size), mask))
        if mode in {"opening", "outro"}:
            draw = ImageDraw.Draw(canvas, "RGBA")
            left, right = round(26 * self.scale), self.width - round(26 * self.scale)
            top, bottom = self.map_rect[3] + round(20 * self.scale), self.height - round(24 * self.scale)
            draw.rounded_rectangle((left, top, right, bottom), radius=round(7 * self.scale), fill=PALETTE["panel"], outline=PALETTE["border"], width=max(1, round(2 * self.scale)))
            label = "开始" if mode == "opening" else "完成"
            draw.text((left + 24 * self.scale, top + 25 * self.scale), f"{self.config.video.title} · {label}", font=self.fonts.city, fill=PALETTE["paper"])
            draw.text((left + 24 * self.scale, top + 83 * self.scale), f"{len(self.config.stops)} 站 · {len(self.routes)} 段 · 约 {self.total_km:,} km", font=self.fonts.body, fill=PALETTE["muted"])
        else:
            self._status(canvas, leg_index, overall, arrival_phase is not None)
        return canvas.convert("RGB")


def render_poster(config: ProjectConfig, output: Path, refresh: bool = False) -> Path:
    config = resolve_project(config, refresh=refresh)
    routes = fetch_routes(config, refresh=refresh)
    renderer = Renderer(config, routes)
    image = renderer.frame(renderer.overview, 0, 0, 0, mode="opening")
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output, quality=95, subsampling=0)
    return output


def render_video(config: ProjectConfig, refresh: bool = False) -> Path:
    config = resolve_project(config, refresh=refresh)
    routes = fetch_routes(config, refresh=refresh)
    renderer = Renderer(config, routes)
    output = config.video.output
    output.parent.mkdir(parents=True, exist_ok=True)
    fps = config.video.fps
    process = subprocess.Popen(
        [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-f", "rawvideo",
            "-pix_fmt", "rgb24", "-s", f"{config.video.width}x{config.video.height}",
            "-r", str(fps), "-i", "-", "-an", "-c:v", "libx264", "-preset", "medium",
            "-crf", str(config.video.crf), "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(output),
        ],
        stdin=subprocess.PIPE,
    )

    def emit(image: Image.Image) -> None:
        if process.stdin is None:
            raise RuntimeError("ffmpeg input pipe closed")
        process.stdin.write(image.tobytes())

    first_camera = renderer.cameras[0]
    hold = round(config.video.intro_hold_seconds * fps)
    dive = round(config.video.dive_seconds * fps)
    arrival = round(config.video.arrival_seconds * fps)
    for _ in range(hold):
        emit(renderer.frame(renderer.overview, 0, 0, 0, mode="opening"))
    for frame in range(dive):
        emit(renderer.frame(interpolate(renderer.overview, first_camera, frame / max(1, dive - 1)), 0, 0, 0, mode="opening"))

    visits: Counter[str] = Counter({config.stops[0].name: 1})
    for frame in range(arrival):
        emit(renderer.frame(first_camera, 0, 0, 0, arrival_phase=frame / max(1, arrival - 1), visit_counts=visits, arrival_stop=config.stops[0]))

    for index, (leg, camera, spec) in enumerate(zip(routes, renderer.cameras, config.legs)):
        seconds = spec.duration_seconds or leg_seconds(leg.distance_km, leg.kind)
        travel_frames = round(seconds * fps)
        positions, headings = vehicle_motion_series(leg.coordinates, travel_frames)
        previous_camera = renderer.cameras[index - 1] if index else camera
        for frame in range(travel_frames):
            local = frame / max(1, travel_frames - 1)
            camera_now = interpolate(previous_camera, camera, min(1.0, local / 0.26))
            route_progress = ferry_state(leg.coordinates, local).route_progress if leg.kind == "ferry" else local
            motion_index = min(travel_frames - 1, round(route_progress * (travel_frames - 1)))
            overall = (index + local) / len(routes)
            emit(renderer.frame(camera_now, index, local, overall, vehicle_position=tuple(positions[motion_index]), vehicle_heading=float(headings[motion_index])))
        visits[leg.destination] += 1
        for frame in range(arrival):
            emit(renderer.frame(camera, index, 1, (index + 1) / len(routes), arrival_phase=frame / max(1, arrival - 1), visit_counts=visits))

    outro = round(config.video.outro_seconds * fps)
    for frame in range(outro):
        camera = interpolate(renderer.cameras[-1], renderer.overview, frame / max(1, outro - 1))
        emit(renderer.frame(camera, len(routes) - 1, 1, 1, mode="outro"))
    for _ in range(round(config.video.final_hold_seconds * fps)):
        emit(renderer.frame(renderer.overview, len(routes) - 1, 1, 1, mode="outro"))
    if process.stdin:
        process.stdin.close()
    if process.wait():
        raise RuntimeError("ffmpeg failed")
    return output
