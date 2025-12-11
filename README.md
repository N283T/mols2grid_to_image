
# mols2grid-to-image

A Python tool to convert molecule data (CSV) into grid images (PNG/HTML) using [mols2grid](https://github.com/cbouy/mols2grid) and [Playwright](https://playwright.dev/python/).

This tool generates a molecular grid visualization and captures it as a high-resolution image, all within a pure Python environment without requiring Node.js.

## Features

- **Pure Python**: Operates entirely in Python using `playwright` for headless browser automation.
- **Flexible Input**: Accepts CSV files containing SMILES strings.
- **Customizable Output**:
  - Control grid layout (columns, cell size).
  - Select specific subsets of data to display.
  - Generates PNG images and optional intermediate HTML files.
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
| `--output` | `-o` | Path to output PNG file | `result.png` |
| `--output-html` | `-oh` | Path to save intermediate HTML file (Optional) | `None` (Not saved) |
| `--config` | `-c` | Path to JSON configuration file | `None` |
| `--smiles-col` | | Column name for SMILES | `smiles` |
| `--n-cols` | | Number of columns in grid | `5` |
| `--subset` | | Columns to display in grid | `None` |
| `--cell-width` | | Cell width in pixels | `150` |
| `--cell-height` | | Cell height in pixels | `150` |

**Example with options:**
```bash
uv run m2g-image data.csv -o my_grid.png --n-cols 8 --cell-width 200
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
from m2g_image import grid_to_image

# 1. Load Data & Create Grid
df = pd.read_csv("data.csv")
grid = mols2grid.display(
    df,
    subset=["ID", "SMILES"],
    n_cols=5,
    smiles_col="SMILES"
)

# 2. Convert to Image
# Returns the path to the saved image
output_path = grid_to_image(grid, "output.png")
print(f"Saved to {output_path}")
```

## Development

**Run Tests:**
```bash
uv run pytest
```
