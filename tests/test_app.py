import json

import pandas as pd
import pytest
from pathlib import Path
from typer.testing import CliRunner
from unittest.mock import patch, MagicMock
from m2g_image.app import app

runner = CliRunner()


def test_app_pagination(test_data_dir, output_dir):
    """Test that app splits output into multiple files when batch_size is set."""

    input_csv = test_data_dir / "test.csv"
    output_png = output_dir / "paginated.png"
    row_count = len(pd.read_csv(input_csv))
    batch_size = 2
    expected_chunks = (row_count + batch_size - 1) // batch_size

    with patch("m2g_image.app.generate_grid_html") as mock_gen:
        mock_gen.side_effect = lambda *args, **kwargs: kwargs["output_image_path"]

        result = runner.invoke(
            app, [str(input_csv), "-o", str(output_png), "--per-page", "2"]
        )

        assert result.exit_code == 0

    assert mock_gen.call_count == expected_chunks

    filenames = [call.kwargs["output_image_path"] for call in mock_gen.call_args_list]

    assert str(output_png.parent / "paginated_01.png") in filenames
    assert str(output_png.parent / "paginated_02.png") in filenames


def test_app_single_page(test_data_dir, output_dir):
    """Test standard single page output."""
    input_csv = test_data_dir / "test.csv"
    output_png = output_dir / "single.png"

    with patch("m2g_image.app.generate_grid_html") as mock_gen:
        mock_gen.return_value = str(output_png)

        result = runner.invoke(app, [str(input_csv), "-o", str(output_png)])

        assert result.exit_code == 0
        assert mock_gen.call_count == 1
        assert mock_gen.call_args.kwargs["output_image_path"] == str(output_png)


def test_app_output_control(test_data_dir, output_dir):
    """Test output_dir option and zero-padded filenames."""
    input_csv = test_data_dir / "test.csv"
    target_output_dir = output_dir / "custom_out"
    output_filename = "myfile.png"
    row_count = len(pd.read_csv(input_csv))
    batch_size = 2
    expected_chunks = (row_count + batch_size - 1) // batch_size

    with patch("m2g_image.app.generate_grid_html") as mock_gen:
        mock_gen.side_effect = lambda *args, **kwargs: kwargs["output_image_path"]

        result = runner.invoke(
            app,
            [
                str(input_csv),
                "-o",
                output_filename,
                "--output-dir",
                str(target_output_dir),
                "--per-page",
                "2",
            ],
        )

        assert result.exit_code == 0
        assert mock_gen.call_count == expected_chunks

        filenames = [
            call.kwargs["output_image_path"] for call in mock_gen.call_args_list
        ]

        expected_first = target_output_dir / "myfile_01.png"
        assert str(expected_first) in filenames

        padding = len(str(expected_chunks))
        expected_last = target_output_dir / f"myfile_{expected_chunks:0{padding}d}.png"
        assert str(expected_last) in filenames

        assert target_output_dir.exists()


def test_app_empty_csv(output_dir, tmp_path):
    """Test that empty CSV exits cleanly with a warning."""
    empty_csv = tmp_path / "empty.csv"
    empty_csv.write_text("smiles,ccd\n")

    result = runner.invoke(app, [str(empty_csv), "-o", str(output_dir / "out.png")])

    assert result.exit_code == 0
    assert (
        "no data rows" in result.output.lower()
        or "no data rows" in (result.stderr or "").lower()
    )


def test_app_transparent_from_config(test_data_dir, output_dir, tmp_path):
    """Test that transparent=true in config file works without CLI flag."""
    input_csv = test_data_dir / "test.csv"
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps({"transparent": True}))

    with patch("m2g_image.app.generate_grid_html") as mock_gen:
        mock_gen.return_value = str(output_dir / "out.png")

        result = runner.invoke(
            app,
            [
                str(input_csv),
                "-o",
                str(output_dir / "out.png"),
                "-c",
                str(config_file),
            ],
        )

        assert result.exit_code == 0
        mock_gen.assert_called_once()
        call_kwargs = mock_gen.call_args.kwargs
        assert call_kwargs.get("transparent") is True


def test_app_malformed_config(test_data_dir, tmp_path):
    """Test that invalid JSON config gives a clear error."""
    config_file = tmp_path / "bad.json"
    config_file.write_text("{invalid json}")
    input_csv = test_data_dir / "test.csv"

    result = runner.invoke(app, [str(input_csv), "-c", str(config_file)])

    assert result.exit_code == 1
    assert "invalid json" in result.output.lower()


def test_app_missing_smiles_column(output_dir, tmp_path):
    """Test that missing SMILES column gives a helpful error."""
    csv_file = tmp_path / "no_smiles.csv"
    csv_file.write_text("id,name\n1,aspirin\n2,caffeine\n")

    result = runner.invoke(app, [str(csv_file), "-o", str(output_dir / "out.png")])

    assert result.exit_code == 1
    assert "smiles" in result.output.lower()
    assert "available columns" in result.output.lower()
