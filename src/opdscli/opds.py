from dataclasses import dataclass, field
from urllib.parse import quote, urljoin

import httpx
from lxml import etree

from opdscli.http import OPDSClientError, fetch_url

ATOM_NS = "http://www.w3.org/2005/Atom"
OPDS_NS = "http://opds-spec.org/2010/catalog"
OPENSEARCH_NS = "http://a9.com/-/spec/opensearch/1.1/"
DC_NS = "http://purl.org/dc/terms/"

NS = {
    "atom": ATOM_NS,
    "opds": OPDS_NS,
    "opensearch": OPENSEARCH_NS,
    "dc": DC_NS,
}

ACQUISITION_REL_PREFIX = "http://opds-spec.org/acquisition"

_SORT_NEW = "http://opds-spec.org/sort/new"
_SORT_POPULAR = "http://opds-spec.org/sort/popular"


@dataclass
class AcquisitionLink:
    href: str
    type: str
    rel: str = ""


@dataclass
class OPDSEntry:
    title: str = ""
    author: str = ""
    summary: str = ""
    updated: str = ""
    entry_id: str = ""
    formats: list[str] = field(default_factory=list)
    acquisition_links: list[AcquisitionLink] = field(
        default_factory=list,
    )


@dataclass
class NavigationLink:
    href: str
    title: str = ""
    rel: str = ""


FORMAT_MAP: dict[str, str] = {
    "application/epub+zip": "epub",
    "application/pdf": "pdf",
    "application/x-mobipocket-ebook": "mobi",
    "application/x-cbz": "cbz",
    "application/x-cbr": "cbr",
    "text/html": "html",
}


def _text(element: etree._Element | None) -> str:
    if element is None:
        return ""
    return (element.text or "").strip()


def _resolve_url(base_url: str, href: str) -> str:
    return urljoin(base_url, href)


def _is_feed_link(rel: str, link_type: str) -> bool:
    """Check if a link points to another OPDS feed."""
    return bool(
        "navigation" in link_type
        or "acquisition" in link_type
        or rel in ("subsection", _SORT_NEW, _SORT_POPULAR)
        or "kind=navigation" in link_type
        or "kind=acquisition" in link_type
        or "profile=opds-catalog" in link_type
        or link_type.startswith("application/atom+xml")
    )


ParseResult = tuple[
    list[OPDSEntry], list[NavigationLink], str | None,
]


def parse_feed(
    xml_text: str, base_url: str = "",
) -> ParseResult:
    """Parse an OPDS Atom feed.

    Returns (entries, navigation_links, next_page_url).
    """
    try:
        root = etree.fromstring(xml_text.encode("utf-8"))
    except etree.XMLSyntaxError as e:
        raise ValueError(f"Invalid XML: {e}") from e

    entries: list[OPDSEntry] = []
    nav_links: list[NavigationLink] = []
    next_url: str | None = None

    for entry_el in root.findall("atom:entry", NS):
        entry = _parse_entry(entry_el, base_url)

        if entry.acquisition_links:
            entries.append(entry)
        else:
            for link_el in entry_el.findall("atom:link", NS):
                rel = link_el.get("rel", "")
                link_type = link_el.get("type", "")
                href = link_el.get("href", "")
                if href and _is_feed_link(rel, link_type):
                    nav_links.append(NavigationLink(
                        href=_resolve_url(base_url, href),
                        title=entry.title,
                        rel=rel,
                    ))

    for link_el in root.findall("atom:link", NS):
        rel = link_el.get("rel", "")
        href = link_el.get("href", "")
        if rel == "next" and href:
            next_url = _resolve_url(base_url, href)

    return entries, nav_links, next_url


