
import math
import pandas as pd
import mols2grid
import os
from pathlib import Path
from typing import Optional, Tuple, List

# 画像化する上で最低限必要なCSS
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
    DataFrameからグリッドHTMLを生成し、直後に画像化を行います。
    画像化のために必要なパラメータ（template="static", prerender=Trueなど）は内部で固定します。
    """
    
    # ユーザーからの指定があっても、画像化に必須な設定で上書きします
    force_kwargs = {
        "template": "static",  # インタラクティブ機能はOFFにする
        "prerender": True,     # JSでの描画遅延を防ぐために事前にレンダリングする
        "useSVG": True,        # 画質確保のためSVGを使用
    }
    
    # kwargsに強制設定をマージ（ユーザー設定より優先）
    display_kwargs = {**kwargs, **force_kwargs}

    grid = mols2grid.display(
        df,
        size=cell_size,
        pad=pad,
        subset=subset,
        n_cols=n_cols,
        border="none",
        fontsize=fontsize,
        smiles_col=smiles_col,
        custom_css=custom_css,
        **display_kwargs
    )
    
    return grid_to_image(
        grid, 
        output_image_path=output_image_path, 
        intermediate_html_path=output_html_path
    )

def grid_to_image(
    grid,
    output_image_path: str = "result.png",
    intermediate_html_path: Optional[str] = None,
    selector: str = "#mols2grid"
) -> str:
    """
    mols2gridオブジェクトを受け取り、Puppeteer経由で画像化します。
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
            selector=selector
        ))
    finally:
        if temp_file:
            try:
                os.unlink(html_path)
            except OSError:
                pass
