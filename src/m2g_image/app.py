import json

import typer
import pandas as pd
from pathlib import Path
from tqdm import tqdm
from typing import Any, List, Optional

from .config import GridConfig
from .converter import generate_grid_html

app = typer.Typer(
    help="Convert Molecule CSV to Grid Image via mols2grid and Playwright"
)


def _load_config(config_path: Optional[Path]) -> dict[str, Any]:
    """Load and validate a JSON configuration file."""
    if not config_path:
        return {}
    if not config_path.exists():
        typer.echo(f"Error: Config file {config_path} does not exist.", err=True)
        raise typer.Exit(code=1)
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        typer.echo(
            f"Error: Invalid JSON in config file {config_path}: {e}", err=True
        )
        raise typer.Exit(code=1) from e
    if not isinstance(data, dict):
        typer.echo(
            f"Error: Config file must contain a JSON object, got {type(data).__name__}",
            err=True,
        )
        raise typer.Exit(code=1)
    return data


def _resolve_input_csv(
    cli_input: Optional[Path], file_config: dict[str, Any]
) -> Path:
    """Resolve and validate the input CSV path."""
    input_str = str(cli_input) if cli_input else file_config.get("input_csv")
    if not input_str:
        typer.echo(
            "Error: input_csv must be provided via argument or config file.", err=True
        )
        raise typer.Exit(code=1)

    input_path = Path(input_str)
    if not input_path.exists():
        typer.echo(f"Error: Input file {input_path} does not exist.", err=True)
        raise typer.Exit(code=1)
    return input_path


def _load_and_validate_csv(input_path: Path, smiles_col: str) -> pd.DataFrame:
    """Load CSV and validate it has data and the required SMILES column."""
    typer.echo(f"Loading {input_path}...")
    df = pd.read_csv(input_path)

    if len(df) == 0:
        typer.echo("Warning: Input CSV has no data rows.", err=True)
        raise typer.Exit(code=0)

    if smiles_col not in df.columns:
        typer.echo(
            f"Error: SMILES column '{smiles_col}' not found in CSV. "
            f"Available columns: {list(df.columns)}",
            err=True,
        )
        raise typer.Exit(code=1)

    return df


def _resolve_output_path(cfg: GridConfig) -> Path:
    """Resolve the final output image path, creating output_dir if needed."""
    output_image = cfg.output_image
    if cfg.output_dir:
        cfg.output_dir.mkdir(parents=True, exist_ok=True)
        return cfg.output_dir / output_image.name
    return output_image


def _resolve_subset(subset: list[str] | None, df: pd.DataFrame) -> list[str]:
    """Resolve subset column list with smart defaults."""
    if subset is not None:
        return subset
    if "ccd" in df.columns:
        return ["ccd"]
    return []


def _run_batch_generation(
    df: pd.DataFrame,
    cfg: GridConfig,
    output_image: Path,
    subset: list[str],
) -> None:
    """Run grid image generation, optionally in batches."""
    total_rows = len(df)
    chunk_size = (
        cfg.n_items_per_page
        if (cfg.n_items_per_page and cfg.n_items_per_page > 0)
        else total_rows
    )
    num_chunks = (total_rows + chunk_size - 1) // chunk_size
    padding_width = len(str(num_chunks))
    grid_kwargs = cfg.to_grid_kwargs()

    typer.echo("Generating Grid & Image (Powered by Playwright)...")

    for i in tqdm(range(num_chunks), desc="Processing Batches"):
        start_idx = i * chunk_size
        end_idx = min((i + 1) * chunk_size, total_rows)
        chunk_df = df.iloc[start_idx:end_idx]

        if num_chunks > 1:
            current_path = (
                output_image.parent
                / f"{output_image.stem}_{i + 1:0{padding_width}d}{output_image.suffix}"
            )
        else:
            current_path = output_image

        generate_grid_html(
            chunk_df,
            output_image_path=str(current_path),
            output_html_path=str(cfg.output_html) if cfg.output_html else None,
            smiles_col=cfg.smiles_col,
            subset=subset,
            n_cols=cfg.n_cols,
            cell_size=cfg.cell_size,
            fontsize=cfg.fontsize,
            **grid_kwargs,
        )


