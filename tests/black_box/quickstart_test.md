# Quickstart Test

Verifies that the Quick Start workflow from the README works end-to-end against the real Project Gutenberg OPDS catalog.

## Preconditions

- The repository is cloned and dependencies are installed (`uv sync`).
- There is no existing catalog named `gutenberg` in the config. If there is, remove it first with `uv run opdscli catalog remove gutenberg`.
- Network access to `https://m.gutenberg.org` is available.

## Steps and expected outcomes

### 1. Add the Project Gutenberg catalog

Run:
```bash
uv run opdscli catalog add gutenberg https://m.gutenberg.org/ebooks.opds/
```

**Verify:**
- The command exits with code 0.
- The output confirms the catalog was added.

Then run:
```bash
uv run opdscli catalog list
```

**Verify:**
- The output includes a catalog named `gutenberg` with URL `https://m.gutenberg.org/ebooks.opds/`.

### 2. Search for a book

Run:
```bash
uv run opdscli search "don quixote" --catalog gutenberg
```

**Verify:**
- The command exits with code 0.
- The output contains at least one result with "Don Quixote" in the title.
- The output is displayed as a formatted table (contains column headers like Title, Author, Format).

### 3. Download a book

Create a temporary directory for the download, then run:
```bash
uv run opdscli download "Don Quixote" --catalog gutenberg --output /tmp/opdscli_test
```

**Verify:**
- The command exits with code 0.
- A file exists in `/tmp/opdscli_test/` with "Don Quixote" in its name and an `.epub` extension.
- The downloaded file is larger than 0 bytes.

### 4. Browse latest additions

Run:
```bash
uv run opdscli latest --catalog gutenberg --limit 5
```

**Verify:**
- The command exits with code 0.
- The output contains a formatted table with up to 5 entries.
- Each entry has at least a title shown.

## Cleanup

- Remove the `gutenberg` catalog: `uv run opdscli catalog remove gutenberg`.
- Delete the temporary download directory: `rm -rf /tmp/opdscli_test`.
