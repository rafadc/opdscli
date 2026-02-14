import typer
from rich.console import Console
from rich.table import Table

from opdscli.config import load_config
from opdscli.http import OPDSClientError, create_client, fetch_url
from opdscli.opds import fetch_entries, parse_feed

console = Console()
err_console = Console(stderr=True)

_NO_CATALOG_MSG = (
    "[red]No catalog specified or default set. "
    "Use --catalog or set a default.[/red]"
)


def _get_state():  # type: ignore[no-untyped-def]
    from opdscli.cli import state

    return state


def latest(
    catalog: str | None = typer.Option(
        None, "--catalog", "-c", help="Catalog to browse.",
    ),
    limit: int = typer.Option(
        20, "--limit", "-l", help="Number of entries to show.",
    ),
) -> None:
    """Show latest additions to a catalog."""
    st = _get_state()
    config = load_config()
    catalog_name = catalog or st.catalog or config.default_catalog
    if not catalog_name or catalog_name not in config.catalogs:
        err_console.print(_NO_CATALOG_MSG)
        raise typer.Exit(code=1)

    cat = config.catalogs[catalog_name]
    client = create_client(cat)

    if st.verbose:
        err_console.print(f"Fetching latest from '{catalog_name}'...")

    # Look for a "latest" / "new" navigation link in the root feed
    feed_url = cat.url
    try:
        root_xml = fetch_url(client, feed_url)
        _, nav_links, _ = parse_feed(root_xml, base_url=feed_url)
        for nav in nav_links:
            title_lower = nav.title.lower()
            if (
                "latest" in title_lower
                or "new" in title_lower
                or "recent" in title_lower
                or nav.rel == "http://opds-spec.org/sort/new"
            ):
                feed_url = nav.href
                break
    except (OPDSClientError, ValueError):
        pass

    entries = fetch_entries(client, feed_url)
    entries.sort(key=lambda e: e.updated or "", reverse=True)
    entries = entries[:limit]

    if not entries:
        console.print("No entries found.")
        return

    table = Table(title="Latest additions")
    table.add_column("Title")
    table.add_column("Author")
    table.add_column("Format")

    for entry in entries:
        formats = ", ".join(entry.formats) if entry.formats else "unknown"
        table.add_row(entry.title, entry.author, formats)

    console.print(table)
