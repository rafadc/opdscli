import pytest

from opdscli.opds import parse_feed


class TestParseNavigationFeed:
    def test_extracts_navigation_links(self, navigation_feed_xml: str) -> None:
        entries, nav_links, next_url = parse_feed(navigation_feed_xml, base_url="https://example.com")
        assert len(nav_links) == 2
        assert nav_links[0].title == "Fiction"
        assert nav_links[0].href == "https://example.com/opds/fiction"
        assert nav_links[1].title == "Science"

    def test_no_book_entries_in_navigation_feed(self, navigation_feed_xml: str) -> None:
        entries, _, _ = parse_feed(navigation_feed_xml, base_url="https://example.com")
        assert len(entries) == 0

    def test_no_next_page(self, navigation_feed_xml: str) -> None:
        _, _, next_url = parse_feed(navigation_feed_xml, base_url="https://example.com")
        assert next_url is None


class TestParseAcquisitionFeed:
    def test_extracts_entries(self, acquisition_feed_xml: str) -> None:
        entries, _, _ = parse_feed(acquisition_feed_xml, base_url="https://example.com")
        assert len(entries) == 3

    def test_entry_title_and_author(self, acquisition_feed_xml: str) -> None:
        entries, _, _ = parse_feed(acquisition_feed_xml, base_url="https://example.com")
        assert entries[0].title == "The Great Adventure"
        assert entries[0].author == "Jane Author"

    def test_multiple_authors(self, acquisition_feed_xml: str) -> None:
        entries, _, _ = parse_feed(acquisition_feed_xml, base_url="https://example.com")
        assert entries[1].author == "John Writer, Alice Coauthor"

    def test_entry_formats(self, acquisition_feed_xml: str) -> None:
        entries, _, _ = parse_feed(acquisition_feed_xml, base_url="https://example.com")
        assert "epub" in entries[0].formats
        assert "pdf" in entries[0].formats
        assert entries[1].formats == ["epub"]
        assert "pdf" in entries[2].formats
        assert "mobi" in entries[2].formats

    def test_acquisition_links(self, acquisition_feed_xml: str) -> None:
        entries, _, _ = parse_feed(acquisition_feed_xml, base_url="https://example.com")
        assert len(entries[0].acquisition_links) == 2
        assert entries[0].acquisition_links[0].href == "https://example.com/download/book-001.epub"
        assert entries[0].acquisition_links[0].type == "application/epub+zip"

    def test_summary(self, acquisition_feed_xml: str) -> None:
        entries, _, _ = parse_feed(acquisition_feed_xml, base_url="https://example.com")
        assert entries[0].summary == "An exciting tale of adventure and discovery."

    def test_updated(self, acquisition_feed_xml: str) -> None:
        entries, _, _ = parse_feed(acquisition_feed_xml, base_url="https://example.com")
        assert entries[0].updated == "2024-01-15T10:00:00Z"

    def test_next_page_link(self, acquisition_feed_xml: str) -> None:
        _, _, next_url = parse_feed(acquisition_feed_xml, base_url="https://example.com")
        assert next_url == "https://example.com/opds/fiction?page=2"


class TestEmptyFeed:
    def test_no_entries(self, empty_feed_xml: str) -> None:
        entries, nav_links, next_url = parse_feed(empty_feed_xml)
        assert entries == []
        assert nav_links == []
        assert next_url is None


class TestMissingFieldsFeed:
    def test_missing_author(self, missing_fields_feed_xml: str) -> None:
        entries, _, _ = parse_feed(missing_fields_feed_xml, base_url="https://example.com")
        # Only the entry with acquisition links should be returned as a book entry
        assert len(entries) == 1
        assert entries[0].title == "No Author Book"
        assert entries[0].author == ""

    def test_entry_without_links_is_not_a_book(
        self, missing_fields_feed_xml: str,
    ) -> None:
        entries, _, _ = parse_feed(missing_fields_feed_xml, base_url="https://example.com")
        titles = [e.title for e in entries]
        assert "No Links Book" not in titles


class TestInvalidXml:
    def test_raises_on_invalid_xml(self) -> None:
        with pytest.raises(ValueError, match="Invalid XML"):
            parse_feed("<not valid xml")

    def test_url_resolution(self, acquisition_feed_xml: str) -> None:
        entries, _, _ = parse_feed(acquisition_feed_xml, base_url="https://example.com/opds/")
        assert entries[0].acquisition_links[0].href == "https://example.com/download/book-001.epub"
