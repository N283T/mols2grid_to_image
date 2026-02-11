import mols2grid
import pandas as pd
from m2g_image import grid_to_image


def main():
    # 1. Prepare a DataFrame
    df = pd.read_csv("example/test.csv")

    # 2. Create a grid object (display settings are specified here)
    print("Creating grid object...")
    grid = mols2grid.display(
        df,
        subset=["ccd", "smiles"],
        smiles_col="smiles",
        n_cols=5,
        size=(150, 150),
        fontsize=10,
        template="static",
        prerender=True,
    )

    # 3. Convert grid object to image
    print("Converting grid object to image...")
    output_path = grid_to_image(grid, "example/example_usage_output.png")

    print(f"Success! Image saved to: {output_path}")


if __name__ == "__main__":
    main()