@app.command()
def main(
    input_csv: Optional[Path] = typer.Argument(None, help="Path to input CSV file"),
    # Output & Config
    output_image: Optional[Path] = typer.Option(
        None, "-o", "--output", help="Path to output PNG file (Default: result.png)"
    ),
    output_html: Optional[Path] = typer.Option(
        None,
        "-oh",
        "--output-html",
        help="Path to save intermediate HTML file (Default: None/False)",
    ),
    config: Optional[Path] = typer.Option(
        None, "-c", "--config", help="Path to JSON configuration file"
    ),
    # Grid Settings
    smiles_col: Optional[str] = typer.Option(
        None, "-sc", "--smiles-col", help="Column name for SMILES (Default: smiles)"
    ),
    subset: Optional[List[str]] = typer.Option(None, help="Columns to display in grid"),
    n_cols: Optional[int] = typer.Option(
        None, "-nc", "--n-cols", help="Number of columns (Default: 5)"
    ),
    cell_width: Optional[int] = typer.Option(
        None, "-w", "--cell-width", help="Cell width (Default: 150)"
    ),
    cell_height: Optional[int] = typer.Option(
        None, "-ch", "--cell-height", help="Cell height (Default: 150)"
    ),
    fontsize: Optional[int] = typer.Option(
        None, "-fs", "--fontsize", help="Font size (Default: 12)"
    ),
    # Molecule display
    sort_by: Optional[str] = typer.Option(None, help="Column to sort by"),
    remove_hs: Optional[bool] = typer.Option(
        None, help="Remove hydrogens (Default: True)"
    ),
    use_coords: Optional[bool] = typer.Option(
        None, help="Use existing coordinates (Default: False)"
    ),
    coord_gen: Optional[bool] = typer.Option(None, help="Use CoordGen (Default: True)"),
    border: Optional[str] = typer.Option(
        None, help="CSS border styling (e.g., '1px solid black')"
    ),
    gap: Optional[int] = typer.Option(None, help="Gap size in pixels (Default: 0)"),
    fontfamily: Optional[str] = typer.Option(
        None, "-ff", "--font-family", help="Font family (Default: sans-serif)"
    ),
    text_align: Optional[str] = typer.Option(
        None, "-ta", "--text-align", help="Text alignment (Default: center)"
    ),
    # Pagination
    n_items_per_page: Optional[int] = typer.Option(
        None,
        "-p",
        "--per-page",
        help="Number of molecules per page (image). If set, splits output into multiple files.",
    ),
    # Transparency
    transparent: Optional[bool] = typer.Option(
        None, "-t", "--transparent", help="Make background transparent (PNG only)."
    ),
    # Output Control
    output_dir: Optional[Path] = typer.Option(
        None,
        "-od",
        "--output-dir",
        help="Directory to save output images. If set, overrides the directory of output-image.",
    ),
):
    """
    Generate a grid image. Parameters can be supplied via CLI args or a JSON config file.
    CLI args take precedence over JSON config.
    """
    file_config = _load_config(config)
    input_path = _resolve_input_csv(input_csv, file_config)

    # Build CLI values dict (None = not provided by user)
    cli_values = {
        "output_image": output_image,
        "output_html": output_html,
        "output_dir": output_dir,
        "smiles_col": smiles_col,
        "subset": subset,
        "n_cols": n_cols,
        "cell_width": cell_width,
        "cell_height": cell_height,
        "fontsize": fontsize,
        "sort_by": sort_by,
        "remove_hs": remove_hs,
        "use_coords": use_coords,
        "coord_gen": coord_gen,
        "border": border,
        "gap": gap,
        "fontfamily": fontfamily,
        "text_align": text_align,
        "n_items_per_page": n_items_per_page,
        "transparent": transparent,
    }

    cfg = GridConfig.from_cli_and_config(cli_values, file_config)
    df = _load_and_validate_csv(input_path, cfg.smiles_col)
    final_output = _resolve_output_path(cfg)
    subset_list = _resolve_subset(cfg.subset, df)

    _run_batch_generation(df, cfg, final_output, subset_list)


if __name__ == "__main__":
    app()
