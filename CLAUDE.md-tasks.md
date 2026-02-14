# opdscli — Task Breakdown

## Summary

Build a Python CLI tool (`opdscli`) for interacting with OPDS 1.x ebook catalogs. The tool supports multiple catalogs with auth, searching (server-side + local fallback), downloading books, and viewing latest additions. Built with Typer + Rich, distributed as a single binary via PyInstaller and Homebrew.

## Dependencies (resolve before starting)

- None. This is a greenfield project with no external blockers.

## Task List

### Phase 1: Project Scaffolding

**1. Initialize project structure with uv**
- Create `pyproject.toml` with Python 3.12, all dependencies (typer, rich, httpx, lxml, pyyaml, thefuzz, pytest, respx, mypy, ruff)
- Set up `src/opdscli/` package layout with `__init__.py`, `__main__.py`, `cli.py`
- Configure ruff, mypy, and pytest in `pyproject.toml`
- Run `uv sync` to verify everything installs
- Acceptance: `uv run python -m opdscli --help` prints a help message
- Complexity: **S**
- Dependencies: none

**2. Set up Typer CLI skeleton with global flags**
- Create main Typer app in `cli.py` with `--verbose`, `--quiet`, `--version`, `--catalog` global options
- Add subcommand groups: `catalog`, `search`, `download`, `latest` (stubs only)
- Acceptance: All subcommands show in `--help`, global flags are parsed
- Complexity: **S**
- Dependencies: Task 1

### Phase 2: Configuration

**3. Implement config file loading and saving**
- Create `src/opdscli/config.py`
- Load/save `~/.config/opdscli.yaml` with PyYAML
- Define data classes or TypedDicts for config structure (catalogs, settings)
- Check file permissions and warn if world-readable
- Handle missing config gracefully (print setup instructions)
- Acceptance: Can load, modify, and save config; permission warning works; missing file handled
- Complexity: **M**
- Dependencies: Task 1

**4. Implement `catalog add/remove/list/set-default` commands**
- Wire up Typer subcommands to config module
- `add`: accepts name, URL, optional `--auth-type`; prompts for credentials interactively
- `remove`: removes by name, confirms before removing default
- `list`: prints all catalogs in a Rich table, marks default with indicator
- `set-default`: updates default, validates catalog name exists
- Acceptance: Full CRUD on catalogs via CLI, config file updated correctly
- Complexity: **M**
- Dependencies: Tasks 2, 3

### Phase 3: OPDS Parsing & HTTP

**5. Implement HTTP client with auth and retry**
- Create `src/opdscli/http.py`
- Build an httpx-based client that applies auth (Basic or Bearer) per catalog config
- Implement retry-once-with-backoff logic
- Handle network errors, timeouts, and auth failures (401/403) with clear messages
- Acceptance: Can fetch OPDS feeds with auth; retries on failure; clear error messages
- Complexity: **M**
- Dependencies: Task 3

**6. Implement OPDS 1.x feed parser**
- Create `src/opdscli/opds.py`
- Parse Atom/XML feeds using lxml
- Extract entries with: title, author(s), available formats (from acquisition links), updated date
- Distinguish navigation feeds from acquisition feeds
- Extract `rel="next"` pagination links
- Detect and parse OpenSearch description documents
- Acceptance: Can parse sample OPDS feeds into structured book/entry objects
- Complexity: **L**
- Dependencies: Task 1
- Technical notes: Use OPDS and Atom namespaces. Book formats come from `link` elements with `rel="http://opds-spec.org/acquisition"` and `type` attributes.

### Phase 4: Core Commands

**7. Implement `search` command**
- Create `src/opdscli/commands/search.py`
- Check if catalog supports OpenSearch; if so, use it
- If not, crawl feed structure up to `--depth` levels (default 3), following navigation links
- Filter entries matching query against title, author, description (case-insensitive substring)
- Display results in Rich table (Title, Author, Format)
- Handle pagination with `rel="next"` links
- Acceptance: Server-side search works when available; local fallback works; results displayed correctly
- Complexity: **L**
- Dependencies: Tasks 5, 6

**8. Implement `latest` command**
- Create `src/opdscli/commands/latest.py`
- Fetch the catalog's main/acquisition feed
- Sort by newest (use `updated` or `published` element)
- Limit to 20 by default, respect `--limit`
- Display in Rich table (Title, Author, Format)
- Acceptance: Shows latest N entries; `--limit` works; proper formatting
- Complexity: **M**
- Dependencies: Tasks 5, 6

