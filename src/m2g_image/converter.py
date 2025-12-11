import pandas as pd
import mols2grid
import os
import io
import contextlib
from pathlib import Path
from typing import Optional, Tuple, List

# Minimum CSS required for imaging
DEFAULT_CSS = """
body {
    background-color: #ffffff;
    margin: 0;
}
.data-mols2grid-id {
    color: transparent !important;
}
"""

def generate_grid_html(
    df: pd.DataFrame,
    output_html_path: Optional[str] = None,
    output_image_path: str = "result.png",
    smiles_col: str = "smiles",
    subset: Optional[List[str]] = None,
    n_cols: int = 5,
    cell_size: Tuple[int, int] = (130, 90),
    fontsize: int = 12,
    pad: int = 10,
    custom_css: str = DEFAULT_CSS,
    **kwargs
) -> str:
    """
    Generates grid HTML from a DataFrame and immediately converts it to an image.
    Parameters required for imaging (template="static", prerender=True, etc.) are fixed internally.
    """
    
    # Force settings required for imaging, overriding user input if necessary
    force_kwargs = {
        "template": "static",  # Disable interactive features
        "prerender": True,     # Prerender to prevent JS rendering delays
        "useSVG": True,        # Use SVG for better quality
    }
    
    # Transparency Handling:
    # If transparent is requested, override body background to transparent.
    # We must POP 'transparent' from kwargs because mols2grid.display doesn't accept it.
    is_transparent = kwargs.pop("transparent", False)
    if is_transparent:
        custom_css += "\nbody { background-color: transparent !important; }"
        
        # Configure MolDrawOptions to enable transparent background for molecules
        from rdkit.Chem.Draw import MolDrawOptions
        opts = kwargs.get("MolDrawOptions", None)
        if opts is None:
            opts = MolDrawOptions()
        
        # opts.clearBackground = False (Do not draw the white rect)
        opts.clearBackground = False
        kwargs["MolDrawOptions"] = opts

    # Merge forced settings into kwargs (taking precedence over user settings)
    display_kwargs = {**kwargs, **force_kwargs}
    
    # Default border to None, but use user specification if provided
    if "border" not in display_kwargs:
        display_kwargs["border"] = "none"

    with contextlib.redirect_stdout(io.StringIO()):
        grid = mols2grid.display(
            df,
            size=cell_size,
            pad=pad,
            subset=subset,
            n_cols=n_cols,
            fontsize=fontsize,
            smiles_col=smiles_col,
            custom_css=custom_css,
            **display_kwargs
        )
    
    return grid_to_image(
        grid, 
        output_image_path=output_image_path, 
        intermediate_html_path=output_html_path,
        omit_background=is_transparent
    )

def grid_to_image(
    grid,
    output_image_path: str = "result.png",
    intermediate_html_path: Optional[str] = None,
    selector: str = "#mols2grid",
    omit_background: bool = False
) -> str:
    """
    Receives a mols2grid object and converts it to an image via Playwright.
    """
    html_content = grid._repr_html_()

    if intermediate_html_path:
        html_path = Path(intermediate_html_path).resolve()
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        temp_file = None
    else:
        import tempfile
        temp_file = tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w", encoding="utf-8")
        temp_file.write(html_content)
        temp_file.close()
        html_path = Path(temp_file.name)
            
    try:
        from .screenshot import capture_element_screenshot
        return str(capture_element_screenshot(
            html_file_path=html_path,
            output_image_path=output_image_path,
            selector=selector,
            omit_background=omit_background
        ))
            
    finally:
        if temp_file:
            try:
                os.unlink(html_path)
            except OSError:
                pass
