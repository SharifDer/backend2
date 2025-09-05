"""
Standalone Google Maps Traffic Analysis Module
Provides traffic analysis using Google Maps screenshots and color detection
"""
import os
import time
import math
from typing import Dict, Any, Optional, Tuple, Union
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from PIL import Image
import numpy as np
from collections import Counter

from app_logger import get_logger
logger = get_logger(__name__)

class GoogleMapsTrafficAnalyzer:
    """Standalone Google Maps traffic analyzer using screenshots and color detection"""
    
    # Traffic color ranges in RGB - smaller ranges around specific colors
    TRAFFIC_COLORS = {
        'dark_red': [(166, 26, 26), (186, 46, 46)],    # Dark red traffic around rgb(176,36,36)
        'red': [(234, 70, 54), (254, 90, 74)],         # Red traffic around rgb(244,80,64)
        'yellow': [(246, 194, 58), (255, 214, 78)],    # Yellow traffic around rgb(256,204,68) - fixed max RGB
        'green': [(14, 218, 146), (34, 238, 166)],     # Green traffic around rgb(24,228,156)
        'gray': [(166, 178, 194), (186, 198, 214)]     # Gray (no data) around rgb(176,188,204)
    }
    
    TRAFFIC_SCORES = {
        'dark_red': 100,
        'red': 100, 
        'yellow': 70,
        'green': 30,
        'gray': 0
    }
    
    def __init__(self, cleanup_screenshots: bool = True):
        """
        Initialize the analyzer
        
        Args:
            cleanup_screenshots: Whether to delete screenshots after analysis
        """
        self.driver = None
        self.cleanup_screenshots = cleanup_screenshots
        
        # Direction mappings for storefront orientation
        self.DIRECTION_ANGLES = {
            'north': 0, 'n': 0,
            'northeast': 45, 'ne': 45,
            'east': 90, 'e': 90,
            'southeast': 135, 'se': 135,
            'south': 180, 's': 180,
            'southwest': 225, 'sw': 225,
            'west': 270, 'w': 270,
            'northwest': 315, 'nw': 315
        }

        self.DAY_MAP = {
            "sunday": 0,
            "monday": 1,
            "tuesday": 2,
            "wednesday": 3,
            "thursday": 4,
            "friday": 5,
            "saturday": 6,
        }
        self.TIME_MAP = {"8:30AM": 28, "6:00PM": 135, "10:00PM": 180}
        
    def setup_webdriver(self) -> Optional[webdriver.Chrome]:
        """Setup Chrome webdriver with specific options for Google Maps"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1200,800")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--allow-running-insecure-content")
        chrome_options.add_argument("--disable-features=VizDisplayCompositor")
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            return self.driver
        except Exception as e:
            logger.error(f"Could not setup webdriver: {e}")
            return None
    
    def cleanup_webdriver(self):
        """Safely cleanup webdriver"""
        if self.driver:
            try:
                self.driver.quit()
                # Add a small delay to ensure the driver is fully closed
                time.sleep(0.5)
                self.driver = None
            except Exception as e:
                logger.error(f"Error closing webdriver: {e}")
                self.driver = None
    
    def get_google_maps_url(self, lat: float, lng: float, zoom: int = 18) -> str:
        """Generate Google Maps URL with traffic layer enabled at 20m zoom level with North up"""
        # Enable traffic layer by adding traffic parameter
        # Zoom level 18 corresponds to approximately 20m scale
        # heading=0 ensures North is pointing up
        base_url = "https://www.google.com/maps"
        # Enhanced URL with explicit traffic layer parameters
        params = f"@{lat},{lng},{zoom}z/data=!5m1!1e1"  # layer=t explicitly enables traffic
        return f"{base_url}/{params}"
    
    def capture_google_maps_screenshot(self, lat: float, lng: float, 
                                     filename: str = "traffic_screenshot", 
                                     save_to_static: bool = False, 
                                     day_of_week: Optional[Union[str, int]] = None,
                                     target_time: Optional[str] = None) -> Optional[str]:
        """Capture screenshot of Google Maps with traffic at specified location"""
        if not self.driver:
            logger.error("Webdriver not initialized")
            return None
            
        try:
            # Generate Google Maps URL with traffic (zoom 18 = 20m scale)
            maps_url = self.get_google_maps_url(lat, lng, zoom=18)
            logger.info(f"Loading Google Maps URL: {maps_url}")
            
            # Load Google Maps
            self.driver.get(maps_url)
            
            # Wait for the page to load
            time.sleep(5)
            
            # Try to accept cookies if present
            try:
                accept_button = WebDriverWait(self.driver, 3).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Accept') or contains(text(), 'I agree')]"))
                )
                accept_button.click()
                time.sleep(2)
            except Exception:
                pass  # Cookie banner might not be present
            
            # # Enhanced traffic layer activation
            # self._ensure_traffic_layer_enabled()
            
            # Wait for traffic data to load
            time.sleep(3)
            
            # # Verify traffic is loaded and retry if needed
            # traffic_loaded = self._verify_traffic_loaded()
            # if not traffic_loaded:
            #     logger.warning("Traffic not detected after first attempt, trying additional methods...")
                
            #     # Try alternative traffic activation
            #     try:
            #         # Method: Reload page with explicit traffic parameter
            #         current_url = self.driver.current_url
            #         if "&layer=t" not in current_url and "?layer=t" not in current_url:
            #             separator = "&" if "?" in current_url else "?"
            #             traffic_url = current_url + separator + "layer=t"
            #             self.driver.get(traffic_url)
            #             time.sleep(5)
                        
            #             # Try the enhanced activation again
            #             self._ensure_traffic_layer_enabled()
            #             time.sleep(3)
                        
            #             # Check again
            #             traffic_loaded = self._verify_traffic_loaded()
            #             if traffic_loaded:
            #                 logger.info("Traffic successfully loaded after URL reload")
            #     except Exception as retry_error:
            #         logger.warning(f"Traffic retry failed: {retry_error}")
                
            #     if not traffic_loaded:
            #         logger.warning("Traffic still not detected - proceeding with current map state")
            # else:
            #     logger.info("Traffic layer successfully loaded and verified")
            
            # Trigger traffic data loading by zooming in and out
            # This helps ensure Google loads traffic data for the specific location

            # Zoom in once to trigger data refresh
            self.driver.execute_script("window.dispatchEvent(new WheelEvent('wheel', {deltaY: -100, bubbles: true}));")
            time.sleep(2)
            
            # Zoom out twice to get back to 20m scale and trigger traffic refresh
            self.driver.execute_script("window.dispatchEvent(new WheelEvent('wheel', {deltaY: 100, bubbles: true}));")
            time.sleep(1)
            self.driver.execute_script("window.dispatchEvent(new WheelEvent('wheel', {deltaY: 100, bubbles: true}));")
            time.sleep(2)

            # Select traffic type (typical or live) if possible
            try:
                # Click the traffic layer button
                traffic_button = WebDriverWait(self.driver, 3).until(
                    EC.element_to_be_clickable(
                        (
                            By.XPATH,
                            '//*[@id="layer"]/div/div/span/button',
                        )
                    )
                )
                traffic_button.click()
                time.sleep(0.3)

                # Click the "Typical traffic" option if available
                self.driver.find_element(
                    By.XPATH, '//*[@id="action-menu"]/div/div[2]'
                ).click()
                time.sleep(1)

                # Choose a day for typical traffic if specified
                if day_of_week is not None:
                    days = self.driver.find_element(
                        By.XPATH, '//*[@id="layer"]/div/div/div/div[1]'
                    ).find_elements(By.TAG_NAME, "button")

                    if isinstance(day_of_week, int) and 0 <= day_of_week <= 6:
                        days[day_of_week].click()
                    else:
                        days[self.DAY_MAP.get(str(day_of_week).strip().lower(), 0)].click()

                    time.sleep(1)  # wait for UI update

                # Hour selection code can be added here if needed
                if target_time is not None:
                    try:
                        pos = self.TIME_MAP.get(target_time.upper().strip().replace(" ", ""), 0)
                        actions = ActionChains(self.driver)

                        slider = WebDriverWait(self.driver, 3).until(
                            EC.presence_of_element_located(
                                (
                                    By.XPATH,
                                    '//*[@id="layer"]/div/div/div/div[2]/div/div[1]/span[2]',
                                )
                            )
                        )

                        actions.click_and_hold(slider).move_by_offset(-35, 0).release().perform() # Return the cursor to the beginning
                        time.sleep(0.2)
                        actions.click_and_hold(slider).move_by_offset(pos, 0).release().perform() # Set the cursor to the specific time position

                        time.sleep(1)  # wait for UI update
                    except Exception:
                        logger.info("Failed to adjust the traffic time slider.")

                logger.info("Typical traffic mode selection attempted.")
            except Exception as e:
                logger.info("Live traffic mode selection attempted.")

            # Generate screenshot path
            if save_to_static:
                # Create static/traffic_screenshots directory if it doesn't exist
                static_dir = os.path.join("static", "traffic_screenshots")
                os.makedirs(static_dir, exist_ok=True)
                
                # Generate unique filename with timestamp
                timestamp = int(time.time())
                screenshot_filename = f"traffic_{timestamp}_{lat}_{lng}.png"
                screenshot_path = os.path.join(static_dir, screenshot_filename)
            else:
                screenshot_path = f"{filename}_{lat}_{lng}.png"
            
            # Take screenshot with retry logic
            screenshot_success = False
            for attempt in range(3):  # Try up to 3 times
                try:
                    self.driver.save_screenshot(screenshot_path)
                    screenshot_success = True
                    break
                except Exception as screenshot_error:
                    logger.warning(f"Screenshot attempt {attempt + 1} failed: {screenshot_error}")
                    if attempt < 2:  # Don't sleep on the last attempt
                        time.sleep(1)
            
            if not screenshot_success:
                raise Exception("Failed to capture screenshot after 3 attempts")
            
            logger.info(f"Screenshot captured at 20m zoom level: {screenshot_path}")
            return screenshot_path
            
        except Exception as e:
            logger.error(f"Failed to capture Google Maps screenshot: {e}")
            return None
    
    def color_distance(self, color1: Tuple[int, int, int], color2: Tuple[int, int, int]) -> float:
        """Calculate Euclidean distance between two RGB colors"""
        try:
            return math.sqrt(sum((a - b) ** 2 for a, b in zip(color1, color2)))
        except OverflowError:
            # Handle overflow by using a simpler distance calculation
            return abs(color1[0] - color2[0]) + abs(color1[1] - color2[1]) + abs(color1[2] - color2[2])
    
    def classify_traffic_color(self, rgb: Tuple[int, int, int]) -> str:
        """Classify RGB color into traffic categories"""
        min_distance = float('inf')
        best_match = 'gray'
        
        for traffic_type, (min_rgb, max_rgb) in self.TRAFFIC_COLORS.items():
            # Check if color is within range
            if all(min_val <= rgb[i] <= max_val for i, (min_val, max_val) in enumerate(zip(min_rgb, max_rgb))):
                return traffic_type
            
            # If not in range, find closest match
            center_rgb = tuple((min_rgb[i] + max_rgb[i]) // 2 for i in range(3))
            distance = self.color_distance(rgb, center_rgb)
            if distance < min_distance:
                min_distance = distance
                best_match = traffic_type
        
        return best_match
    
    def add_pin_to_image(self, image_path: str, storefront_direction: str = 'north') -> str:
        """Add a pin marker and directional arrow to the center of the image for verification"""
        try:
            from PIL import ImageDraw
            
            # Add a small delay to ensure the file is not locked
            time.sleep(0.2)
            
            # Load the image
            image = Image.open(image_path)
            draw = ImageDraw.Draw(image)
            
            # Get image center
            width, height = image.size
            center_x, center_y = width // 2, height // 2
            
            # Draw a pin-like marker
            pin_size = 10
            
            # Pin body (red circle)
            draw.ellipse([
                center_x - pin_size, center_y - pin_size,
                center_x + pin_size, center_y + pin_size
            ], fill='red', outline='darkred', width=2)
            
            # Pin point (small triangle below)
            draw.polygon([
                (center_x, center_y + pin_size),
                (center_x - 4, center_y + pin_size + 8),
                (center_x + 4, center_y + pin_size + 8)
            ], fill='darkred')
            
            # Add directional arrow for storefront direction
            self._add_directional_arrow(image, center_x, center_y, storefront_direction)
            
            # Generate pinned image path
            pinned_path = image_path.replace('.png', '_pinned.png')
            
            # Ensure we close the original image before saving
            image_copy = image.copy()
            image.close()
            
            # Save the modified image
            image_copy.save(pinned_path)
            image_copy.close()
            
            logger.info(f"Pin and directional arrow added to image: {pinned_path}")
            return pinned_path
            
        except Exception as e:
            logger.error(f"Failed to add pin to image: {e}")
            return image_path  # Return original path if pin addition fails
    
    def _add_directional_arrow(self, image: Image.Image, center_x: int, center_y: int, direction: str):
        """Add a directional arrow pointing towards the storefront direction"""
        try:
            # Try to load the arrow image from the specified path
            arrow_path = r"c:\Users\u_je_\Downloads\image-removebg-preview.png"
            
            # If the file doesn't exist locally, create a simple arrow
            if not os.path.exists(arrow_path):
                self._draw_simple_arrow(image, center_x, center_y, direction)
                return
            
            # Load and process the arrow image
            arrow_img = Image.open(arrow_path)
            
            # Resize arrow to appropriate size (about 30x30 pixels)
            arrow_size = (30, 30)
            arrow_img = arrow_img.resize(arrow_size, Image.Resampling.LANCZOS)
            
            # Get the direction angle and rotate the arrow
            direction_angle = self.DIRECTION_ANGLES.get(direction.lower(), 0)
            
            # Rotate the arrow to point in the correct direction
            # Note: PIL rotation is counterclockwise, and we want 0° to point North (up)
            # So we need to adjust: North=0° -> -90° rotation (to point up)
            rotation_angle = -(direction_angle - 90)
            rotated_arrow = arrow_img.rotate(rotation_angle, expand=True, fillcolor=(0, 0, 0, 0))
            
            # Calculate arrow position (offset from center pin)
            arrow_distance = 40  # Distance from pin center
            arrow_angle_rad = math.radians(direction_angle)
            arrow_x = int(center_x + arrow_distance * math.cos(arrow_angle_rad) - rotated_arrow.width // 2)
            arrow_y = int(center_y - arrow_distance * math.sin(arrow_angle_rad) - rotated_arrow.height // 2)
            
            # Paste the arrow onto the image
            if rotated_arrow.mode == 'RGBA':
                image.paste(rotated_arrow, (arrow_x, arrow_y), rotated_arrow)
            else:
                image.paste(rotated_arrow, (arrow_x, arrow_y))
            
            logger.info(f"Directional arrow added pointing {direction}")
            
        except Exception as e:
            logger.warning(f"Could not add custom arrow image: {e}, falling back to simple arrow")
            self._draw_simple_arrow(image, center_x, center_y, direction)
    
    def _draw_simple_arrow(self, image: Image.Image, center_x: int, center_y: int, direction: str):
        """Draw a simple directional arrow using PIL drawing functions"""
        try:
            from PIL import ImageDraw
            
            draw = ImageDraw.Draw(image)
            
            # Get direction angle
            direction_angle = self.DIRECTION_ANGLES.get(direction.lower(), 0)
            angle_rad = math.radians(direction_angle)
            
            # Arrow parameters
            arrow_length = 25
            arrow_color = 'blue'
            
            # Calculate arrow end point
            end_x = center_x + arrow_length * math.cos(angle_rad)
            end_y = center_y - arrow_length * math.sin(angle_rad)  # Negative because Y is inverted
            
            # Draw arrow shaft
            draw.line([(center_x, center_y), (end_x, end_y)], fill=arrow_color, width=3)
            
            # Calculate arrowhead points
            head_length = 8
            head_angle1 = angle_rad + math.radians(150)  # 30 degrees from shaft
            head_angle2 = angle_rad - math.radians(150)  # 30 degrees from shaft
            
            head_x1 = end_x + head_length * math.cos(head_angle1)
            head_y1 = end_y - head_length * math.sin(head_angle1)
            head_x2 = end_x + head_length * math.cos(head_angle2)
            head_y2 = end_y - head_length * math.sin(head_angle2)
            
            # Draw arrowhead
            draw.polygon([(end_x, end_y), (head_x1, head_y1), (head_x2, head_y2)], fill=arrow_color)
            
            # Add direction label
            label_distance = 35
            label_x = center_x + label_distance * math.cos(angle_rad)
            label_y = center_y - label_distance * math.sin(angle_rad)
            
            # Draw text background for better visibility
            text = direction.upper()
            draw.text((label_x, label_y), text, fill='white', anchor='mm')
            
            logger.info(f"Simple arrow drawn pointing {direction}")
            
        except Exception as e:
            logger.error(f"Failed to draw simple arrow: {e}")
    
    def find_storefront_in_direction(self, image_array: np.ndarray, center_x: int, center_y: int, 
                                   direction: str, max_distance: int = 150) -> Dict[str, Any]:
        """
        Find the closest traffic color in the specified direction using cone-based search
        
        Args:
            image_array: The image as numpy array
            center_x, center_y: Center coordinates of the image
            direction: Storefront direction (n, ne, e, se, s, sw, w, nw)
            max_distance: Maximum distance to search in pixels
            
        Returns:
            Dict with storefront analysis results
        """
        direction_angle = self.DIRECTION_ANGLES.get(direction.lower(), 0)
        height, width = image_array.shape[:2]
        
        # Convert angle to radians
        angle_rad = math.radians(direction_angle)
        
        # Cone parameters: 30-degree cone (±15 degrees from center direction)
        cone_half_angle = math.radians(15)
        
        storefront_result = {
            'found': False,
            'color': 'gray',
            'distance': max_distance,
            'score': 0,
            'direction': direction,
            'searched_pixels': 0
        }
        
        # Search in expanding circles from center
        for distance in range(5, max_distance, 2):  # Start from 5px, step by 2
            pixels_in_ring = []
            
            # Check pixels in a ring at this distance
            for angle_offset in range(-180, 180, 2):  # Check every 2 degrees
                current_angle = angle_rad + math.radians(angle_offset)
                
                # Check if this angle is within our cone
                angle_diff = abs(angle_offset)
                if angle_diff > math.degrees(cone_half_angle):
                    continue
                
                # Calculate pixel position
                x = int(center_x + distance * math.cos(current_angle))
                y = int(center_y - distance * math.sin(current_angle))  # Negative because image Y is inverted
                
                # Check if pixel is within image bounds
                if 0 <= x < width and 0 <= y < height:
                    rgb = tuple(image_array[y, x][:3])
                    color_type = self.classify_traffic_color(rgb)
                    
                    # Only consider traffic colors (not gray/no-data)
                    if color_type != 'gray':
                        pixels_in_ring.append({
                            'color': color_type,
                            'distance': distance,
                            'position': (x, y),
                            'rgb': rgb
                        })
                        storefront_result['searched_pixels'] += 1
            
            # If we found traffic colors at this distance, take the most common one
            if pixels_in_ring:
                colors_at_distance = [p['color'] for p in pixels_in_ring]
                most_common_color = Counter(colors_at_distance).most_common(1)[0][0]
                
                storefront_result.update({
                    'found': True,
                    'color': most_common_color,
                    'distance': distance,
                    'score': self.TRAFFIC_SCORES[most_common_color],
                    'pixels_found': len(pixels_in_ring)
                })
                
                logger.info(f"Storefront found in direction {direction}: {most_common_color} at {distance}px")
                break
        
        return storefront_result
    
    def analyze_traffic_in_image(self, image_path: str, center_lat: float, center_lng: float, 
                               storefront_direction: str = 'north') -> Dict[str, Any]:
        """Analyze traffic colors in the screenshot image with directional storefront detection"""
        try:
            # Load the image
            image = Image.open(image_path)
            image_array = np.array(image)
            
            height, width = image_array.shape[:2]
            center_x, center_y = width // 2, height // 2
            
            # Define analysis zones (in pixels from center)
            # Zoom level 18 corresponds to approximately 20m scale
            pixels_per_meter = 1.5  # Adjusted for zoom level 18 (20m scale)
            
            zones = {
                'storefront': int(25 * pixels_per_meter),    # 25m radius for storefront
                '50m': int(50 * pixels_per_meter),           # 50m radius
                '100m': int(100 * pixels_per_meter),         # 100m radius  
                '150m': int(150 * pixels_per_meter)          # 150m radius
            }
            
            traffic_analysis = {
                'storefront_score': 0,
                'area_scores': {},
                'total_pixels_analyzed': 0,
                'color_distribution': {color: 0 for color in self.TRAFFIC_COLORS.keys()},
                'storefront_direction': storefront_direction,
                'storefront_details': {}
            }
            
            # Find storefront in the specified direction using cone-based search
            storefront_result = self.find_storefront_in_direction(
                image_array, center_x, center_y, storefront_direction, zones['150m']
            )
            
            traffic_analysis['storefront_details'] = storefront_result
            traffic_analysis['storefront_score'] = storefront_result['score']
            
            # Update color distribution with storefront findings
            if storefront_result['found']:
                traffic_analysis['color_distribution'][storefront_result['color']] += storefront_result.get('pixels_found', 1)
            
            # Analyze different distance zones (surrounding area analysis)
            for zone_name, zone_radius in zones.items():
                if zone_name == 'storefront':
                    continue
                    
                zone_colors = []
                pixels_in_zone = 0
                
                # Analyze annular region (between this radius and previous)
                prev_radius = zones.get('50m' if zone_name == '100m' else 
                                      '100m' if zone_name == '150m' else 'storefront', 0)
                
                for y in range(max(0, center_y - zone_radius), 
                              min(height, center_y + zone_radius + 1)):
                    for x in range(max(0, center_x - zone_radius), 
                                  min(width, center_x + zone_radius + 1)):
                        distance = math.sqrt((x - center_x)**2 + (y - center_y)**2)
                        if prev_radius < distance <= zone_radius:
                            rgb = tuple(image_array[y, x][:3])
                            color_type = self.classify_traffic_color(rgb)
                            zone_colors.append(color_type)
                            pixels_in_zone += 1
                
                # Calculate zone score
                if zone_colors:
                    color_counts = Counter(zone_colors)
                    zone_score = sum(
                        count * self.TRAFFIC_SCORES[color] 
                        for color, count in color_counts.items()
                    ) / len(zone_colors)
                    
                    traffic_analysis['area_scores'][zone_name] = {
                        'score': zone_score,
                        'pixels': pixels_in_zone,
                        'colors': dict(color_counts)
                    }
                    
                    # Update overall color distribution
                    for color, count in color_counts.items():
                        traffic_analysis['color_distribution'][color] += count
            
            traffic_analysis['total_pixels_analyzed'] = sum(traffic_analysis['color_distribution'].values())
            
            return traffic_analysis
            
        except Exception as e:
            logger.error(f"Failed to analyze traffic in image: {e}")
            return {}
    
    def calculate_final_traffic_score(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate final traffic score based on analysis"""
        if not analysis:
            return {'score': 0, 'details': 'Analysis failed'}
        
        # 70% weight for storefront traffic
        storefront_score = analysis.get('storefront_score', 0)
        storefront_weight = 0.7
        
        # 30% weight for surrounding area traffic with distance multipliers
        area_weight = 0.3
        area_score = 0
        total_weighted_pixels = 0
        
        area_scores = analysis.get('area_scores', {})
        multipliers = {'50m': 1.0, '100m': 0.5, '150m': 0.25}
        
        for zone, multiplier in multipliers.items():
            if zone in area_scores:
                zone_data = area_scores[zone]
                zone_score = zone_data.get('score', 0)
                zone_pixels = zone_data.get('pixels', 0)
                
                weighted_contribution = zone_score * multiplier * zone_pixels
                area_score += weighted_contribution
                total_weighted_pixels += zone_pixels * multiplier
        
        if total_weighted_pixels > 0:
            area_score = area_score / total_weighted_pixels
        
        # Calculate final score
        final_score = (storefront_score * storefront_weight) + (area_score * area_weight)
        
        return {
            'score': round(final_score, 2),
            'storefront_score': storefront_score,
            'area_score': round(area_score, 2),
            'storefront_weight': storefront_weight,
            'area_weight': area_weight,
            'total_pixels_analyzed': analysis.get('total_pixels_analyzed', 0),
            'color_distribution': analysis.get('color_distribution', {}),
            'area_details': area_scores
        }

    def analyze_location_traffic(self, lat: float, lng: float, save_to_static: bool = False, 
                               storefront_direction: str = 'north', 
                               day_of_week: Optional[Union[str, int]] = None, 
                               target_time: Optional[str] = None) -> Dict[str, Any]:
        """
        Main method to analyze traffic using Google Maps screenshots
        
        Args:
            lat: Latitude of the location
            lng: Longitude of the location
            save_to_static: Whether to save screenshot to static folder
            storefront_direction: Direction the storefront faces (n, ne, e, se, s, sw, w, nw)
            day_of_week: Day of week for historical traffic (e.g., 'Monday', 0-6)
            target_time: Target Time for historical traffic ('8:30AM', '6:00PM', '10:00PM')

        Returns:
            Dict containing traffic analysis results
        """
        try:
            # Setup webdriver
            if not self.setup_webdriver():
                raise Exception("Failed to setup webdriver")
            
            # Capture screenshot
            screenshot_path = self.capture_google_maps_screenshot(lat, lng, save_to_static=save_to_static, 
                                                                  day_of_week=day_of_week, target_time=target_time)
            if not screenshot_path:
                raise Exception("Failed to capture screenshot")
            
            # Add pin to image for verification
            pinned_screenshot_path = self.add_pin_to_image(screenshot_path, storefront_direction)
            
            # Initialize image_id for static storage
            image_id = None
            
            # If saving to static, handle the static file creation
            if save_to_static:
                static_dir = os.path.join("static", "traffic_screenshots")
                os.makedirs(static_dir, exist_ok=True)
                
                timestamp = int(time.time())
                static_filename = f"traffic_{timestamp}_{lat}_{lng}_pinned.png"
                static_pinned_path = os.path.join(static_dir, static_filename)
                
                # Copy pinned image to static location with retry logic
                if os.path.exists(pinned_screenshot_path):
                    try:
                        import shutil
                        time.sleep(0.5)  # Brief pause to ensure file is not locked
                        shutil.copy2(pinned_screenshot_path, static_pinned_path)
                        image_id = os.path.splitext(static_filename)[0]  # Remove .png extension
                        logger.info(f"Pinned image saved to static: {static_pinned_path}")
                    except Exception as copy_error:
                        logger.warning(f"Could not copy to static folder: {copy_error}")
                        # Continue with local analysis but note the copy failure
                        pass
            
            # Analyze traffic in the image with storefront direction
            analysis = self.analyze_traffic_in_image(pinned_screenshot_path, lat, lng, storefront_direction)
            if not analysis:
                raise Exception("Failed to analyze traffic")
            
            # Calculate final score
            result = self.calculate_final_traffic_score(analysis)
            
            # Add metadata
            result.update({
                'method': 'google_maps_screenshot',
                'screenshot_path': pinned_screenshot_path if not self.cleanup_screenshots or save_to_static else None,
                'image_id': image_id,
                'coordinates': {'lat': lat, 'lng': lng},
                'storefront_direction': storefront_direction,
                'analysis_timestamp': time.time(),
                'storefront_details': analysis.get('storefront_details', {})
            })
            
            # Cleanup screenshot files if requested and not saved to static
            if self.cleanup_screenshots and not save_to_static:
                try:
                    # Add a small delay to ensure files are not locked
                    time.sleep(0.5)
                    
                    if os.path.exists(screenshot_path):
                        os.remove(screenshot_path)
                        logger.debug(f"Cleaned up original screenshot: {screenshot_path}")
                        
                    if os.path.exists(pinned_screenshot_path) and pinned_screenshot_path != screenshot_path:
                        os.remove(pinned_screenshot_path)
                        logger.debug(f"Cleaned up pinned screenshot: {pinned_screenshot_path}")
                        
                except PermissionError as pe:
                    logger.warning(f"Could not cleanup screenshot files (permission denied): {pe}")
                except Exception as cleanup_error:
                    logger.warning(f"Could not cleanup screenshot files: {cleanup_error}")
            
            logger.info(f"Google Maps traffic analysis completed for {lat}, {lng} facing {storefront_direction}: Score {result['score']}")
            return result
            
        except Exception as e:
            logger.error(f"Google Maps traffic analysis failed: {e}")
            return {
                'score': 0,
                'method': 'google_maps_screenshot',  
                'error': str(e),
                'coordinates': {'lat': lat, 'lng': lng},
                'storefront_direction': storefront_direction
            }
        
        finally:
            self.cleanup_webdriver()
    
    def _ensure_traffic_layer_enabled(self):
        """Enhanced method to ensure traffic layer is enabled with multiple approaches"""
        try:
            logger.info("Attempting to enable traffic layer...")
            
            # Method 1: Try to find and click traffic button by aria-label
            try:
                traffic_button = WebDriverWait(self.driver, 3).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Traffic']"))
                )
                traffic_button.click()
                logger.info("Traffic enabled via aria-label button")
                time.sleep(2)
                return
            except Exception:
                pass
            
            # Method 2: Try to find traffic button by text content
            try:
                traffic_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Traffic')]")
                traffic_button.click()
                logger.info("Traffic enabled via text content button")
                time.sleep(2)
                return
            except Exception:
                pass
            
            # Method 3: Try to find the layers menu and enable traffic
            try:
                # Look for layers button (menu icon)
                layers_button = self.driver.find_element(By.XPATH, "//button[@aria-label='Layers' or @aria-label='Menu' or contains(@class, 'layers')]")
                layers_button.click()
                time.sleep(1)
                
                # Try to find traffic option in the menu
                traffic_option = self.driver.find_element(By.XPATH, "//div[contains(text(), 'Traffic') or contains(text(), 'traffic')]")
                traffic_option.click()
                logger.info("Traffic enabled via layers menu")
                time.sleep(2)
                return
            except Exception:
                pass
            
            # Method 4: Use keyboard shortcut (Ctrl+Shift+T for traffic in some versions)
            try:
                from selenium.webdriver.common.keys import Keys
                from selenium.webdriver.common.action_chains import ActionChains
                
                actions = ActionChains(self.driver)
                actions.key_down(Keys.CONTROL).key_down(Keys.SHIFT).send_keys('t').key_up(Keys.SHIFT).key_up(Keys.CONTROL).perform()
                logger.info("Traffic toggle attempted via keyboard shortcut")
                time.sleep(2)
                return
            except Exception:
                pass
            
            # Method 5: Try to inject traffic layer via JavaScript
            try:
                # Attempt to enable traffic layer via JavaScript
                traffic_script = """
                // Try to find and enable traffic layer
                var buttons = document.querySelectorAll('button, div');
                for (var i = 0; i < buttons.length; i++) {
                    var btn = buttons[i];
                    if (btn.textContent && (btn.textContent.toLowerCase().includes('traffic') || 
                        btn.getAttribute('aria-label') && btn.getAttribute('aria-label').toLowerCase().includes('traffic'))) {
                        btn.click();
                        console.log('Traffic layer enabled via JavaScript');
                        break;
                    }
                }
                """
                self.driver.execute_script(traffic_script)
                logger.info("Traffic enable attempted via JavaScript")
                time.sleep(2)
                return
            except Exception:
                pass
            
            # Method 6: Force reload with explicit traffic parameter
            try:
                current_url = self.driver.current_url
                if "layer=t" not in current_url:
                    # Add traffic layer parameter to current URL
                    if "?" in current_url:
                        traffic_url = current_url + "&layer=t"
                    else:
                        traffic_url = current_url + "?layer=t"
                    
                    self.driver.get(traffic_url)
                    logger.info("Traffic enabled via URL parameter injection")
                    time.sleep(3)
                    return
            except Exception:
                pass
            
            logger.warning("All traffic layer activation methods failed - proceeding with current state")
            
        except Exception as e:
            logger.error(f"Error in traffic layer activation: {e}")
    
    def _verify_traffic_loaded(self) -> bool:
        """Verify if traffic data is actually loaded by taking a quick screenshot and checking for traffic colors"""
        try:
            # Take a temporary screenshot to check traffic colors
            temp_screenshot = "temp_traffic_check.png"
            self.driver.save_screenshot(temp_screenshot)
            
            # Quick analysis to see if traffic colors are present
            image = Image.open(temp_screenshot)
            image_array = np.array(image)
            
            # Sample center area for traffic colors
            height, width = image_array.shape[:2]
            center_x, center_y = width // 2, height // 2
            sample_size = 100  # 100x100 pixel area around center
            
            traffic_pixel_count = 0
            total_sampled = 0
            
            for y in range(max(0, center_y - sample_size//2), min(height, center_y + sample_size//2)):
                for x in range(max(0, center_x - sample_size//2), min(width, center_x + sample_size//2)):
                    rgb = tuple(image_array[y, x][:3])
                    color_type = self.classify_traffic_color(rgb)
                    total_sampled += 1
                    
                    # Count pixels that are actual traffic colors (not gray/no-data)
                    if color_type in ['dark_red', 'red', 'yellow', 'green']:
                        traffic_pixel_count += 1
            
            # Cleanup temp file
            try:
                os.remove(temp_screenshot)
            except Exception:
                pass
            
            # Consider traffic loaded if we find traffic colors in at least 1% of sampled pixels
            traffic_ratio = traffic_pixel_count / total_sampled if total_sampled > 0 else 0
            traffic_loaded = traffic_ratio > 0.01
            
            logger.info(f"Traffic verification: {traffic_pixel_count}/{total_sampled} traffic pixels ({traffic_ratio:.3f}), loaded: {traffic_loaded}")
            return traffic_loaded
            
        except Exception as e:
            logger.warning(f"Could not verify traffic loading: {e}")
            return False  # Assume not loaded if verification fails

# Standalone functions for easy usage
def analyze_traffic_at_location(lat: float, lng: float, cleanup_screenshots: bool = True, 
                              save_to_static: bool = False, storefront_direction: str = 'north', 
                              day_of_week: Optional[Union[str, int]] = None,
                              target_time: Optional[str] = None) -> Dict[str, Any]:
    """
    Standalone function to analyze traffic at a specific location
    
    Args:
        lat: Latitude of the location
        lng: Longitude of the location
        cleanup_screenshots: Whether to delete screenshots after analysis (ignored if save_to_static=True)
        save_to_static: Whether to save screenshot to static folder for web access
        storefront_direction: Direction the storefront faces (n, ne, e, se, s, sw, w, nw)
        day_of_week: Day of week for historical traffic (e.g., 'Monday', 0-6)
        target_time: Target Time for historical traffic ('8:30AM', '6:00PM', '10:00PM')

    Returns:
        Dict containing traffic analysis results
    """
    analyzer = GoogleMapsTrafficAnalyzer(cleanup_screenshots=cleanup_screenshots)
    return analyzer.analyze_location_traffic(lat, lng, save_to_static=save_to_static, 
                                           storefront_direction=storefront_direction,
                                           day_of_week=day_of_week,
                                           target_time=target_time)


def compare_multiple_locations(locations: list, cleanup_screenshots: bool = True) -> list:
    """
    Analyze traffic for multiple locations and compare them
    
    Args:
        locations: List of dicts with 'lat', 'lng', optional 'name', and optional 'storefront_direction' keys
        cleanup_screenshots: Whether to delete screenshots after analysis
        
    Returns:
        List of locations with traffic analysis results, sorted by score
    """
    analyzer = GoogleMapsTrafficAnalyzer(cleanup_screenshots=cleanup_screenshots)
    results = []
    
    for location in locations:
        try:
            storefront_direction = location.get('storefront_direction', 'north')
            result = analyzer.analyze_location_traffic(
                location['lat'], location['lng'], 
                storefront_direction=storefront_direction,
                day_of_week=location["day_of_week"],
                target_time=location["target_time"]
            )
            result['name'] = location.get('name', f"Location_{location['lat']}_{location['lng']}")
            results.append(result)
        except Exception as e:
            logger.error(f"Failed to analyze location {location}: {e}")
            results.append({
                'name': location.get('name', f"Location_{location['lat']}_{location['lng']}"),
                'score': 0,
                'error': str(e),
                'coordinates': {'lat': location['lat'], 'lng': location['lng']},
                'storefront_direction': location.get('storefront_direction', 'north')
            })
    
    # Sort by score (descending)
    results.sort(key=lambda x: x.get('score', 0), reverse=True)
    
    return results
