from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def fixtures_dir() -> Path:
    return FIXTURES_DIR


@pytest.fixture
def navigation_feed_xml(fixtures_dir: Path) -> str:
    return (fixtures_dir / "navigation_feed.xml").read_text()


@pytest.fixture
def acquisition_feed_xml(fixtures_dir: Path) -> str:
    return (fixtures_dir / "acquisition_feed.xml").read_text()


@pytest.fixture
def opensearch_xml(fixtures_dir: Path) -> str:
    return (fixtures_dir / "opensearch.xml").read_text()


@pytest.fixture
def empty_feed_xml(fixtures_dir: Path) -> str:
    return (fixtures_dir / "empty_feed.xml").read_text()


@pytest.fixture
def missing_fields_feed_xml(fixtures_dir: Path) -> str:
    return (fixtures_dir / "missing_fields_feed.xml").read_text()
