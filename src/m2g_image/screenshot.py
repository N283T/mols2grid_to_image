from pathlib import Path
from playwright.sync_api import sync_playwright


def capture_element_screenshot(
    html_file_path: str | Path,
    output_image_path: str | Path,
    selector: str = "#mols2grid",
    omit_background: bool = False,
) -> Path:
    """
    Captures a screenshot of a specific element in an HTML file using Playwright.

    Args:
        html_file_path: Path to the input HTML file.
        output_image_path: Path where the PNG will be saved.
        selector: CSS selector for the element to capture.
        omit_background: If True, omit the default white background.

    Returns:
        Path object of the output image.
    """
    html_file = Path(html_file_path).resolve()
    output_file = Path(output_image_path).resolve()

    if not html_file.exists():
        raise FileNotFoundError(f"HTML file not found: {html_file}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            page = browser.new_page()
            file_url = f"file://{html_file}"
            page.goto(file_url, wait_until="networkidle")

            locator = page.locator(selector)
            if locator.count() == 0:
                raise RuntimeError(f"Element not found: {selector}")

            locator.screenshot(path=str(output_file), omit_background=omit_background)
        finally:
            browser.close()

    return output_file
