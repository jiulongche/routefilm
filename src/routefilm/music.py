"""Licensed music discovery, download provenance, beat analysis, and region mixing."""

from __future__ import annotations

import hashlib
import json
import math
import re
import subprocess
import urllib.parse
import urllib.request
import wave
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import yaml

DEFAULT_ALLOWED_LICENSES = {"cc0", "pdm", "by", "by-sa"}
MAX_DOWNLOAD_BYTES = 200 * 1024 * 1024


@dataclass(frozen=True)
class MusicResult:
    id: str
    title: str
    creator: str | None
    provider: str
    license: str
    license_url: str | None
    landing_url: str
    download_url: str
    filetype: str | None = None
    duration_seconds: float | None = None


def _json(
    url: str,
    user_agent: str = "RouteFilm/0.1 (+https://github.com/jiulongche/routefilm)",
) -> dict[str, Any]:
    request = urllib.request.Request(url, headers={"User-Agent": user_agent})
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))


def normalize_license(value: str | None) -> str:
    value = (value or "").strip().lower().replace("cc ", "")
    aliases = {
        "public domain": "pdm",
        "publicdomain": "pdm",
        "cc-by": "by",
        "cc-by-sa": "by-sa",
        "cc0 1.0": "cc0",
    }
    return aliases.get(value, value.split(" ")[0])


def search_openverse(query: str, limit: int = 12) -> list[MusicResult]:
    params = urllib.parse.urlencode({"q": query, "page_size": min(limit, 50)})
    payload = _json(f"https://api.openverse.org/v1/audio/?{params}")
    results = []
    for item in payload.get("results", [])[:limit]:
        direct = item.get("url")
        landing = item.get("foreign_landing_url") or direct
        if not direct or not landing:
            continue
        results.append(
            MusicResult(
                id=str(item.get("id")),
                title=item.get("title") or "Untitled",
                creator=item.get("creator"),
                provider="openverse",
                license=normalize_license(item.get("license")),
                license_url=item.get("license_url"),
                landing_url=landing,
                download_url=direct,
                filetype=item.get("filetype"),
                duration_seconds=item.get("duration"),
            )
        )
    return results