def _parse_entry(
    entry_el: etree._Element, base_url: str,
) -> OPDSEntry:
    """Parse a single Atom entry element."""
    title = _text(entry_el.find("atom:title", NS))
    entry_id = _text(entry_el.find("atom:id", NS))
    updated = _text(entry_el.find("atom:updated", NS))

    authors = []
    for author_el in entry_el.findall("atom:author", NS):
        name = _text(author_el.find("atom:name", NS))
        if name:
            authors.append(name)
    author = ", ".join(authors)

    summary = _text(entry_el.find("atom:summary", NS))
    if not summary:
        summary = _text(entry_el.find("atom:content", NS))

    acq_links: list[AcquisitionLink] = []
    formats: list[str] = []
    for link_el in entry_el.findall("atom:link", NS):
        rel = link_el.get("rel", "")
        if rel.startswith(ACQUISITION_REL_PREFIX) or rel == "":
            link_type = link_el.get("type", "")
            href = link_el.get("href", "")
            if href and link_type and any(
                mime in link_type for mime in FORMAT_MAP
            ):
                acq_links.append(AcquisitionLink(
                    href=_resolve_url(base_url, href),
                    type=link_type,
                    rel=rel,
                ))
                fmt = FORMAT_MAP.get(link_type, link_type)
                if fmt not in formats:
                    formats.append(fmt)

    return OPDSEntry(
        title=title,
        author=author,
        summary=summary,
        updated=updated,
        entry_id=entry_id,
        formats=formats,
        acquisition_links=acq_links,
    )


def detect_opensearch(
    client: httpx.Client, feed_url: str,
) -> str | None:
    """Detect if the feed has an OpenSearch endpoint."""
    try:
        xml_text = fetch_url(client, feed_url)
    except OPDSClientError:
        return None
    try:
        root = etree.fromstring(xml_text.encode("utf-8"))
    except etree.XMLSyntaxError:
        return None

    for link_el in root.findall("atom:link", NS):
        rel = link_el.get("rel", "")
        link_type = link_el.get("type", "")
        href = link_el.get("href", "")
        if (
            rel == "search"
            and "opensearchdescription" in link_type
            and href
        ):
            desc_url = _resolve_url(feed_url, href)
            try:
                return _parse_opensearch_description(
                    client, desc_url,
                )
            except OPDSClientError:
                return None

    return None


def _parse_opensearch_description(
    client: httpx.Client, desc_url: str,
) -> str | None:
    """Parse an OpenSearch description document."""
    xml_text = fetch_url(client, desc_url)
    try:
        root = etree.fromstring(xml_text.encode("utf-8"))
    except etree.XMLSyntaxError:
        return None

    url_el = root.find("opensearch:Url", NS)
    if url_el is None:
        url_el = root.find(
            "{http://a9.com/-/spec/opensearch/1.1/}Url",
        )
    if url_el is None:
        url_el = root.find("Url")

    if url_el is not None:
        template = url_el.get("template", "")
        if template:
            return template

    return None


def perform_opensearch(
    client: httpx.Client,
    url_template: str,
    query: str,
) -> list[OPDSEntry]:
    """Perform an OpenSearch query."""
    search_url = url_template.replace(
        "{searchTerms}", quote(query, safe=""),
    )
    xml_text = fetch_url(client, search_url)
    entries, _, _ = parse_feed(xml_text, base_url=search_url)
    return entries


def fetch_entries(
    client: httpx.Client, feed_url: str,
) -> list[OPDSEntry]:
    """Fetch all entries from a single feed page."""
    xml_text = fetch_url(client, feed_url)
    entries, _, _ = parse_feed(xml_text, base_url=feed_url)
    return entries


def crawl_entries(
    client: httpx.Client,
    feed_url: str,
    max_depth: int = 3,
) -> list[OPDSEntry]:
    """Crawl an OPDS feed recursively."""
    all_entries: list[OPDSEntry] = []
    visited: set[str] = set()

    def _crawl(url: str, depth: int) -> None:
        if depth > max_depth or url in visited:
            return
        visited.add(url)

        xml_text = fetch_url(client, url)
        entries, nav_links, next_url = parse_feed(
            xml_text, base_url=url,
        )

        all_entries.extend(entries)

        for nav in nav_links:
            _crawl(nav.href, depth + 1)

        if next_url:
            _crawl(next_url, depth)

    _crawl(feed_url, 0)
    return all_entries