**9. Implement `download` command**
- Create `src/opdscli/commands/download.py`
- Search catalog for exact title match (case-insensitive)
- If no match: show error + up to 5 fuzzy suggestions using thefuzz
- Select format: use `--format` flag > config default > EPUB fallback
- Download file with Rich progress bar
- Save to `--output` or cwd with sanitized filename (`<title>.<format>`)
- Acceptance: Exact match download works; fuzzy suggestions shown on miss; progress bar displays; correct file saved
- Complexity: **L**
- Dependencies: Tasks 5, 6, 7 (reuses search/crawl logic)

### Phase 5: Testing

**10. Create OPDS XML test fixtures**
- Create `tests/fixtures/` directory
- Add sample OPDS navigation feed XML
- Add sample OPDS acquisition feed XML with multiple entries and formats
- Add sample OpenSearch description document XML
- Add edge cases: empty feed, feed with missing fields, paginated feed
- Acceptance: Realistic fixtures that cover all parsing paths
- Complexity: **S**
- Dependencies: Task 6

**11. Write unit tests for OPDS parser**
- Test parsing of navigation feeds, acquisition feeds, entry extraction
- Test OpenSearch detection and URL template parsing
- Test pagination link extraction
- Test handling of malformed/incomplete feeds
- Acceptance: All parser paths covered; tests pass
- Complexity: **M**
- Dependencies: Tasks 6, 10

**12. Write unit tests for config module**
- Test load, save, add catalog, remove catalog, set default
- Test permission check warnings
- Test missing config file handling
- Acceptance: All config operations tested
- Complexity: **S**
- Dependencies: Tasks 3, 10

**13. Write integration tests for CLI commands**
- Use Typer's CliRunner to test each command end-to-end
- Mock HTTP with respx
- Test search (server-side and local fallback), latest, download
- Test error cases: network failure, auth failure, no match
- Test catalog management commands
- Acceptance: All commands tested via CLI runner; all error paths covered
- Complexity: **L**
- Dependencies: Tasks 7, 8, 9, 10

### Phase 6: Packaging & Distribution

**14. Set up PyInstaller build**
- Create PyInstaller spec or configure via `pyproject.toml`
- Build single binary for macOS
- Test that the binary works standalone
- Acceptance: `./opdscli --help` works from the built binary without Python installed
- Complexity: **M**
- Dependencies: Tasks 1–9

**15. Create Homebrew tap formula**
- Create a Homebrew tap repository structure
- Write formula that installs the PyInstaller binary or builds from source
- Document installation instructions in README
- Acceptance: `brew install <tap>/opdscli` installs and runs successfully
- Complexity: **M**
- Dependencies: Task 14

## Suggested Implementation Order

| Phase | Tasks | Description |
|-------|-------|-------------|
| 1 — Scaffolding | 1, 2 | Project setup, CLI skeleton |
| 2 — Config | 3, 4 | Config management, catalog CRUD |
| 3 — Core Infra | 5, 6 | HTTP client, OPDS parser |
| 4 — Commands | 7, 8, 9 | search, latest, download |
| 5 — Testing | 10, 11, 12, 13 | Fixtures, unit tests, integration tests |
| 6 — Distribution | 14, 15 | PyInstaller, Homebrew |

Tasks within each phase can often be parallelized (e.g., tasks 5 and 6 are independent).

## Risk Areas

- **OPDS parsing complexity** (Task 6): OPDS feeds vary wildly in practice. Real-world catalogs may use non-standard extensions or deviate from the spec. Consider doing an exploratory spike against 2-3 real catalogs early on.
- **OpenSearch integration** (Task 7): Not all catalogs implement OpenSearch, and those that do may have quirks. The local crawl fallback is the safety net.
- **PyInstaller binary size** (Task 14): Python + lxml + httpx can produce large binaries (50-100MB+). May need to investigate tree-shaking or alternative packaging if size is a concern.
- **Fuzzy matching quality** (Task 9): thefuzz results depend on the scoring algorithm. May need tuning of the score threshold for suggestions.

## Testing Strategy

| Area | Approach |
|------|----------|
| OPDS parsing | Unit tests with XML fixtures (navigation, acquisition, OpenSearch, edge cases) |
| Config management | Unit tests for load/save/CRUD operations |
| HTTP client | Unit tests with mocked responses (respx), covering auth, retry, errors |
| CLI commands | Integration tests via Typer CliRunner with mocked HTTP |
| Download | Test progress bar rendering, file writing, filename sanitization |
| Error handling | Dedicated tests for each error path (network, auth, invalid feed, no match) |
