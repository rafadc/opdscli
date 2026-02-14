import typer
from rich.console import Console

from opdscli import __version__

app = typer.Typer(
    help="A CLI tool to interact with OPDS 1.x ebook catalogs.",
)
catalog_app = typer.Typer(help="Manage OPDS catalogs.")
app.add_typer(catalog_app, name="catalog")

console = Console()
err_console = Console(stderr=True)


class State:
    verbose: bool = False
    quiet: bool = False
    catalog: str | None = None


state = State()


def version_callback(value: bool) -> None:
    if value:
        console.print(f"opdscli {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    verbose: bool = typer.Option(
        False, "--verbose", "-v",
        help="Increase output verbosity.",
    ),
    quiet: bool = typer.Option(
        False, "--quiet", "-q",
        help="Suppress non-essential output.",
    ),
    catalog: str | None = typer.Option(
        None, "--catalog", "-c",
        help="Override the default catalog.",
    ),
    version: bool | None = typer.Option(
        None, "--version",
        callback=version_callback,
        is_eager=True,
        help="Print version and exit.",
    ),
) -> None:
    state.verbose = verbose
    state.quiet = quiet
    state.catalog = catalog


def register_commands() -> None:
    """Register all commands with the app."""
    from opdscli.commands.catalog import (
        register as register_catalog,
    )
    from opdscli.commands.download import download
    from opdscli.commands.latest import latest
    from opdscli.commands.search import search

    register_catalog(catalog_app)
    app.command()(search)
    app.command()(latest)
    app.command()(download)


def main_entry() -> None:
    """Entry point for the console script."""
    register_commands()
    app()
