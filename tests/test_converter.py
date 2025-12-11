
import pytest
import pandas as pd
from unittest.mock import MagicMock, patch
from m2g_image.converter import generate_grid_html, grid_to_image

@pytest.fixture
def sample_df():
    return pd.DataFrame({
        "smiles": ["C", "CC", "CCC"],
        "ccd": ["M1", "M2", "M3"]
    })

def test_generate_grid_html_creates_files(sample_df, output_dir):
    """Test that generate_grid_html calls grid_to_image and creates output."""
    
    html_out = output_dir / "test.html"
    image_out = output_dir / "test.png"
    
    # We mock grid_to_image to avoid actual browser launch overhead in unit tests
    with patch("m2g_image.converter.grid_to_image") as mock_g2i:
        mock_g2i.return_value = str(image_out)
        
        result_path = generate_grid_html(
            sample_df,
            output_html_path=str(html_out),
            output_image_path=str(image_out),
            smiles_col="smiles",
            n_cols=3
        )
        
        assert result_path == str(image_out)
        mock_g2i.assert_called_once()
        # Verify arguments passed to grid_to_image
        args, kwargs = mock_g2i.call_args
        # kwargs should contain intermediate_html_path
        assert kwargs["intermediate_html_path"] == str(html_out)

def test_grid_to_image_logic(output_dir):
    """Test the logic inside grid_to_image (file handling etc) without real screenshot."""
    
    mock_grid = MagicMock()
    mock_grid._repr_html_.return_value = "<html><body>Test</body></html>"
    
    output_png = output_dir / "out.png"
    intermediate_html = output_dir / "temp.html"
    
    with patch("m2g_image.screenshot.capture_element_screenshot") as mock_capture:
        mock_capture.return_value = output_png
        
        result = grid_to_image(
            mock_grid,
            output_image_path=str(output_png),
            intermediate_html_path=str(intermediate_html)
        )
        
        assert result == str(output_png)
        mock_capture.assert_called_once()
        
        # Check if intermediate HTML was created
        assert intermediate_html.exists()
        assert intermediate_html.read_text() == "<html><body>Test</body></html>"