def search_wikimedia(query: str, limit: int = 12) -> list[MusicResult]:
    params = {
        "action": "query",
        "format": "json",
        "generator": "search",
        "gsrsearch": f"filetype:audio {query}",
        "gsrnamespace": "6",
        "gsrlimit": str(min(limit, 50)),
        "prop": "imageinfo",
        "iiprop": "url|mime|extmetadata",
        "origin": "*",
    }
    payload = _json("https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(params))
    results: list[MusicResult] = []
    for page in payload.get("query", {}).get("pages", {}).values():
        info = (page.get("imageinfo") or [{}])[0]
        metadata = info.get("extmetadata", {})
        direct = info.get("url")
        if not direct:
            continue
        license_name = metadata.get("LicenseShortName", {}).get("value", "")
        license_url = metadata.get("LicenseUrl", {}).get("value")
        creator = metadata.get("Artist", {}).get("value")
        if creator:
            creator = re.sub("<[^>]+>", "", creator).strip()
        results.append(
            MusicResult(
                id=str(page.get("pageid")),
                title=str(page.get("title", "")).removeprefix("File:"),
                creator=creator,
                provider="wikimedia",
                license=normalize_license(license_name),
                license_url=license_url,
                landing_url=info.get("descriptionurl") or direct,
                download_url=direct,
                filetype=(info.get("mime") or "").split("/")[-1] or None,
            )
        )
    return results[:limit]


def search_music(query: str, provider: str = "openverse", limit: int = 12) -> list[MusicResult]:
    if provider == "openverse":
        return search_openverse(query, limit)
    if provider == "wikimedia":
        return search_wikimedia(query, limit)
    raise ValueError(f"unsupported music provider: {provider}")


def write_search_manifest(
    path: Path, query: str, provider: str, results: list[MusicResult]
) -> None:
    payload = {
        "schema_version": 1,
        "query": query,
        "provider": provider,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "results": [asdict(item) for item in results],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _safe_name(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip("-.")
    return value[:100] or "track"


def download_from_manifest(
    manifest_path: Path,
    result_id: str,
    output_dir: Path,
    allowed_licenses: set[str] | None = None,
) -> tuple[Path, Path]:
    allowed = allowed_licenses or DEFAULT_ALLOWED_LICENSES
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    selected = next((item for item in manifest.get("results", []) if str(item["id"]) == result_id), None)
    if selected is None:
        raise KeyError(f"result id not found: {result_id}")
    license_id = normalize_license(selected.get("license"))
    if license_id not in allowed:
        raise PermissionError(
            f"license '{license_id or 'unknown'}' is not in the download allowlist: {sorted(allowed)}"
        )
    url = selected["download_url"]
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("download URL must use http or https")
    suffix = Path(parsed.path).suffix.lower()
    if not suffix or len(suffix) > 8:
        suffix = "." + (selected.get("filetype") or "audio")
    output_dir.mkdir(parents=True, exist_ok=True)
    destination = output_dir / f"{_safe_name(selected['provider'] + '-' + result_id + '-' + selected['title'])}{suffix}"
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "RouteFilm/0.1 (+https://github.com/jiulongche/routefilm)"},
    )
    digest = hashlib.sha256()
    total = 0
    with urllib.request.urlopen(request, timeout=120) as response, destination.open("wb") as target:
        advertised = int(response.headers.get("Content-Length", "0") or 0)
        if advertised > MAX_DOWNLOAD_BYTES:
            raise ValueError("audio file exceeds 200 MiB safety limit")
        while chunk := response.read(1024 * 1024):
            total += len(chunk)
            if total > MAX_DOWNLOAD_BYTES:
                raise ValueError("audio file exceeds 200 MiB safety limit")
            target.write(chunk)
            digest.update(chunk)
    record = {
        **selected,
        "downloaded_at": datetime.now(timezone.utc).isoformat(),
        "sha256": digest.hexdigest(),
        "bytes": total,
        "manifest": str(manifest_path),
        "notice": "Verify attribution and the current source license before publication.",
    }
    sidecar = destination.with_suffix(destination.suffix + ".license.json")
    sidecar.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    return destination, sidecar


def decode_audio(path: Path, sample_rate: int = 22050, channels: int = 1) -> np.ndarray:
    command = [
        "ffmpeg", "-v", "error", "-i", str(path), "-f", "f32le", "-acodec", "pcm_f32le",
        "-ac", str(channels), "-ar", str(sample_rate), "-",
    ]
    completed = subprocess.run(command, check=True, stdout=subprocess.PIPE)
    data = np.frombuffer(completed.stdout, dtype=np.float32)
    return data if channels == 1 else data.reshape(-1, channels)


def analyze_pcm(audio: np.ndarray, sample_rate: int) -> dict[str, Any]:
    if audio.ndim > 1:
        audio = audio.mean(axis=1)
    frame, hop = 2048, 512
    if len(audio) < frame * 2:
        return {"duration_seconds": len(audio) / sample_rate, "bpm": None, "beats": []}
    window = np.hanning(frame).astype(np.float32)
    spectra = []
    for start in range(0, len(audio) - frame, hop):
        spectra.append(np.abs(np.fft.rfft(audio[start:start + frame] * window)))
    spectra_array = np.asarray(spectra)
    flux = np.maximum(0, np.diff(spectra_array, axis=0)).sum(axis=1)
    flux = (flux - flux.mean()) / (flux.std() + 1e-9)
    seconds_per_frame = hop / sample_rate
    min_lag = max(1, round(60 / 180 / seconds_per_frame))
    max_lag = min(len(flux) - 1, round(60 / 60 / seconds_per_frame))
    correlations = [float(np.dot(flux[:-lag], flux[lag:])) for lag in range(min_lag, max_lag + 1)]
    best_lag = min_lag + int(np.argmax(correlations))
    bpm = 60.0 / (best_lag * seconds_per_frame)
    if bpm < 90:
        bpm *= 2
    threshold = max(0.5, float(np.percentile(flux, 82)))
    peaks = [
        index for index in range(1, len(flux) - 1)
        if flux[index] > threshold and flux[index] >= flux[index - 1] and flux[index] > flux[index + 1]
    ]
    min_gap = max(1, round(0.20 / seconds_per_frame))
    filtered: list[int] = []
    for peak in peaks:
        if not filtered or peak - filtered[-1] >= min_gap:
            filtered.append(peak)
        elif flux[peak] > flux[filtered[-1]]:
            filtered[-1] = peak
    return {
        "duration_seconds": round(len(audio) / sample_rate, 3),
        "bpm": round(bpm, 2),
        "beats": [round((index + 1) * seconds_per_frame, 3) for index in filtered],
    }


def analyze_audio(path: Path, output: Path | None = None) -> dict[str, Any]:
    analysis = analyze_pcm(decode_audio(path), 22050)
    analysis["source"] = str(path)
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(analysis, indent=2), encoding="utf-8")
    return analysis


