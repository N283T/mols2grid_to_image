# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Python CLI tool and library that converts CSV files containing SMILES molecular data into grid PNG images. Uses `mols2grid` for grid generation and `Playwright` (headless Chromium) for HTML-to-image capture.

## Commands

```bash
# Install dependencies
uv sync

# Install Playwright browsers (required for screenshot functionality)
uv run playwright install chromium

# Run all tests
uv run pytest

# Run a single test
uv run pytest tests/test_config.py::test_cli_overrides_config

# Lint and format
ruff format . && ruff check --fix .

# CLI usage
uv run m2g-image input.csv -o output.png
uv run m2g-image --version
```

## Architecture

The package lives in `src/m2g_image/` with four modules forming a pipeline:

1. **`config.py`** - Frozen `GridConfig` dataclass. Centralizes all defaults and provides `from_cli_and_config(cli_values, file_config)` for three-tier merging (CLI > JSON config > defaults). `to_grid_kwargs()` builds the kwargs dict for mols2grid, mapping field names (e.g. `remove_hs` -> `removeHs`).

2. **`app.py`** - Typer CLI entrypoint (`m2g-image` command). Decomposed into small helper functions: `_load_config`, `_resolve_input_csv`, `_load_and_validate_csv`, `_resolve_output_path`, `_resolve_subset`, `_run_batch_generation`. Delegates pagination to `generate_grid_images()`.

3. **`converter.py`** - Core logic. `generate_grid_image()` is the primary API (returns `Path`). Forces `template="static"`, `prerender=True`, `useSVG=True` on `mols2grid.display()`, handles transparency via CSS injection and `MolDrawOptions.clearBackground`. `generate_grid_images()` is a generator for paginated output yielding `(page_number, Path)`. `generate_grid_html()` is a deprecated wrapper returning `str`.

4. **`screenshot.py`** - Playwright wrapper. `capture_element_screenshot()` launches headless Chromium with try/finally for browser cleanup, navigates to a `file://` URL, and screenshots the `#mols2grid` element.

**Data flow:** CSV -> pandas DataFrame -> `mols2grid.display()` -> HTML string -> temp file -> Playwright screenshot -> PNG

## Testing

Tests use `pytest` with `pytest-mock`. Most tests mock `generate_grid_image`/`generate_grid_images` or `grid_to_image` to avoid launching Playwright. `test_screenshot.py` contains integration tests that actually launch Playwright. Test data is in `tests/data/test.csv` (36 rows). Test output goes to `tests/output/`.

## Key Dependencies

- `mols2grid` - Molecular grid HTML generation (depends on `rdkit`)
- `playwright` - Headless browser for HTML-to-PNG conversion
- `typer` - CLI framework
- `pandas` - Data handling

## Project-Specific Patterns

- The `transparent` flag is popped from `**kwargs` before passing to `mols2grid.display()` (which doesn't accept it) and handled via CSS + `MolDrawOptions`
- `mols2grid.display()` stdout is suppressed via `contextlib.redirect_stdout`
- `GridConfig` is frozen (immutable) - use `from_cli_and_config()` to create instances
- If the DataFrame has a `ccd` column, it becomes the default `subset`
- Unknown keys in JSON config trigger a `UserWarning`
