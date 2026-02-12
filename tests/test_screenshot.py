import pytest
from m2g_image.screenshot import capture_element_screenshot


def test_capture_element_screenshot_real(output_dir):
    """
    Integration test: Actually launch Playwright and capture a screenshot.
    This requires a working Playwright environment.
    """

    html_content = """
    <html>
    <body>
        <div id="target" style="width:100px; height:100px; background:red;">Target</div>
        <div id="other">Other</div>
    </body>
    </html>
    """

    test_html = output_dir / "test_screenshot.html"
    test_html.write_text(html_content)

    output_png = output_dir / "screenshot.png"

    result_path = capture_element_screenshot(
        html_file_path=test_html, output_image_path=output_png, selector="#target"
    )

    assert result_path == output_png
    assert output_png.exists()
    assert output_png.stat().st_size > 0


def test_capture_element_not_found(output_dir):
    """Test error handling when element is missing."""

    html_content = "<html><body></body></html>"
    test_html = output_dir / "empty.html"
    test_html.write_text(html_content)

    with pytest.raises(RuntimeError, match="Element not found"):
        capture_element_screenshot(
            html_file_path=test_html,
            output_image_path=output_dir / "fail.png",
            selector="#nonexistent",
        )


def test_capture_file_not_found(output_dir):
    """Test error handling when HTML file does not exist."""

    with pytest.raises(FileNotFoundError, match="HTML file not found"):
        capture_element_screenshot(
            html_file_path=output_dir / "nonexistent.html",
            output_image_path=output_dir / "fail.png",
        )
