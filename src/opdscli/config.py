import os
import stat
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from rich.console import Console

CONFIG_PATH = Path.home() / ".config" / "opdscli.yaml"

err_console = Console(stderr=True)


@dataclass
class AuthConfig:
    type: str  # "basic" or "bearer"
    username: str | None = None
    password: str | None = None
    token: str | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"type": self.type}
        if self.username is not None:
            d["username"] = self.username
        if self.password is not None:
            d["password"] = self.password
        if self.token is not None:
            d["token"] = self.token
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AuthConfig":
        return cls(
            type=data.get("type", "basic"),
            username=data.get("username"),
            password=data.get("password"),
            token=data.get("token"),
        )


@dataclass
class CatalogConfig:
    url: str
    auth: AuthConfig | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"url": self.url}
        if self.auth is not None:
            d["auth"] = self.auth.to_dict()
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CatalogConfig":
        auth_data = data.get("auth")
        auth = AuthConfig.from_dict(auth_data) if auth_data else None
        return cls(url=data["url"], auth=auth)


@dataclass
class AppConfig:
    default_catalog: str | None = None
    catalogs: dict[str, CatalogConfig] = field(default_factory=dict)
    settings: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "default_catalog": self.default_catalog,
            "catalogs": {name: cat.to_dict() for name, cat in self.catalogs.items()},
            "settings": self.settings,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AppConfig":
        catalogs = {}
        for name, cat_data in data.get("catalogs", {}).items():
            catalogs[name] = CatalogConfig.from_dict(cat_data)
        return cls(
            default_catalog=data.get("default_catalog"),
            catalogs=catalogs,
            settings=data.get("settings", {}),
        )


def _check_permissions(path: Path) -> None:
    """Warn if the config file is world-readable."""
    try:
        mode = path.stat().st_mode
        if mode & stat.S_IROTH:
            err_console.print(
                f"[yellow]Warning: {path} is world-readable. "
                f"Run 'chmod 600 {path}' to restrict access.[/yellow]"
            )
    except OSError:
        pass


def load_config(path: Path | None = None) -> AppConfig:
    """Load config from YAML file. Returns empty config if file doesn't exist."""
    config_path = path or CONFIG_PATH

    if not config_path.exists():
        return AppConfig()

    _check_permissions(config_path)

    with open(config_path) as f:
        data = yaml.safe_load(f)

    if not data:
        return AppConfig()

    return AppConfig.from_dict(data)


def save_config(config: AppConfig, path: Path | None = None) -> None:
    """Save config to YAML file."""
    config_path = path or CONFIG_PATH
    config_path.parent.mkdir(parents=True, exist_ok=True)

    with open(config_path, "w") as f:
        yaml.dump(config.to_dict(), f, default_flow_style=False, sort_keys=False)

    # Set restrictive permissions on newly created files
    if sys.platform != "win32":
        os.chmod(config_path, stat.S_IRUSR | stat.S_IWUSR)
