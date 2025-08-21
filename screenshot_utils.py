import os
import time
import base64
import logging
from typing import Optional, Tuple
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

logger = logging.getLogger(__name__)

def setup_webdriver() -> Optional[webdriver.Chrome]:
    """Setup Chrome webdriver for screenshots"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1200,800")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        return driver
    except Exception as e:
        logger.warning(f"Could not setup webdriver for screenshots: {e}")
        return None

def capture_map_screenshot(map_obj, filename: str, driver: Optional[webdriver.Chrome] = None) -> Tuple[Optional[str], Optional[str]]:
    """Capture screenshot of folium map"""
    if driver is None:
        logger.warning(f"No webdriver available for {filename}")
        return None, None
    
    try:
        # Save map to temporary HTML
        temp_html = f"temp_{filename}.html"
        map_obj.save(temp_html)
        
        # Load the HTML file
        file_path = os.path.abspath(temp_html)
        driver.get(f"file://{file_path}")
        
        # Wait for map to load
        time.sleep(3)
        
        # Take screenshot
        screenshot_path = f"{filename}.png"
        driver.save_screenshot(screenshot_path)
        
        # Clean up temp file
        if os.path.exists(temp_html):
            os.remove(temp_html)
        
        logger.info(f"Screenshot saved: {screenshot_path}")
        
        # Convert to base64 for embedding
        with open(screenshot_path, 'rb') as img_file:
            img_base64 = base64.b64encode(img_file.read()).decode()
        
        return screenshot_path, img_base64
        
    except Exception as e:
        logger.error(f"Screenshot failed for {filename}: {e}")
        return None, None

def cleanup_webdriver(driver: Optional[webdriver.Chrome]) -> None:
    """Safely cleanup webdriver"""
    if driver:
        try:
            driver.quit()
        except Exception as e:
            logger.error(f"Error closing webdriver: {e}")