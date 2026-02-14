from pathlib import Path
from unittest.mock import patch

import httpx
import respx
from typer.testing import CliRunner

from opdscli.cli import app, register_commands
from opdscli.config import AppConfig, CatalogConfig

runner = CliRunner()

# Register commands once for all tests
register_commands()

FIXTURES_DIR = Path(__file__).parent / "fixtures"

_TEST_CONFIG = AppConfig(
    default_catalog="test",
    catalogs={
        "test": CatalogConfig(url="https://example.com/opds"),
    },
)


def _test_config() -> AppConfig:
    return AppConfig(
        default_catalog="test",
        catalogs={
            "test": CatalogConfig(
                url="https://example.com/opds",
            ),
        },
    )


def _empty_xml() -> str:
    return (FIXTURES_DIR / "empty_feed.xml").read_text()


class TestVersionFlag:
    def test_version(self):
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "0.1.0" in result.output


class TestCatalogCommands:
    def test_catalog_add_and_list(self):
        with (
            patch(
                "opdscli.commands.catalog.load_config",
                lambda: AppConfig(),
            ),
            patch("opdscli.commands.catalog.save_config"),
        ):
            result = runner.invoke(
                app,
                ["catalog", "add", "mylib",
                 "https://example.com/opds"],
            )
            assert result.exit_code == 0
            assert "Added catalog" in result.output

    def test_catalog_add_duplicate(self):
        with patch(
            "opdscli.commands.catalog.load_config",
            _test_config,
        ):
            result = runner.invoke(
                app,
                ["catalog", "add", "test", "https://other.com"],
            )
            assert result.exit_code == 1

    def test_catalog_remove(self):
        with (
            patch(
                "opdscli.commands.catalog.load_config",
                _test_config,
            ),
            patch("opdscli.commands.catalog.save_config"),
        ):
            result = runner.invoke(
                app, ["catalog", "remove", "test"],
            )
            assert result.exit_code == 0
            assert "Removed" in result.output

    def test_catalog_remove_nonexistent(self):
        with patch(
            "opdscli.commands.catalog.load_config",
            lambda: AppConfig(),
        ):
            result = runner.invoke(
                app, ["catalog", "remove", "nope"],
            )
            assert result.exit_code == 1

    def test_catalog_list_empty(self):
        with patch(
            "opdscli.commands.catalog.load_config",
            lambda: AppConfig(),
        ):
            result = runner.invoke(app, ["catalog", "list"])
            assert result.exit_code == 0
            assert "No catalogs configured" in result.output

    def test_catalog_list_with_entries(self):
        with patch(
            "opdscli.commands.catalog.load_config",
            _test_config,
        ):
            result = runner.invoke(app, ["catalog", "list"])
            assert result.exit_code == 0
            assert "test" in result.output

    def test_catalog_set_default(self):
        def cfg():
            return AppConfig(catalogs={
                "a": CatalogConfig(url="https://a.com"),
                "b": CatalogConfig(url="https://b.com"),
            })

        with (
            patch(
                "opdscli.commands.catalog.load_config", cfg,
            ),
            patch("opdscli.commands.catalog.save_config"),
        ):
            result = runner.invoke(
                app, ["catalog", "set-default", "b"],
            )
            assert result.exit_code == 0
            assert "Default catalog set to 'b'" in result.output

    def test_catalog_set_default_nonexistent(self):
        with patch(
            "opdscli.commands.catalog.load_config",
            lambda: AppConfig(),
        ):
            result = runner.invoke(
                app, ["catalog", "set-default", "nope"],
            )
            assert result.exit_code == 1


