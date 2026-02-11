import pytest
from dataclasses import FrozenInstanceError
from pathlib import Path
from m2g_image.config import GridConfig


def test_cli_overrides_config():
    """CLI values take priority over config file values."""
    cli = {"n_cols": 3, "fontsize": None}
    config = {"n_cols": 10, "fontsize": 20}

    cfg = GridConfig.from_cli_and_config(cli, config)

    assert cfg.n_cols == 3  # CLI wins
    assert cfg.fontsize == 20  # Config wins (CLI is None)


def test_config_fallback():
    """Config values used when CLI is None."""
    cli = {"smiles_col": None, "transparent": None}
    config = {"smiles_col": "SMILES", "transparent": True}

    cfg = GridConfig.from_cli_and_config(cli, config)

    assert cfg.smiles_col == "SMILES"
    assert cfg.transparent is True


def test_defaults():
    """Dataclass defaults used when both CLI and config are empty."""
    cfg = GridConfig.from_cli_and_config({}, {})

    assert cfg.output_image == Path("result.png")
    assert cfg.smiles_col == "smiles"
    assert cfg.n_cols == 5
    assert cfg.cell_width == 150
    assert cfg.cell_height == 150
    assert cfg.fontsize == 12
    assert cfg.transparent is False
    assert cfg.n_items_per_page is None


def test_to_grid_kwargs_excludes_none():
    """None values are excluded from grid kwargs."""
    cfg = GridConfig(sort_by=None, gap=None, border="1px solid black")
    kwargs = cfg.to_grid_kwargs()

    assert "sort_by" not in kwargs
    assert "gap" not in kwargs
    assert kwargs["border"] == "1px solid black"


def test_to_grid_kwargs_transparent():
    """transparent=True is included in grid kwargs."""
    cfg = GridConfig(transparent=True)
    kwargs = cfg.to_grid_kwargs()

    assert kwargs["transparent"] is True


def test_to_grid_kwargs_name_mapping():
    """Field names are mapped to mols2grid kwarg names."""
    cfg = GridConfig(remove_hs=True, coord_gen=False)
    kwargs = cfg.to_grid_kwargs()

    assert kwargs["removeHs"] is True
    assert kwargs["coordGen"] is False
    assert "remove_hs" not in kwargs
    assert "coord_gen" not in kwargs


def test_cell_size_property():
    """cell_size returns (cell_width, cell_height) tuple."""
    cfg = GridConfig(cell_width=200, cell_height=300)
    assert cfg.cell_size == (200, 300)


def test_frozen():
    """Mutation raises FrozenInstanceError."""
    cfg = GridConfig()
    with pytest.raises(FrozenInstanceError):
        cfg.n_cols = 10


def test_path_coercion_from_config():
    """String paths from config are coerced to Path objects."""
    cli = {}
    config = {"output_image": "custom.png", "output_dir": "/tmp/out"}

    cfg = GridConfig.from_cli_and_config(cli, config)

    assert cfg.output_image == Path("custom.png")
    assert cfg.output_dir == Path("/tmp/out")


def test_unknown_config_keys_warning():
    """Unknown keys in config file trigger a warning."""
    import warnings

    cli = {}
    config = {"n_cols": 3, "unknown_key": "value", "another_bad": 42}

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        cfg = GridConfig.from_cli_and_config(cli, config)

    warning_messages = [str(x.message) for x in w]
    assert any("another_bad" in msg for msg in warning_messages)
    assert any("unknown_key" in msg for msg in warning_messages)
    assert cfg.n_cols == 3


def test_input_csv_not_warned():
    """input_csv is a known special key and should not trigger a warning."""
    import warnings

    cli = {}
    config = {"input_csv": "test.csv", "n_cols": 3}

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        GridConfig.from_cli_and_config(cli, config)

    warning_messages = [str(x.message) for x in w]
    assert not any("input_csv" in msg for msg in warning_messages)
