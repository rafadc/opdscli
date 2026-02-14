# Black Box Tests

This folder contains end-to-end tests described in natural language as Markdown files. They are designed to be executed by a coding agent (e.g. Claude Code) rather than a traditional test runner.

## How it works

Each `*_test.md` file describes a test scenario in plain English. A coding agent reads the file, performs the steps described, and verifies the expected outcomes. This approach tests the CLI as a real user would interact with it -- from the outside, with no mocking or access to internals.

## Running the tests

1. Open a coding agent session in the repository root.
2. Ask the agent to run the black box tests:
   ```
   Run the black box tests in tests/black_box/
   ```
3. The agent will read each `*_test.md` file, execute the described steps, and report pass/fail for each scenario.

## Writing new tests

- Create a new file matching the pattern `*_test.md`.
- Describe the **preconditions** (any setup the agent must do before the test).
- Describe the **steps** the agent should execute, typically CLI commands.
- Describe the **expected outcomes** the agent should verify.
- Keep steps concrete and verifiable. The agent needs to be able to determine unambiguously whether each check passed or failed.

## Test index

| File | Description |
|------|-------------|
| [quickstart_test.md](quickstart_test.md) | Verifies that the Quick Start workflow from the README works end-to-end against the Project Gutenberg OPDS catalog. |
