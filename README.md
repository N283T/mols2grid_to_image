# mols2grid-to-image

A Python tool to convert molecule data (CSV) into grid images (PNG/HTML) using [mols2grid](https://github.com/cbouy/mols2grid) and [Playwright](https://playwright.dev/python/).

This tool generates a molecular grid visualization and captures it as a high-resolution image, all within a pure Python environment without requiring Node.js.

## Features

- **Pure Python**: Operates entirely in Python using `playwright` for headless browser automation.
- **Flexible Input**: Accepts CSV files containing SMILES strings.
- **Customizable Output**:
  - Control grid layout (columns, cell size, border, gap).
  - Select specific subsets of data to display.
  - Customize fonts and text alignment.
  - **Pagination**: Split large datasets into multiple images automatically.
  - **Transparent Background**: Generate PNGs with transparent backgrounds (including molecule images).
  - **Output Control**: Specify output directory and automatic zero-padded filenames for batch processing.
- **Configuration**: Support for JSON configuration files for reproducible settings.

## Installation

This project is managed with `uv`.

1.  **Sync dependencies**:
    ```bash
    uv sync
    ```

2.  **Install Playwright browsers**:
    ```bash
    uv run playwright install chromium
    ```

## Usage

You can use `mols2grid-to-image` as a CLI tool or as a library.

### CLI (Command Line Interface)

The package provides a `m2g-image` command.

**Basic Usage:**
```bash
uv run m2g-image input.csv -o output.png
```

**Options:**

| Option | Shorthand | Description | Default |
| :--- | :--- | :--- | :--- |
| `--output` | `-o` | Path to output PNG file (base name). | `result.png` |
| `--output-dir` | | Directory to save output images. Overrides `--output` dir. | `None` |
| `--output-html` | `-oh` | Path to save intermediate HTML file (Optional). | `None` (Not saved) |
| `--config` | `-c` | Path to JSON configuration file. | `None` |
| `--smiles-col` | | Column name for SMILES. | `smiles` |
| `--n-cols` | | Number of columns in grid. | `5` |
| `--subset` | | Columns to display in grid. | `None` |
| `--cell-width` | | Cell width in pixels. | `150` |
| `--cell-height` | | Cell height in pixels. | `150` |
| `--n-items-per-page` | | Number of items per image (pagination). | `None` (All in one) |
| `--transparent` | | Enable transparent background for grid and molecules. | `False` |
| `--border` | | CSS border for cells (e.g., "1px solid black"). | `None` |
| `--gap` | | Gap between cells in pixels. | `0` |
| `--fontfamily` | | Font family for text. | `None` |
| `--text-align` | | Text alignment (left, center, right). | `None` |
| `--sort-by` | | Column to sort by. | `None` |
| `--remove-hs` | | Remove hydrogens from depiction. | `True` |

**Examples:**

1. **Pagination**: Split into images with 50 molecules each.
   ```bash
   uv run m2g-image data.csv --n-items-per-page 50 -o batch.png
   # Generates batch_1.png, batch_2.png, ...
   ```

2. **Transparent Background**:
   ```bash
   uv run m2g-image data.csv --transparent -o transparent.png
   ```

3. **Output Directory & Zero Padding**:
   ```bash
   uv run m2g-image data.csv --n-items-per-page 10 --output-dir results/ -o grid.png
   # Generates results/grid_01.png, results/grid_02.png, ...
   ```

### Configuration File (JSON)

You can define parameters in a JSON file to avoid long command lines.

**config.json:**
```json
{
    "output_image": "custom_output.png",
    "n_cols": 4,
    "cell_width": 200,
    "cell_height": 200,
    "n_items_per_page": 20,
    "transparent": true,
    "subset": ["ID", "SMILES", "Activity"]
}
```

**Run with config:**
```bash
uv run m2g-image data.csv -c config.json
```

### Python Library Usage

You can integrate the conversion logic into your own Python scripts.

```python
import pandas as pd
import mols2grid
from m2g_image import grid_to_image, generate_grid_html

# 1. High-level wrapper (Recommended)
generate_grid_html(
    pd.read_csv("data.csv"),
    output_image_path="output.png",
    n_cols=5,
    subset=["ID"],
    transparent=True
)

# 2. Low-level usage
grid = mols2grid.display(df, ...)
# Note: For transparency, you must handle CSS and MolDrawOptions manually if using raw grid_to_image
output_path = grid_to_image(grid, "output.png", omit_background=True)
```

## Development

**Run Tests:**
```bash
uv run pytest
```
