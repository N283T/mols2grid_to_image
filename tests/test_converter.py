import warnings

import pandas as pd
import pytest
from unittest.mock import MagicMock, patch
from m2g_image.converter import (
    generate_grid_html,
    generate_grid_image,
    generate_grid_images,
    grid_to_image,
)


@pytest.fixture
def sample_df():
    return pd.DataFrame({"smiles": ["C", "CC", "CCC"], "ccd": ["M1", "M2", "M3"]})


def test_generate_grid_image_creates_files(sample_df, output_dir):
    """Test that generate_grid_image calls grid_to_image and creates output."""
    html_out = output_dir / "test.html"
    image_out = output_dir / "test.png"

    with patch("m2g_image.converter.grid_to_image") as mock_g2i:
        mock_g2i.return_value = image_out

        result_path = generate_grid_image(
            sample_df,
            output_html_path=str(html_out),
            output_image_path=str(image_out),
            smiles_col="smiles",
            n_cols=3,
            sort_by="smiles",
            gap=20,
        )

        assert result_path == image_out
        mock_g2i.assert_called_once()
        args, kwargs = mock_g2i.call_args
        assert kwargs["intermediate_html_path"] == str(html_out)


def test_generate_grid_image_returns_path(sample_df, output_dir):
    """generate_grid_image returns a Path object, not a string."""
    from pathlib import Path

    image_out = output_dir / "test.png"

    with patch("m2g_image.converter.grid_to_image") as mock_g2i:
        mock_g2i.return_value = image_out
        result = generate_grid_image(sample_df, output_image_path=str(image_out))
        assert isinstance(result, Path)


def test_generate_grid_image_passes_kwargs(sample_df, output_dir):
    """Test that extra kwargs are passed to mols2grid.display."""
    with (
        patch("m2g_image.converter.mols2grid.display") as mock_display,
        patch("m2g_image.converter.grid_to_image") as mock_g2i,
    ):
        mock_g2i.return_value = output_dir / "dummy.png"

        generate_grid_image(
            sample_df,
            output_image_path="dummy.png",
            sort_by="smiles",
            gap=15,
            removeHs=True,
            border="1px solid red",
        )

        mock_display.assert_called_once()
        _args, kwargs = mock_display.call_args

        assert kwargs["sort_by"] == "smiles"
        assert kwargs["gap"] == 15
        assert kwargs["removeHs"] is True
        assert kwargs["border"] == "1px solid red"
        assert kwargs["template"] == "static"
        assert kwargs["prerender"] is True


def test_generate_grid_html_deprecation_warning(sample_df, output_dir):
    """generate_grid_html emits DeprecationWarning."""
    with (
        patch("m2g_image.converter.grid_to_image") as mock_g2i,
        warnings.catch_warnings(record=True) as w,
    ):
        warnings.simplefilter("always")
        mock_g2i.return_value = output_dir / "test.png"

        result = generate_grid_html(
            sample_df, output_image_path=str(output_dir / "test.png")
        )

        assert len(w) == 1
        assert issubclass(w[0].category, DeprecationWarning)
        assert "generate_grid_image" in str(w[0].message)
        # Returns str for backward compat
        assert isinstance(result, str)


def test_generate_grid_images_single_page(sample_df, output_dir):
    """Single page yields one result."""
    with patch("m2g_image.converter.generate_grid_image") as mock_gen:
        mock_gen.return_value = output_dir / "result.png"

        results = list(
            generate_grid_images(sample_df, output_image_path=output_dir / "result.png")
        )

        assert len(results) == 1
        assert results[0][0] == 1  # page number
        mock_gen.assert_called_once()


def test_generate_grid_images_pagination(sample_df, output_dir):
    """Multiple pages yield correct number of results."""
    with patch("m2g_image.converter.generate_grid_image") as mock_gen:
        mock_gen.side_effect = lambda *a, **kw: kw["output_image_path"]

        results = list(
            generate_grid_images(
                sample_df,
                output_image_path=output_dir / "result.png",
                n_items_per_page=2,
            )
        )

        assert len(results) == 2
        assert results[0][0] == 1
        assert results[1][0] == 2
        assert mock_gen.call_count == 2


def test_generate_grid_images_empty_df(output_dir):
    """Empty DataFrame yields nothing."""
    empty_df = pd.DataFrame({"smiles": []})
    results = list(
        generate_grid_images(empty_df, output_image_path=output_dir / "result.png")
    )
    assert results == []


def test_grid_to_image_logic(output_dir):
    """Test the logic inside grid_to_image (file handling etc) without real screenshot."""
    mock_grid = MagicMock()
    mock_grid._repr_html_.return_value = "<html><body>Test</body></html>"

    output_png = output_dir / "out.png"
    intermediate_html = output_dir / "temp.html"

    with patch("m2g_image.converter.capture_element_screenshot") as mock_capture:
        mock_capture.return_value = output_png

        result = grid_to_image(
            mock_grid,
            output_image_path=str(output_png),
            intermediate_html_path=str(intermediate_html),
        )

        assert result == output_png
        mock_capture.assert_called_once()

        # Check if intermediate HTML was created
        assert intermediate_html.exists()
        assert intermediate_html.read_text() == "<html><body>Test</body></html>"