def _read_stereo(path: Path, sample_rate: int) -> np.ndarray:
    return decode_audio(path, sample_rate=sample_rate, channels=2)


def _accent(audio: np.ndarray, frame: int, sample_rate: int, major: bool) -> None:
    length = min(round((0.42 if major else 0.25) * sample_rate), len(audio) - frame)
    if length <= 0:
        return
    t = np.arange(length, dtype=np.float32) / sample_rate
    hit = np.sin(2 * math.pi * (98 * t - 55 * t * t)) * np.exp(-15 * t) * (0.18 if major else 0.10)
    hit += np.sin(2 * math.pi * 1150 * t) * np.exp(-48 * t) * (0.04 if major else 0.02)
    audio[frame:frame + length] += hit[:, None]


def mix_plan(plan_path: Path, output: Path) -> Path:
    plan = yaml.safe_load(plan_path.read_text(encoding="utf-8"))
    base = plan_path.parent
    sample_rate = int(plan.get("sample_rate", 48000))
    duration = float(plan["duration_seconds"])
    crossfade = float(plan.get("crossfade_seconds", 1.8))
    target = np.zeros((round(duration * sample_rate), 2), dtype=np.float32)
    tracks = {name: _read_stereo((base / value).resolve(), sample_rate) for name, value in plan["tracks"].items()}
    regions = plan["regions"]
    half_fade = crossfade / 2
    for index, region in enumerate(regions):
        start, end = float(region["start"]), float(region["end"])
        insert_start = max(0.0, start - (half_fade if index else 0.0))
        insert_end = min(duration, end + (half_fade if index < len(regions) - 1 else 0.0))
        needed = round((insert_end - insert_start) * sample_rate)
        source_start = round(max(0.0, float(region.get("offset", 0.0)) - (start - insert_start)) * sample_rate)
        clip = tracks[region["track"]][source_start:source_start + needed].copy()
        if len(clip) < needed:
            clip = np.pad(clip, ((0, needed - len(clip)), (0, 0)))
        clip *= 10 ** (float(region.get("gain_db", 0.0)) / 20)
        envelope = np.ones(needed, dtype=np.float32)
        overlap = min(round(crossfade * sample_rate), needed)
        if index and overlap:
            envelope[:overlap] = np.sin(np.linspace(0, math.pi / 2, overlap, dtype=np.float32))
        if index < len(regions) - 1 and overlap:
            envelope[-overlap:] = np.cos(np.linspace(0, math.pi / 2, overlap, dtype=np.float32))
        a, b = round(insert_start * sample_rate), round(insert_end * sample_rate)
        target[a:b] += clip[: b - a] * envelope[: b - a, None]
    for event in plan.get("accents", []):
        _accent(target, round(float(event["time"]) * sample_rate), sample_rate, bool(event.get("major")))
    fade_in = min(len(target), round(float(plan.get("fade_in_seconds", 1.2)) * sample_rate))
    fade_out = min(len(target), round(float(plan.get("fade_out_seconds", 4.2)) * sample_rate))
    target[:fade_in] *= np.linspace(0, 1, fade_in, dtype=np.float32)[:, None]
    target[-fade_out:] *= np.linspace(1, 0, fade_out, dtype=np.float32)[:, None]
    peak = float(np.max(np.abs(target)))
    if peak > 0.96:
        target *= 0.96 / peak
    output.parent.mkdir(parents=True, exist_ok=True)
    pcm = (np.clip(target, -1, 1) * 32767).astype("<i2")
    with wave.open(str(output), "wb") as stream:
        stream.setnchannels(2)
        stream.setsampwidth(2)
        stream.setframerate(sample_rate)
        stream.writeframes(pcm.tobytes())
    return output


def mux_audio(video: Path, audio: Path, output: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "ffmpeg", "-y", "-v", "error", "-i", str(video), "-i", str(audio),
            "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac",
            "-b:a", "256k", "-shortest", "-movflags", "+faststart", str(output),
        ],
        check=True,
    )
    return output
