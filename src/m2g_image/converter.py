"""Grid HTML generation and image conversion."""

import contextlib
import io
import os
import tempfile
import warnings
from pathlib import Path
from typing import Generator, List, Optional, Tuple

import mols2grid
import pandas as pd

from .screenshot import capture_element_screenshot

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


def generate_grid_image(
    df: pd.DataFrame,
    output_image_path: str | Path = "result.png",
    output_html_path: str | Path | None = None,
    smiles_col: str = "smiles",
    subset: Optional[List[str]] = None,
    n_cols: int = 5,
    cell_size: Tuple[int, int] = (150, 150),
    fontsize: int = 12,
    pad: int = 10,
    custom_css: str = DEFAULT_CSS,
    **kwargs,
) -> Path:
    """
    Generate a grid image from a DataFrame of molecules.

    Generates grid HTML via mols2grid and converts it to a PNG image.
    Parameters required for imaging (template="static", prerender=True, etc.)
    are fixed internally.

    Returns:
        Path to the output image file.
    """
    # Force settings required for imaging
    force_kwargs = {
        "template": "static",
        "prerender": True,
        "useSVG": True,
    }

    # Pop 'transparent' because mols2grid.display doesn't accept it
    is_transparent = kwargs.pop("transparent", False)
    if is_transparent:
        transparent_css = "\nbody { background-color: transparent !important; }"
        custom_css = custom_css + transparent_css

        from rdkit.Chem.Draw import MolDrawOptions

        opts = kwargs.get("MolDrawOptions", None)
        if opts is None:
            opts = MolDrawOptions()
        opts.clearBackground = False
        kwargs["MolDrawOptions"] = opts

    display_kwargs = {**kwargs, **force_kwargs}

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
            **display_kwargs,
        )

    return grid_to_image(
        grid,
        output_image_path=output_image_path,
        intermediate_html_path=output_html_path,
        omit_background=is_transparent,
    )


def generate_grid_images(
    df: pd.DataFrame,
    output_image_path: str | Path = "result.png",
    n_items_per_page: int | None = None,
    **kwargs,
) -> Generator[tuple[int, Path], None, None]:
    """
    Generate grid images, optionally paginated.

    Yields (page_number, image_path) tuples. Page numbers are 1-based.
    If n_items_per_page is None or >= len(df), yields a single image.
    """
    total_rows = len(df)
    if total_rows == 0:
        return

    chunk_size = (
        n_items_per_page if (n_items_per_page and n_items_per_page > 0) else total_rows
    )
    num_chunks = (total_rows + chunk_size - 1) // chunk_size
    padding_width = len(str(num_chunks))
    output_path = Path(output_image_path)

    for i in range(num_chunks):
        start_idx = i * chunk_size
        end_idx = min((i + 1) * chunk_size, total_rows)
        chunk_df = df.iloc[start_idx:end_idx]

        if num_chunks > 1:
            current_path = (
                output_path.parent
                / f"{output_path.stem}_{i + 1:0{padding_width}d}{output_path.suffix}"
            )
        else:
            current_path = output_path

        result = generate_grid_image(
            chunk_df,
            output_image_path=current_path,
            **kwargs,
        )
        yield (i + 1, result)


def generate_grid_html(
    df: pd.DataFrame,
    output_html_path: str | Path | None = None,
    output_image_path: str | Path = "result.png",
    smiles_col: str = "smiles",
    subset: Optional[List[str]] = None,
    n_cols: int = 5,
    cell_size: Tuple[int, int] = (150, 150),
    fontsize: int = 12,
    pad: int = 10,
    custom_css: str = DEFAULT_CSS,
    **kwargs,
) -> str:
    """Deprecated: Use generate_grid_image instead."""
    warnings.warn(
        "generate_grid_html is deprecated, use generate_grid_image",
        DeprecationWarning,
        stacklevel=2,
    )
    return str(
        generate_grid_image(
            df,
            output_image_path=output_image_path,
            output_html_path=output_html_path,
            smiles_col=smiles_col,
            subset=subset,
            n_cols=n_cols,
            cell_size=cell_size,
            fontsize=fontsize,
            pad=pad,
            custom_css=custom_css,
            **kwargs,
        )
    )


def grid_to_image(
    grid,
    output_image_path: str | Path = "result.png",
    intermediate_html_path: str | Path | None = None,
    selector: str = "#mols2grid",
    omit_background: bool = False,
) -> Path:
    """
    Convert a mols2grid object to an image via Playwright.

    Returns:
        Path to the output image file.
    """
    html_content = grid._repr_html_()

    if intermediate_html_path:
        html_path = Path(intermediate_html_path).resolve()
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        temp_file = None
    else:
        temp_file = tempfile.NamedTemporaryFile(
            suffix=".html", delete=False, mode="w", encoding="utf-8"
        )
        temp_file.write(html_content)
        temp_file.close()
        html_path = Path(temp_file.name)

    try:
        return capture_element_screenshot(
            html_file_path=html_path,
            output_image_path=output_image_path,
            selector=selector,
            omit_background=omit_background,
        )
    finally:
        if temp_file:
            try:
                os.unlink(html_path)
            except OSError:
                pass