class TestSearchCommand:
    @respx.mock
    def test_search_local_fallback(self):
        acq_xml = (
            FIXTURES_DIR / "acquisition_feed.xml"
        ).read_text()
        nav_xml = (
            FIXTURES_DIR / "navigation_feed.xml"
        ).read_text()
        respx.get("https://example.com/opds").mock(
            return_value=httpx.Response(200, text=nav_xml),
        )
        respx.get("https://example.com/opensearch.xml").mock(
            return_value=httpx.Response(404),
        )
        respx.get("https://example.com/opds/fiction").mock(
            return_value=httpx.Response(200, text=acq_xml),
        )
        respx.get("https://example.com/opds/science").mock(
            return_value=httpx.Response(200, text=acq_xml),
        )
        respx.get(
            "https://example.com/opds/fiction?page=2",
        ).mock(
            return_value=httpx.Response(
                200, text=_empty_xml(),
            ),
        )

        with patch(
            "opdscli.commands.search.load_config",
            _test_config,
        ):
            result = runner.invoke(
                app, ["search", "adventure"],
            )
            assert result.exit_code == 0
            assert "The Great Adventure" in result.output

    @respx.mock
    def test_search_no_results(self):
        respx.get("https://example.com/opds").mock(
            return_value=httpx.Response(
                200, text=_empty_xml(),
            ),
        )

        with patch(
            "opdscli.commands.search.load_config",
            _test_config,
        ):
            result = runner.invoke(
                app, ["search", "nonexistent"],
            )
            assert result.exit_code == 0
            assert "No results found" in result.output

    def test_search_no_catalog(self):
        with patch(
            "opdscli.commands.search.load_config",
            lambda: AppConfig(),
        ):
            result = runner.invoke(app, ["search", "test"])
            assert result.exit_code == 1


class TestLatestCommand:
    @respx.mock
    def test_latest_shows_entries(self):
        acq_xml = (
            FIXTURES_DIR / "acquisition_feed.xml"
        ).read_text()
        respx.get("https://example.com/opds").mock(
            return_value=httpx.Response(200, text=acq_xml),
        )

        with patch(
            "opdscli.commands.latest.load_config",
            _test_config,
        ):
            result = runner.invoke(app, ["latest"])
            assert result.exit_code == 0
            assert "The Great Adventure" in result.output
            assert "Mystery at Dawn" in result.output

    @respx.mock
    def test_latest_with_limit(self):
        acq_xml = (
            FIXTURES_DIR / "acquisition_feed.xml"
        ).read_text()
        respx.get("https://example.com/opds").mock(
            return_value=httpx.Response(200, text=acq_xml),
        )

        with patch(
            "opdscli.commands.latest.load_config",
            _test_config,
        ):
            result = runner.invoke(
                app, ["latest", "--limit", "1"],
            )
            assert result.exit_code == 0
            assert "The Great Adventure" in result.output

    @respx.mock
    def test_latest_empty(self):
        respx.get("https://example.com/opds").mock(
            return_value=httpx.Response(
                200, text=_empty_xml(),
            ),
        )

        with patch(
            "opdscli.commands.latest.load_config",
            _test_config,
        ):
            result = runner.invoke(app, ["latest"])
            assert result.exit_code == 0
            assert "No entries found" in result.output


class TestDownloadCommand:
    @respx.mock
    def test_download_exact_match(self, tmp_path):
        acq_xml = (
            FIXTURES_DIR / "acquisition_feed.xml"
        ).read_text()
        respx.get("https://example.com/opds").mock(
            return_value=httpx.Response(200, text=acq_xml),
        )
        respx.get(
            "https://example.com/opds/fiction?page=2",
        ).mock(
            return_value=httpx.Response(
                200, text=_empty_xml(),
            ),
        )
        respx.get(
            "https://example.com/download/book-001.epub",
        ).mock(
            return_value=httpx.Response(
                200, content=b"fake epub content",
            ),
        )

        with patch(
            "opdscli.commands.download.load_config",
            _test_config,
        ):
            result = runner.invoke(app, [
                "download", "The Great Adventure",
                "--output", str(tmp_path),
            ])
            assert result.exit_code == 0
            assert "Saved to" in result.output
            saved = tmp_path / "The Great Adventure.epub"
            assert saved.exists()

    @respx.mock
    def test_download_not_found_with_suggestions(self):
        acq_xml = (
            FIXTURES_DIR / "acquisition_feed.xml"
        ).read_text()
        respx.get("https://example.com/opds").mock(
            return_value=httpx.Response(200, text=acq_xml),
        )
        respx.get(
            "https://example.com/opds/fiction?page=2",
        ).mock(
            return_value=httpx.Response(
                200, text=_empty_xml(),
            ),
        )

        with patch(
            "opdscli.commands.download.load_config",
            _test_config,
        ):
            result = runner.invoke(
                app, ["download", "The Great Adventuree"],
            )
            assert result.exit_code == 1
            assert "not found" in result.output

    def test_download_no_catalog(self):
        with patch(
            "opdscli.commands.download.load_config",
            lambda: AppConfig(),
        ):
            result = runner.invoke(
                app, ["download", "test"],
            )
            assert result.exit_code == 1
