
from pathlib import Path
from playwright.sync_api import sync_playwright

def capture_element_screenshot(
    html_file_path: str | Path,
    output_image_path: str | Path,
    selector: str = "#mols2grid",
    **kwargs
) -> Path:
    """
    Captures a screenshot of a specific element in an HTML file using Playwright.
    
    Args:
        html_file_path: Path to the input HTML file.
        output_image_path: Path where the PNG will be saved.
        selector: CSS selector for the element to capture.
    
    Returns:
        Path object of the output image.
    """
    html_file = Path(html_file_path).resolve()
    output_file = Path(output_image_path).resolve()
    
    if not html_file.exists():
        raise FileNotFoundError(f"HTML file not found: {html_file}")

    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Go to file URL
        file_url = f"file://{html_file}"
        page.goto(file_url, wait_until="networkidle")
        
        # Locate element
        locator = page.locator(selector)
        
        if locator.count() == 0:
            browser.close()
            raise RuntimeError(f"Element not found: {selector}")
            
        # Helper to ensure background is white if transparent (common issue in screenshots)
        # We can inject style if needed, but for now just screenshot.
        
        locator.screenshot(path=str(output_file))
        browser.close()

    return output_file
