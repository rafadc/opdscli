from __future__ import annotations

from typing import TYPE_CHECKING

import typer
from rich.console import Console
from rich.table import Table

from opdscli.config import AuthConfig, CatalogConfig, load_config, save_config

if TYPE_CHECKING:
    from opdscli.cli import State

console = Console()
err_console = Console(stderr=True)


def _get_state() -> State:
    from opdscli.cli import state

    return state


def catalog_add(
    name: str = typer.Argument(help="Name for the catalog."),
    url: str = typer.Argument(help="OPDS feed URL."),
    auth_type: str | None = typer.Option(
        None, "--auth-type", help="Auth type: basic or bearer.",
    ),
) -> None:
    """Add a new catalog."""
    config = load_config()

    if name in config.catalogs:
        err_console.print(f"[red]Catalog '{name}' already exists.[/red]")
        raise typer.Exit(code=1)

    auth: AuthConfig | None = None
    if auth_type:
        if auth_type == "basic":
            username = typer.prompt("Username")
            password = typer.prompt("Password", hide_input=True)
            auth = AuthConfig(type="basic", username=username, password=password)
        elif auth_type == "bearer":
            token = typer.prompt("Bearer token", hide_input=True)
            auth = AuthConfig(type="bearer", token=token)
        else:
            msg = f"Unknown auth type '{auth_type}'. Use 'basic' or 'bearer'."
            err_console.print(f"[red]{msg}[/red]")
            raise typer.Exit(code=1)

    config.catalogs[name] = CatalogConfig(url=url, auth=auth)
    if config.default_catalog is None:
        config.default_catalog = name

    save_config(config)
    if not _get_state().quiet:
        console.print(f"Added catalog '{name}' ({url})")


def catalog_remove(
    name: str = typer.Argument(help="Name of the catalog to remove."),
) -> None:
    """Remove a catalog."""
    config = load_config()

    if name not in config.catalogs:
        err_console.print(f"[red]Catalog '{name}' not found.[/red]")
        raise typer.Exit(code=1)

    del config.catalogs[name]
    if config.default_catalog == name:
        config.default_catalog = next(iter(config.catalogs), None)

    save_config(config)
    if not _get_state().quiet:
        console.print(f"Removed catalog '{name}'")


def catalog_list() -> None:
    """List all configured catalogs."""
    config = load_config()

    if not config.catalogs:
        console.print("No catalogs configured. Use 'opdscli catalog add' to add one.")
        return

    table = Table(title="Catalogs")
    table.add_column("Name")
    table.add_column("URL")
    table.add_column("Auth")
    table.add_column("Default")

    for name, cat in config.catalogs.items():
        is_default = "*" if name == config.default_catalog else ""
        auth_str = cat.auth.type if cat.auth else "none"
        table.add_row(name, cat.url, auth_str, is_default)

    console.print(table)


def catalog_set_default(
    name: str = typer.Argument(help="Name of the catalog to set as default."),
) -> None:
    """Set the default catalog."""
    config = load_config()

    if name not in config.catalogs:
        err_console.print(f"[red]Catalog '{name}' not found.[/red]")
        raise typer.Exit(code=1)

    config.default_catalog = name
    save_config(config)
    if not _get_state().quiet:
        console.print(f"Default catalog set to '{name}'")


def register(catalog_app: typer.Typer) -> None:
    """Register all catalog subcommands."""
    catalog_app.command("add")(catalog_add)
    catalog_app.command("remove")(catalog_remove)
    catalog_app.command("list")(catalog_list)
    catalog_app.command("set-default")(catalog_set_default)
