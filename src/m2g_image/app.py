
import typer
import pandas as pd
import json
from pathlib import Path
from typing import List, Optional, Any
from .converter import generate_grid_html

app = typer.Typer(help="Convert Molecule CSV to Grid Image via mols2grid and Playwright")

def load_config(config_path: Path) -> dict:
    if not config_path.exists():
        return {}
    with open(config_path, "r") as f:
        return json.load(f)

@app.command()
def main(
    input_csv: Optional[Path] = typer.Argument(None, help="Path to input CSV file"),
    
    # Optional Output & Config
    output_image: Optional[Path] = typer.Option(None, "-o", "--output", help="Path to output PNG file (Default: result.png)"),
    output_html: Optional[Path] = typer.Option(None, "-oh", "--output-html", help="Path to save intermediate HTML file (Default: None/False)"),
    config: Optional[Path] = typer.Option(None, "-c", "--config", help="Path to JSON configuration file"),
    
    # Grid Settings
    smiles_col: Optional[str] = typer.Option(None, help="Column name for SMILES (Default: smiles)"),
    subset: Optional[List[str]] = typer.Option(None, help="Columns to display in grid"),
    n_cols: Optional[int] = typer.Option(None, help="Number of columns (Default: 5)"),
    cell_width: Optional[int] = typer.Option(None, help="Cell width (Default: 150)"),
    cell_height: Optional[int] = typer.Option(None, help="Cell height (Default: 150)"),
    fontsize: Optional[int] = typer.Option(None, help="Font size (Default: 12)"),
):
    """
    Generate a grid image. Parameters can be supplied via CLI args or a JSON config file.
    CLI args take precedence over JSON config.
    """
    
    # 1. Load Config from JSON
    file_config = {}
    if config:
        if not config.exists():
            typer.echo(f"Error: Config file {config} does not exist.", err=True)
            raise typer.Exit(code=1)
        file_config = load_config(config)

    # 2. Resolve Parameters (CLI > JSON > Defaults)
    def get_param(cli_val: Any, key: str, default: Any) -> Any:
        if cli_val is not None:
            return cli_val
        if key in file_config:
            return file_config[key]
        return default

    # Required Input
    final_input_path = get_param(input_csv, "input_csv", None)
    if not final_input_path:
        # Check if "input_csv" is in config string path?
        if "input_csv" in file_config:
            final_input_path = Path(file_config["input_csv"])
        else:
            typer.echo("Error: input_csv must be provided via argument or config file.", err=True)
            raise typer.Exit(code=1)
            
    final_input_path = Path(final_input_path)
    if not final_input_path.exists():
        typer.echo(f"Error: Input file {final_input_path} does not exist.", err=True)
        raise typer.Exit(code=1)

    # Resolve other params
    final_output_image = get_param(output_image, "output_image", "result.png")
    final_output_html = get_param(output_html, "output_html", None)
    final_smiles_col = get_param(smiles_col, "smiles_col", "smiles")
    final_n_cols = get_param(n_cols, "n_cols", 5)
    final_cell_width = get_param(cell_width, "cell_width", 150)
    final_cell_height = get_param(cell_height, "cell_height", 150)
    final_fontsize = get_param(fontsize, "fontsize", 12)
    
    # Subset is a list.
    # Typer returns empty list if not provided? No, Optional[List] default None returns None.
    # If user provides --subset multiple times, it is a list.
    final_subset = subset
    if final_subset is None:
        if "subset" in file_config:
            final_subset = file_config["subset"]
        else:
            # Default logic
             final_subset = None # Let downstream handle or set default here
    
    
    # 3. Load Data & Run
    typer.echo(f"Loading {final_input_path}...")
    df = pd.read_csv(final_input_path)
    
    if final_subset is None:
        if "ccd" in df.columns:
            final_subset = ["ccd"]
        else:
            final_subset = []

    typer.echo("Generating Grid & Image (Powered by Playwright)...")
    
    output_path = generate_grid_html(
        df,
        output_html_path=str(final_output_html) if final_output_html else None,
        output_image_path=str(final_output_image),
        smiles_col=final_smiles_col,
        subset=final_subset,
        n_cols=final_n_cols,
        cell_size=(final_cell_width, final_cell_height),
        fontsize=final_fontsize,
        # use_pixi is removed/ignored as we use python-native playwright
    )
    
    typer.echo(f"Done! Image saved to {output_path}")

if __name__ == "__main__":
    app()
