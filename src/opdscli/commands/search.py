from __future__ import annotations

from typing import TYPE_CHECKING

import typer
from rich.console import Console
from rich.table import Table

from opdscli.config import load_config
from opdscli.http import create_client
from opdscli.opds import crawl_entries, detect_opensearch, perform_opensearch

if TYPE_CHECKING:
    from opdscli.cli import State

console = Console()
err_console = Console(stderr=True)

_NO_CATALOG_MSG = (
    "[red]No catalog specified or default set. "
    "Use --catalog or set a default.[/red]"
)


def _get_state() -> State:
    from opdscli.cli import state

    return state


def search(
    query: str = typer.Argument(help="Search query."),
    catalog: str | None = typer.Option(
        None, "--catalog", "-c", help="Catalog to search.",
    ),
    depth: int = typer.Option(
        3, "--depth", "-d",
        help="Max crawl depth for local search.",
    ),
) -> None:
    """Search for books in a catalog."""
    st = _get_state()
    config = load_config()
    catalog_name = catalog or st.catalog or config.default_catalog
    if not catalog_name or catalog_name not in config.catalogs:
        err_console.print(_NO_CATALOG_MSG)
        raise typer.Exit(code=1)

    cat = config.catalogs[catalog_name]
    client = create_client(cat)

    if st.verbose:
        err_console.print(
            f"Searching catalog '{catalog_name}' for '{query}'...",
        )

    # Try server-side OpenSearch first
    opensearch_url = detect_opensearch(client, cat.url)
    if opensearch_url:
        if st.verbose:
            err_console.print("Using server-side OpenSearch.")
        entries = perform_opensearch(client, opensearch_url, query)
    else:
        if st.verbose:
            err_console.print(
                f"No OpenSearch. Crawling locally (depth={depth}).",
            )
        all_entries = crawl_entries(client, cat.url, max_depth=depth)
        query_lower = query.lower()
        entries = [
            e
            for e in all_entries
            if query_lower in e.title.lower()
            or query_lower in e.author.lower()
            or query_lower in e.summary.lower()
        ]

    if not entries:
        console.print("No results found.")
        return

    table = Table(title=f"Search results for '{query}'")
    table.add_column("Title")
    table.add_column("Author")
    table.add_column("Format")

    for entry in entries:
        formats = ", ".join(entry.formats) if entry.formats else "unknown"
        table.add_row(entry.title, entry.author, formats)

    console.print(table)
