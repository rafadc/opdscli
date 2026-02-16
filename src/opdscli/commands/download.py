from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING

import typer
from rich.console import Console
from rich.progress import Progress
from thefuzz import fuzz  # type: ignore[import-untyped]

from opdscli.config import load_config
from opdscli.http import create_client, stream_download
from opdscli.opds import (
    OPDSEntry,
    crawl_entries,
    detect_opensearch,
    perform_opensearch,
)

if TYPE_CHECKING:
    from opdscli.cli import State

console = Console()
err_console = Console(stderr=True)

FORMAT_MIME_MAP: dict[str, str] = {
    "epub": "application/epub+zip",
    "pdf": "application/pdf",
    "mobi": "application/x-mobipocket-ebook",
}


def _get_state() -> State:
    from opdscli.cli import state

    return state


def sanitize_filename(name: str) -> str:
    return re.sub(r'[<>:"/\\|?*]', "_", name).strip(". ")


def find_download_link(
    entry: OPDSEntry, preferred_format: str,
) -> tuple[str | None, str]:
    """Find the best download link for the preferred format."""
    preferred_mime = FORMAT_MIME_MAP.get(
        preferred_format, preferred_format,
    )
    for link in entry.acquisition_links:
        if preferred_mime in link.type:
            return link.href, preferred_format
    # Fallback: return the first available acquisition link
    if entry.acquisition_links:
        link = entry.acquisition_links[0]
        fmt = next(
            (k for k, v in FORMAT_MIME_MAP.items() if v in link.type),
            "bin",
        )
        return link.href, fmt
    return None, preferred_format


def download(
    title: str = typer.Argument(
        help="Exact title of the book to download.",
    ),
    catalog: str | None = typer.Option(
        None, "--catalog", "-c", help="Catalog to search.",
    ),
    format: str | None = typer.Option(
        None, "--format", "-f",
        help="Preferred format (epub, pdf, mobi).",
    ),
    output: Path | None = typer.Option(
        None, "--output", "-o", help="Output directory.",
    ),
) -> None:
    """Download a book by exact title match."""
    st = _get_state()
    config = load_config()
    catalog_name = catalog or st.catalog or config.default_catalog
    if not catalog_name or catalog_name not in config.catalogs:
        err_console.print(
            "[red]No catalog specified or default set. "
            "Use --catalog or set a default.[/red]"
        )
        raise typer.Exit(code=1)

    cat = config.catalogs[catalog_name]
    client = create_client(cat)
    preferred_format = format or config.settings.get(
        "default_format", "epub",
    )

    if st.verbose:
        err_console.print(
            f"Searching catalog '{catalog_name}' for '{title}'...",
        )

    # Try OpenSearch first, fall back to crawling
    opensearch_url = detect_opensearch(client, cat.url)
    if opensearch_url:
        if st.verbose:
            err_console.print("Using server-side OpenSearch.")
        all_entries = perform_opensearch(
            client, opensearch_url, title,
        )
    else:
        if st.verbose:
            err_console.print("No OpenSearch. Crawling locally.")
        all_entries = crawl_entries(client, cat.url, max_depth=3)

    # Exact match (case-insensitive)
    match = next(
        (e for e in all_entries if e.title.lower() == title.lower()),
        None,
    )

    if not match:
        err_console.print(f"[red]Book '{title}' not found.[/red]")
        scored = [
            (e, fuzz.ratio(title.lower(), e.title.lower()))
            for e in all_entries
        ]
        scored.sort(key=lambda x: x[1], reverse=True)
        suggestions = [
            e for e, score in scored[:5] if score > 30
        ]
        if suggestions:
            err_console.print("\nDid you mean:")
            for s in suggestions:
                err_console.print(f"  - {s.title} ({s.author})")
        raise typer.Exit(code=1)

    download_url, fmt = find_download_link(match, preferred_format)
    if not download_url:
        err_console.print(
            f"[red]No downloadable format for '{match.title}'.[/red]",
        )
        raise typer.Exit(code=1)

    filename = f"{sanitize_filename(match.title)}.{fmt}"
    dest_dir = output or Path.cwd()
    dest_path = dest_dir / filename

    if st.verbose:
        err_console.print(f"Downloading {download_url} -> {dest_path}")

    with Progress(console=console) as progress:
        task = progress.add_task(
            f"Downloading {match.title}", total=None,
        )
        stream_download(client, download_url, dest_path, progress, task)

    if not st.quiet:
        console.print(f"Saved to {dest_path}")
