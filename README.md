# opdscli

A CLI tool for browsing, searching, and downloading ebooks from [OPDS 1.x](https://opds-spec.org/) catalogs.

## Features

- **Search** catalogs using server-side OpenSearch or local crawling fallback
- **Download** books by title with format preference and progress bar
- **Browse** latest additions to any catalog
- **Manage** multiple catalogs with per-catalog authentication (Basic Auth, Bearer tokens)
- **Rich output** with formatted tables and progress bars
- **Single binary** distribution via PyInstaller

## Installation

### Homebrew (recommended)

```bash
brew tap rafadc/opdscli
brew install opdscli
```

### From source

Requires Python 3.12+ and [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/rafadc/opdscli.git
cd opdscli
uv sync
```

### Standalone binary

Build a self-contained binary:

```bash
uv sync
uv run pyinstaller --noconfirm opdscli.spec
# Binary is at dist/opdscli
```

## Quick start

```bash
# Add the Project Gutenberg catalog
opdscli catalog add gutenberg https://m.gutenberg.org/ebooks.opds/

# Search for Don Quixote
opdscli search "don quixote"

# Download it in plain text
opdscli download "Don Quixote" --format txt

# Browse latest additions
opdscli latest
```

## Usage

### Global flags

| Flag | Short | Description |
|------|-------|-------------|
| `--verbose` | `-v` | Show HTTP requests and parsing details |
| `--quiet` | `-q` | Suppress all output except errors and data |
| `--catalog` | `-c` | Override the default catalog for this command |
| `--version` | | Print version and exit |

### Managing catalogs

```bash
# Add a public catalog
opdscli catalog add mylib https://example.com/opds

# Add a catalog with Basic Auth (prompts for credentials)
opdscli catalog add private https://private.example.com/opds --auth-type basic

# Add a catalog with Bearer token auth
opdscli catalog add tokenlib https://token.example.com/opds --auth-type bearer

# List all catalogs
opdscli catalog list

# Set the default catalog
opdscli catalog set-default mylib

# Remove a catalog
opdscli catalog remove oldlib
```

### Searching

```bash
# Search the default catalog
opdscli search "science fiction"

# Search a specific catalog
opdscli search "python programming" --catalog mylib

# Increase crawl depth for local search (default: 3)
opdscli search "rare book" --depth 5
```

The search command tries server-side OpenSearch first. If the catalog doesn't support it, it crawls the feed structure locally, matching against title, author, and description fields.

### Downloading

```bash
# Download by exact title (case-insensitive)
opdscli download "The Great Adventure"

# Specify format (default: epub)
opdscli download "The Great Adventure" --format pdf

# Specify output directory
opdscli download "The Great Adventure" --output ~/Books

# Download from a specific catalog
opdscli download "The Great Adventure" --catalog mylib
```

If no exact match is found, the tool shows up to 5 fuzzy suggestions from the catalog.

### Browsing latest

```bash
# Show 20 latest additions (default)
opdscli latest

# Show more entries
opdscli latest --limit 50

# From a specific catalog
opdscli latest --catalog mylib
```

## Configuration

Config is stored at `~/.config/opdscli.yaml`:

```yaml
default_catalog: mylib
catalogs:
  mylib:
    url: https://my-library.example.com/opds
    auth:
      type: basic
      username: user
      password: pass
  tokenlib:
    url: https://token.example.com/opds
    auth:
      type: bearer
      token: abc123
  public:
    url: https://public.example.com/opds
settings:
  default_format: epub
```

Credentials are stored in plaintext. The CLI sets restrictive file permissions (`600`) and warns if the file is world-readable.

## Supported formats

| Format | MIME type |
|--------|-----------|
| EPUB | `application/epub+zip` |
| PDF | `application/pdf` |
| MOBI | `application/x-mobipocket-ebook` |
| CBZ | `application/x-cbz` |
| CBR | `application/x-cbr` |

## Development

### Setup

```bash
git clone https://github.com/rafadc/opdscli.git
cd opdscli
uv sync
```

### Running

```bash
# Via uv
uv run opdscli --help

# Or as a module
uv run python -m opdscli --help
```

### Testing

```bash
uv run pytest
```

49 tests covering OPDS parsing, config management, HTTP client behavior, and CLI commands end-to-end (with mocked HTTP via respx).

### Linting and type checking

```bash
uv run ruff check src/ tests/
uv run mypy src/
```

### Project structure

```
src/opdscli/
├── __init__.py         # Version
├── __main__.py         # Entry point
├── cli.py              # Typer app, global flags, command registration
├── config.py           # YAML config load/save, permission checks
├── http.py             # httpx client with auth and retry-once
├── opds.py             # OPDS 1.x Atom/XML parser, OpenSearch, crawler
└── commands/
    ├── catalog.py      # add, remove, list, set-default
    ├── search.py       # OpenSearch + local crawl fallback
    ├── latest.py       # Latest entries sorted by date
    └── download.py     # Exact match, fuzzy suggestions, progress bar
```

### Tech stack

| Component | Library |
|-----------|---------|
| CLI framework | [Typer](https://typer.tiangolo.com/) |
| Terminal output | [Rich](https://rich.readthedocs.io/) |
| HTTP client | [httpx](https://www.python-httpx.org/) |
| XML parsing | [lxml](https://lxml.de/) |
| Config | [PyYAML](https://pyyaml.org/) |
| Fuzzy matching | [thefuzz](https://github.com/seatgeek/thefuzz) |
| Packaging | [PyInstaller](https://pyinstaller.org/) |
