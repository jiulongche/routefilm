"""Safe, non-executing dotenv discovery for optional image generation."""

from __future__ import annotations

import os
import stat
from pathlib import Path
from urllib.parse import urlparse

from dotenv import dotenv_values, set_key

URL_KEY = "ROUTEFILM_IMAGE_BASE_URL"
API_KEY_NAMES = ("ROUTEFILM_IMAGE_API_KEY", "OPENAI_API_KEY")


def user_image_config_path(home: Path | None = None) -> Path:
    if home is not None:
        root = home / ".config"
    else:
        root = (
            Path(os.environ["XDG_CONFIG_HOME"])
            if os.getenv("XDG_CONFIG_HOME")
            else Path.home() / ".config"
        )
    return root.expanduser() / "routefilm" / ".env"


def _config_paths(cwd: Path | None = None, home: Path | None = None) -> list[Path]:
    explicit = os.getenv("ROUTEFILM_ENV_FILE")
    if explicit:
        return [Path(explicit).expanduser()]
    start = (cwd or Path.cwd()).resolve()
    project = ""
    for directory in (start, *start.parents):
        candidate = directory / ".env"
        if candidate.is_file():
            project = str(candidate)
            break
    paths = [Path(project)] if project else []
    user_path = user_image_config_path(home)
    if user_path not in paths:
        paths.append(user_path)
    return paths


def resolve_image_credentials(
    *,
    base_url: str | None = None,
    api_key: str | None = None,
    cwd: Path | None = None,
    home: Path | None = None,
) -> tuple[str | None, str | None]:
    """Resolve arguments, process environment, then dotenv files without mutating os.environ."""
    endpoint = base_url or os.getenv(URL_KEY)
    key = api_key or os.getenv(API_KEY_NAMES[0]) or os.getenv(API_KEY_NAMES[1])
    if endpoint and key:
        return endpoint, key
    for path in _config_paths(cwd, home):
        if not path.is_file():
            continue
        values = dotenv_values(path)
        endpoint = endpoint or values.get(URL_KEY)
        key = key or values.get(API_KEY_NAMES[0]) or values.get(API_KEY_NAMES[1])
        if endpoint and key:
            break
    return endpoint, key


def image_config_path(
    scope: str, *, cwd: Path | None = None, home: Path | None = None
) -> Path:
    if scope == "project":
        return (cwd or Path.cwd()).resolve() / ".env"
    if scope == "user":
        return user_image_config_path(home)
    raise ValueError("scope must be project or user")


def configure_image_environment(
    base_url: str | None = None,
    *,
    scope: str = "user",
    cwd: Path | None = None,
    home: Path | None = None,
) -> Path:
    """Create or update a private dotenv file without accepting an API key argument."""
    endpoint = base_url or resolve_image_credentials(cwd=cwd, home=home)[0]
    if not endpoint:
        raise ValueError("image API base URL is missing; pass --base-url with an http(s) URL")
    parsed = urlparse(endpoint)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("image API base URL must be an absolute http(s) URL")
    if parsed.username or parsed.password:
        raise ValueError("image API credentials must not be embedded in the base URL")
    path = image_config_path(scope, cwd=cwd, home=home)
    if path.is_symlink():
        raise ValueError(f"refusing to update symlinked image config: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(
            "# RouteFilm local image configuration. Never commit this file.\n",
            encoding="utf-8",
        )
    current = dotenv_values(path)
    set_key(str(path), URL_KEY, endpoint.rstrip("/"), quote_mode="never")
    if not any(name in current for name in API_KEY_NAMES):
        set_key(str(path), API_KEY_NAMES[0], "", quote_mode="never")
    path.chmod(stat.S_IRUSR | stat.S_IWUSR)
    return path
