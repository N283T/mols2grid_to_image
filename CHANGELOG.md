# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [0.1.0] - 2026-02-12

### Added

- CLI tool `m2g-image` for converting CSV files with SMILES data to grid PNG images
- Library API: `generate_grid_image()`, `generate_grid_images()`, `grid_to_image()`
- Frozen `GridConfig` dataclass with three-tier parameter resolution (CLI > JSON config > defaults)
- Pagination support with automatic zero-padded filenames
- Transparent background support for grid and molecule images
- JSON configuration file support with unknown key warnings
- Rich console output with progress bars
- `--version` flag
- Playwright-based HTML-to-PNG screenshot capture
- Comprehensive test suite (30 tests, 84% coverage)
- GitHub Actions CI/CD (test matrix Python 3.10-3.13, lint, PyPI publish)
- MIT License

[0.1.0]: https://github.com/N283T/mols2grid_to_image/releases/tag/v0.1.0
