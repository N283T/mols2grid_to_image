
from tempfile import template
import mols2grid
import pandas as pd
from m2g_image import grid_to_image

def main():
    # 1. 任意のデータフレームを用意
    df = pd.read_csv("test.csv")

    # 2. mols2gridでグリッドオブジェクトを作成 (表示設定はここで行う)
    print("Creating grid object...")
    grid = mols2grid.display(
        df,
        subset=["ccd", "smiles"],
        smiles_col="smiles",
        n_cols=5,
        size=(150, 150),
        fontsize=10,
        template="static",
        prerender=True
    )

    # 3. グリッドオブジェクトを直接画像化関数に渡す
    print("Converting grid object to image...")
    output_path = grid_to_image(grid, "example_output.png")
    
    print(f"Success! Image saved to: {output_path}")

if __name__ == "__main__":
    main()
