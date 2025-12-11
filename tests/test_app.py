
import pytest
from typer.testing import CliRunner
from unittest.mock import patch, MagicMock
from m2g_image.app import app
from pathlib import Path

runner = CliRunner()

def test_app_pagination(test_data_dir, output_dir):
    """Test that app splits output into multiple files when batch_size is set."""
    
    input_csv = test_data_dir / "test.csv"
    output_png = output_dir / "paginated.png"
    
    # We mock generate_grid_html to avoid real processing
    with patch("m2g_image.app.generate_grid_html") as mock_gen:
        mock_gen.side_effect = lambda *args, **kwargs: kwargs["output_image_path"]
        
        # Run with batch size small enough to trigger splitting (assuming test.csv has > 2 rows)
        result = runner.invoke(app, [str(input_csv), "-o", str(output_png), "--n-items-per-page", "2"])
        
        assert result.exit_code == 0
        
    # If pagination happens, multiple calls
    # test.csv has 36 rows, batch 2 => 18 chunks
    assert mock_gen.call_count == 18
    
    # Check filenames
    filenames = [call.kwargs["output_image_path"] for call in mock_gen.call_args_list]
    
    # 36 items / 2 = 18 chunks. Max is 18 (2 digits). So padding is 02d.
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
    
    # We mock generate_grid_html to avoid real processing
    with patch("m2g_image.app.generate_grid_html") as mock_gen:
        mock_gen.side_effect = lambda *args, **kwargs: kwargs["output_image_path"]

        # Run with batch_size 2 for 36 items -> 18 chunks. len("18") is 2.
        # Expecting zero padding for filenames like myfile_01.png
        result = runner.invoke(app, [
            str(input_csv), 
            "-o", output_filename, 
            "--output-dir", str(target_output_dir),
            "--n-items-per-page", "2"
        ])
        
        assert result.exit_code == 0
        assert mock_gen.call_count == 18
        
        filenames = [call.kwargs["output_image_path"] for call in mock_gen.call_args_list]
        
        # Check first filename (should be inside custom_out and padded)
        # 01 because 1 < 10 and max is 18 (2 digits)
        expected_first = target_output_dir / "myfile_01.png"
        assert str(expected_first) in filenames
        
        # Check last filename
        expected_last = target_output_dir / "myfile_18.png"
        assert str(expected_last) in filenames
        
        # Check directory existence verified by app code? 
        # The app should create target_output_dir
        assert target_output_dir.exists()
