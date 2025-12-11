
import typer
import pandas as pd
import json
from pathlib import Path
from typing import List, Optional, TypeVar, Any
from .converter import generate_grid_html

app = typer.Typer(help="Convert Molecule CSV to Grid Image via mols2grid and Playwright")

T = TypeVar("T")

def load_config(config_path: Path) -> dict[str, Any]:
    """Load configuration from a JSON file."""
    if not config_path.exists():
        return {}
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)

def resolve_param(cli_val: Optional[T], config_val: Optional[T], default: T) -> T:
    """
    Resolve parameter value with priority: CLI > Config > Default.
    """
    if cli_val is not None:
        return cli_val
    if config_val is not None:
        return config_val
    return default

@app.command()
def main(
    input_csv: Optional[Path] = typer.Argument(None, help="Path to input CSV file"),
    
    # Optional Output & Config
    output_image: Optional[Path] = typer.Option(None, "-o", "--output", help="Path to output PNG file (Default: result.png)"),
    output_html: Optional[Path] = typer.Option(None, "-oh", "--output-html", help="Path to save intermediate HTML file (Default: None/False)"),
    config: Optional[Path] = typer.Option(None, "-c", "--config", help="Path to JSON configuration file"),
    # Grid Settings
    smiles_col: Optional[str] = typer.Option(None, "-sc", "--smiles-col", help="Column name for SMILES (Default: smiles)"),
    subset: Optional[List[str]] = typer.Option(None, help="Columns to display in grid"),
    n_cols: Optional[int] = typer.Option(None, "-nc", "--n-cols", help="Number of columns (Default: 5)"),
    cell_width: Optional[int] = typer.Option(None, "-w", "--cell-width", help="Cell width (Default: 150)"),
    cell_height: Optional[int] = typer.Option(None, "-h", "--cell-height", help="Cell height (Default: 150)"),
    fontsize: Optional[int] = typer.Option(None, "-fs", "--fontsize", help="Font size (Default: 12)"),
    
    # New Options
    sort_by: Optional[str] = typer.Option(None, help="Column to sort by"),
    remove_hs: Optional[bool] = typer.Option(None, help="Remove hydrogens (Default: True)"),
    use_coords: Optional[bool] = typer.Option(None, help="Use existing coordinates (Default: False)"),
    coord_gen: Optional[bool] = typer.Option(None, help="Use CoordGen (Default: True)"),
    border: Optional[str] = typer.Option(None, help="CSS border styling (e.g., '1px solid black')"),
    gap: Optional[int] = typer.Option(None, help="Gap size in pixels (Default: 0)"),
    fontfamily: Optional[str] = typer.Option(None, "-ff", "--font-family",help="Font family (Default: sans-serif)"),
    text_align: Optional[str] = typer.Option(None, "-ta", "--text-align", help="Text alignment (Default: center)"),
    
    # Pagination
    n_items_per_page: Optional[int] = typer.Option(None, "-p", "--per-page", help="Number of molecules per page (image). If set, splits output into multiple files."),
    
    # Transparency
    transparent: bool = typer.Option(False, "-t", "--transparent", help="Make background transparent (PNG only)."),
    
    # Output Control
    output_dir: Optional[Path] = typer.Option(None, "-od", "--output-dir", help="Directory to save output images. If set, overrides the directory of output-image."),
):
    """
    Generate a grid image. Parameters can be supplied via CLI args or a JSON config file.
    CLI args take precedence over JSON config.
    """
    
    # 1. Load Config from JSON
    file_config: dict[str, Any] = {}
    if config:
        if not config.exists():
            typer.echo(f"Error: Config file {config} does not exist.", err=True)
            raise typer.Exit(code=1)
        file_config = load_config(config)

    # 2. Resolve Parameters
    # Input CSV is special because it's required
    final_input_path_str = resolve_param(
        str(input_csv) if input_csv else None, 
        file_config.get("input_csv"), 
        None
    )
    
    if not final_input_path_str:
        typer.echo("Error: input_csv must be provided via argument or config file.", err=True)
        raise typer.Exit(code=1)
            
    final_input_path = Path(final_input_path_str)
    if not final_input_path.exists():
        typer.echo(f"Error: Input file {final_input_path} does not exist.", err=True)
        raise typer.Exit(code=1)

    # Output Dir Resolution
    final_output_dir = resolve_param(output_dir, Path(file_config.get("output_dir")) if file_config.get("output_dir") else None, None)
    
    # Output Image Resolution
    raw_output_image = resolve_param(str(output_image) if output_image else None, file_config.get("output_image"), "result.png")
    final_output_image = Path(raw_output_image)
    
    # If output_dir is specified, we rely on it. 
    # Whatever path is in final_output_image, we take its name and put it in output_dir.
    if final_output_dir:
        if not final_output_dir.exists():
            final_output_dir.mkdir(parents=True, exist_ok=True)
        final_output_image = final_output_dir / final_output_image.name

    # output_html
    config_output_html = file_config.get("output_html")
    final_output_html = resolve_param(
        output_html, 
        Path(config_output_html) if config_output_html else None, 
        None
    )

    final_smiles_col = resolve_param(smiles_col, file_config.get("smiles_col"), "smiles")
    final_n_cols = resolve_param(n_cols, file_config.get("n_cols"), 5)
    final_cell_width = resolve_param(cell_width, file_config.get("cell_width"), 150)
    final_cell_height = resolve_param(cell_height, file_config.get("cell_height"), 150)
    final_fontsize = resolve_param(fontsize, file_config.get("fontsize"), 12)
    
    final_subset = resolve_param(subset, file_config.get("subset"), None)

    # New Params Resolution
    final_sort_by = resolve_param(sort_by, file_config.get("sort_by"), None)
    final_remove_hs = resolve_param(remove_hs, file_config.get("remove_hs"), None) # Default is handled by mols2grid usually (True)
    final_use_coords = resolve_param(use_coords, file_config.get("use_coords"), None)
    final_coord_gen = resolve_param(coord_gen, file_config.get("coord_gen"), None)
    final_border = resolve_param(border, file_config.get("border"), None)
    final_gap = resolve_param(gap, file_config.get("gap"), None)
    final_fontfamily = resolve_param(fontfamily, file_config.get("fontfamily"), None)
    final_text_align = resolve_param(text_align, file_config.get("text_align"), None)
    
    final_n_items_per_page = resolve_param(n_items_per_page, file_config.get("n_items_per_page"), None)
    final_transparent = resolve_param(transparent, file_config.get("transparent"), False)

    # 3. Load Data & Run
    typer.echo(f"Loading {final_input_path}...")
    df = pd.read_csv(final_input_path)
    
    # Subset default logic if still None
    if final_subset is None:
        if "ccd" in df.columns:
            final_subset = ["ccd"]
        else:
            final_subset = []

    typer.echo("Generating Grid & Image (Powered by Playwright)...")
    
    # Construct kwargs dynamically to avoid passing None for everything
    grid_kwargs = {}
    if final_sort_by is not None: grid_kwargs["sort_by"] = final_sort_by
    if final_remove_hs is not None: grid_kwargs["removeHs"] = final_remove_hs
    if final_use_coords is not None: grid_kwargs["use_coords"] = final_use_coords
    if final_coord_gen is not None: grid_kwargs["coordGen"] = final_coord_gen
    if final_border is not None: grid_kwargs["border"] = final_border
    if final_gap is not None: grid_kwargs["gap"] = final_gap
    if final_fontfamily is not None: grid_kwargs["fontfamily"] = final_fontfamily
    if final_text_align is not None: grid_kwargs["text_align"] = final_text_align
    if final_transparent: grid_kwargs["transparent"] = True

    # Batch Processing Logic
    total_rows = len(df)
    chunk_size = final_n_items_per_page if (final_n_items_per_page and final_n_items_per_page > 0) else total_rows
    
    # Calculate number of chunks
    num_chunks = (total_rows + chunk_size - 1) // chunk_size
    padding_width = len(str(num_chunks))  # Calculate padding width based on total chunks
    if num_chunks == 0: num_chunks = 1 # Handle empty df case gracefully-ish
    
    from tqdm import tqdm
    for i in tqdm(range(num_chunks), desc="Processing Batches"):
        start_idx = i * chunk_size
        end_idx = min((i + 1) * chunk_size, total_rows)
        chunk_df = df.iloc[start_idx:end_idx]
        
        # Determine output filename
        if num_chunks > 1:
            stem = final_output_image.stem
            suffix = final_output_image.suffix
            # Use zero padding
            current_output_path = final_output_image.parent / f"{stem}_{i+1:0{padding_width}d}{suffix}"
        else:
            current_output_path = final_output_image

        output_path = generate_grid_html(
            chunk_df,
            output_image_path=str(current_output_path),
            output_html_path=str(final_output_html) if final_output_html else None,
            smiles_col=final_smiles_col,
            subset=final_subset,
            n_cols=final_n_cols,
            cell_size=(final_cell_width, final_cell_height),
            fontsize=final_fontsize,
            **grid_kwargs
        )
    
        # typer.echo(f"Done! Image saved to {output_path}")

if __name__ == "__main__":
    app()
