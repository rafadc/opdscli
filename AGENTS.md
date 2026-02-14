# opdscli

A CLI tool to interact with OPDS 1.x (Atom/XML) catalogs for browsing, searching, and downloading ebooks.

## Configuration

Catalogs are stored in `~/.config/opdscli.yaml`. The config file format:

```yaml
default_catalog: mylib
catalogs:
  mylib:
    url: https://my-library.example.com/opds
    auth:
      type: basic  # or "bearer"
      username: user  # for basic auth
      password: pass  # for basic auth
      token: abc123   # for bearer auth
  public:
    url: https://public-opds.example.com/feed
settings:
  default_format: epub  # preferred download format
```

Credentials are stored in plaintext. The CLI should warn the user if the config file has overly permissive permissions (e.g., world-readable) and recommend `chmod 600`.

## Commands

### `opdscli catalog add <name> <url> [--auth-type basic|bearer]`

Add a new catalog to the config. Prompts for credentials interactively if `--auth-type` is specified.

### `opdscli catalog remove <name>`

Remove a catalog from the config.

### `opdscli catalog list`

List all configured catalogs, marking the default.

### `opdscli catalog set-default <name>`

Set the default catalog.

### `opdscli search <query> [--catalog <name>] [--depth <n>]`

Search for books matching the query in the title, author, or description fields.

- **Server-side first**: Uses the OPDS OpenSearch endpoint if the catalog supports it.
- **Fallback to local crawling**: If OpenSearch is not available, crawls the feed structure and filters client-side.
- **Crawl depth**: When crawling locally, follows navigation links up to 3 levels deep by default. Override with `--depth`.
- **Output**: Rich-formatted table with columns: Title, Author, Format.
- **Catalog selection**: Uses the default catalog unless `--catalog` is specified.

### `opdscli download <title> [--catalog <name>] [--format <fmt>] [--output <path>]`

Download a book by exact title match.

- **Exact match**: Searches the catalog for a book whose title matches the argument exactly (case-insensitive).
- **No match behavior**: If no exact match is found, prints an error and shows up to 5 fuzzy suggestions from the catalog.
- **Format preference**: Downloads EPUB by default. Override with `--format` (e.g., `pdf`, `mobi`). A default format can also be set in config under `settings.default_format`.
- **Download location**: Saves to the current working directory by default. Override with `--output`.
- **Progress bar**: Shows a Rich progress bar during download.
- **Filename**: Uses `<title>.<format>` as the filename, sanitized for filesystem safety.

### `opdscli latest [--catalog <name>] [--limit <n>]`

Show the latest additions to the catalog.

- **Default count**: Shows 20 entries by default. Override with `--limit`.
- **Output**: Rich-formatted table with columns: Title, Author, Format.
- **Data source**: Reads from the catalog's acquisition feed sorted by newest.

## Global Flags

- `--verbose` / `-v`: Increase output verbosity (show HTTP requests, parsing details).
- `--quiet` / `-q`: Suppress all output except errors and requested data.
- `--version`: Print version and exit.
- `--catalog <name>`: Override the default catalog for any command.

## OPDS 1.x Details

- Parse Atom/XML feeds using standard XML parsing.
- Support navigation feeds (links with `rel="subsection"` or similar) for catalog browsing.
- Support acquisition feeds for book entries.
- Extract OpenSearch description documents for server-side search when available.
- Handle pagination via `rel="next"` links when crawling.

## Authentication

- **HTTP Basic Auth**: Send credentials with each request.
- **Bearer Token (OAuth)**: Send `Authorization: Bearer <token>` header.
- Auth type and credentials are per-catalog in the config file.
- Public (no-auth) catalogs are supported by omitting the `auth` section.

## Error Handling

- **Network errors**: Retry once with backoff, then fail with a clear error message and exit code 1.
- **Invalid OPDS feed**: Print a descriptive error identifying what's wrong (not valid XML, missing required elements, etc.).
- **Auth failures (401/403)**: Print a clear message suggesting the user check their credentials.
- **Missing config**: On first run with no config, print instructions for setting up a catalog.

## Technical Details

### Technology Stack

- **Language**: Python 3.12
- **Package manager**: uv (use `uv sync`, not pip)
- **CLI framework**: Typer
- **Output formatting**: Rich (tables and progress bars)
- **XML parsing**: lxml or defusedxml for OPDS feed parsing
- **HTTP client**: httpx (async-capable, modern alternative to requests)
- **Config**: PyYAML for config file handling
- **Fuzzy matching**: thefuzz (for download title suggestions)
- **Linting**: ruff
- **Type checking**: mypy
- **Testing**: pytest with fixtures and mocked HTTP (using respx or pytest-httpx)

### Distribution

- **Single binary**: Built with PyInstaller.
- **Homebrew**: Distributable via a Homebrew tap formula.

### Testing Strategy

- Use sample OPDS XML fixtures for parsing tests.
- Mock HTTP requests (no live server needed for tests).
- Test CLI commands via Typer's test runner (CliRunner).
- Cover: OPDS parsing, search (server-side and local), download, config management, error handling.

## Open Questions

- None at this time. All major decisions have been made.
