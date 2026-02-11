"""Grid configuration dataclass with CLI/config file merging."""

import warnings
from dataclasses import dataclass, fields
from pathlib import Path
from typing import Any


# Mapping from GridConfig field names to mols2grid.display kwarg names
# Only includes fields that differ from the dataclass field name
_GRID_KWARG_NAMES: dict[str, str] = {
    "remove_hs": "removeHs",
    "coord_gen": "coordGen",
}

# Fields that map to mols2grid.display kwargs (optional params)
_GRID_KWARG_FIELDS: set[str] = {
    "sort_by",
    "remove_hs",
    "use_coords",
    "coord_gen",
    "border",
    "gap",
    "fontfamily",
    "text_align",
}


@dataclass(frozen=True)
class GridConfig:
    """Immutable configuration for grid image generation."""

    # I/O
    output_image: Path = Path("result.png")
    output_html: Path | None = None
    output_dir: Path | None = None

    # Grid layout
    smiles_col: str = "smiles"
    n_cols: int = 5
    cell_width: int = 150
    cell_height: int = 150
    fontsize: int = 12
    subset: list[str] | None = None

    # Molecule display
    sort_by: str | None = None
    remove_hs: bool | None = None
    use_coords: bool | None = None
    coord_gen: bool | None = None

    # Cell styling
    border: str | None = None
    gap: int | None = None
    fontfamily: str | None = None
    text_align: str | None = None

    # Pagination & output
    n_items_per_page: int | None = None
    transparent: bool = False

    @property
    def cell_size(self) -> tuple[int, int]:
        """Return cell dimensions as a (width, height) tuple."""
        return (self.cell_width, self.cell_height)

    def to_grid_kwargs(self) -> dict[str, Any]:
        """Build kwargs dict for generate_grid_html, excluding None values."""
        result: dict[str, Any] = {}
        for field_name in _GRID_KWARG_FIELDS:
            value = getattr(self, field_name)
            if value is not None:
                kwarg_name = _GRID_KWARG_NAMES.get(field_name, field_name)
                result[kwarg_name] = value
        if self.transparent:
            result["transparent"] = True
        return result

    @classmethod
    def from_cli_and_config(
        cls,
        cli_values: dict[str, Any],
        file_config: dict[str, Any],
    ) -> "GridConfig":
        """
        Merge with priority: CLI > Config file > Dataclass defaults.

        cli_values: dict where None means "not provided by user".
        file_config: dict from JSON config file.
        """
        merged: dict[str, Any] = {}
        field_names = {f.name for f in fields(cls)}

        # Warn on unknown keys in config file (excluding special keys like input_csv)
        _KNOWN_EXTRA_KEYS = {"input_csv"}
        unknown_keys = set(file_config.keys()) - field_names - _KNOWN_EXTRA_KEYS
        for key in sorted(unknown_keys):
            warnings.warn(
                f"Unknown config key ignored: '{key}'",
                UserWarning,
                stacklevel=2,
            )

        for f in fields(cls):
            cli_val = cli_values.get(f.name)
            config_val = file_config.get(f.name)

            if cli_val is not None:
                merged[f.name] = _coerce_value(f.name, cli_val)
            elif config_val is not None:
                merged[f.name] = _coerce_value(f.name, config_val)
            # else: use dataclass default

        return cls(**merged)


# Fields that should be coerced to Path
_PATH_FIELDS: set[str] = {"output_image", "output_html", "output_dir"}


def _coerce_value(field_name: str, value: Any) -> Any:
    """Coerce config values to their expected types."""
    if field_name in _PATH_FIELDS and isinstance(value, str):
        return Path(value)
    return value
