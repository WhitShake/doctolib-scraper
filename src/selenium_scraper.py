# src/selenium_scraper.py
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import json
import logging
from typing import Dict, Optional, List
from sqlalchemy.orm import Session

from models import Doctor, Department
from data_processors import extract_doctor_data
from scraper import DoctolibScraper

import sys
print("Script starting...")
print(f"Python path: {sys.executable}")

logger = logging.getLogger(__name__)

# =============================================================================
# DEBUG PRINT - This runs when file is imported/executed
# =============================================================================
print("🚀 selenium_scraper.py is loading...")

class SeleniumDoctolibScraper:
    def __init__(self, headless: bool = True):
        """
        Initialize selenium WebDriver
        Args:
            headless: Run browser in background (True) or visible (False)
        """
        self.headless = headless
        self.driver = None
        self.setup_driver()
        self.legacy_scraper = DoctolibScraper() # Reuse existing scraper

    def setup_driver(self):
        """Setup Chrome WebDriver with realistic browser settings"""
        chrome_options = Options()

        if self.headless:
            chrome_options.add_argument("--headless")  # Run in background

        # Realistic browser settings to avoid detection
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        # Real user agent
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_17) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

        # Window size
        chrome_options.add_argument("--window-size=1920,1080")

        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            # Remove automation flags
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            logger.info("Selenium WebDriver initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize WebDriver: {e}")
            raise



    def test_access(self):  # ← MAKE SURE THIS IS INDENTED LIKE THIS
        """Test if we can access Doctolib"""
        print("🌐 test_access() called")
        try:
            self.driver.get("https://www.doctolib.fr")
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            title = self.driver.title
            print(f"✅ Successfully accessed Doctolib. Title: {title}")
            return True
        except Exception as e:
            print(f"❌ Failed to access Doctolib: {e}")
            return False
        


    def handle_cookie_popup(self):
        """Accept cookies to access the page"""
        try:
            #Wait for cookie popup and click accpet - try severl selectors
            logger.info("Looking for cookie popup...")

            accept_button = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.ID, "didomi-notice-agree-button"))
            )

            accept_button.click()
            logger.info(f"Cookie popup handled - Clicked 'Agree and close'")
            time.sleep(2) # Wait for popup to disappear
            return True
                
        except TimeoutException:
            logger.info(f"No cookie popup found within 5 seconds")
            return False
        except Exception as e:
            logger.error(f"Error handling cookie popup: {e}")
            return False
        

    def enter_specialty(self, specialty: str):
        """Enter specialty in the search query input"""
        try:
            specialty_input = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "input.searchbar-query-input"))
            )
            specialty_input.clear()
            specialty_input.send_keys(specialty)
            logger.info(f"Entered specialty: {specialty}")
            time.sleep(2) # Wait for auto-suggestions to appear

            # CAN SELECT FROM AUTO-SUGGESTIONS HERE IF NEEDED
            return True
        
        except Exception as e:
            logger.error(f"Failed to enter specialty: {e}")
            return False
        


    def enter_location(self, location: str):
        """Enter location and select from auto-suggestions"""
        try:
            location_input = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "input.searchbar-place-input"))
            )

            # Make sure selector is focused on location input
            location_input.click()
            time.sleep(0.5)

            location_input.clear()
            location_input.send_keys(location)
            logger.info(f"Entered location: {location}")
            time.sleep(2) # Wait for auto-suggestions to appear

            suggestions = self.driver.find_elements(By.CSS_SELECTOR, "button.searchbar-result")

            # Filter out specialties
            location_suggestions = []
            for suggestion in suggestions:
                # Check if specialty class is present
                try:
                    specialty_elements = suggestion.find_elements(By.CSS_SELECTOR, ".searchbar-result-speciality")

                    if not specialty_elements:
                        location_suggestions.append(suggestion)
                except:
                    location_suggestions.append(suggestion)


            # Debug: What options are available
            
            logger.info(f"Found{len(suggestions)} location suggestions")
            for i, suggestion in enumerate(suggestions):
                logger.info(f"   Suggestion {i+1}: {suggestion.text}")

            # CAN SELECT FROM AUTO_SUGGESTIONS HERE
            return self.select_location_suggestion(location, location_suggestions)
        
        except Exception as e:
            logger.error(f"Failed to enter location: {e}")
            return False
        


    def select_location_suggestion(self, location: str, location_suggestions):
        """Click the first location suggestion from the dropdown (skip compass button)"""

        try:
            logger.info(f"🔍 Processing {len(location_suggestions)} filtered location suggestions")
            
            if not location_suggestions:
                logger.warning("⚠️ No location suggestions found after filtering")
                return False
            # Get all suggestions
            # suggestions = self.driver.find_elements(By.CSS_SELECTOR, "button.searchbar-result")
            # logger.info(f"Found {len(suggestions)} total suggestions")

            for i, suggestion in enumerate(location_suggestions):
                suggestion_text = suggestion.text
                logger.info(f"   Evaluating location: '{suggestion_text}'")

                # Skip first suggestion - "Around Me"
                if i == 0:
                    logger.info("   Skipping compass/'around me' button")
                    continue

                # Look for location in the suggestion
                if location.lower() in suggestion_text.lower():
                    suggestion.click()
                    logger.info(f"Selected location suggestion at index {i}: {suggestion_text}")

                    time.sleep(1)
                    return True
            
            # If no exact match, click the first non-compass location suggestion
            for suggestion in location_suggestions:
                suggestion_text = suggestion.text.lower()
                if 'autour de moi' not in suggestion_text and 'around me' not in suggestion_text:
                    suggestion.click()
                    logger.info(f"✅ Selected first available location: {suggestion.text}")
                    time.sleep(1)
                    return True
                    
            logger.warning("⚠️ No suitable location suggestions found after filtering")
            return False
                
                # if len(location_suggestions) > 1:
                #     location_suggestions[1].click()
                #     logger.info(f"Selected fallback location: {location_suggestions[1].text}")
                #     time.sleep(1)
                #     return True
                
                # logger.warning("No location suggestions found")
                # return False
            
        except Exception as e:
            logger.error(f"Failed to select location suggestions: {e}")
            return False
        


    def click_search(self):
        """Click the search button"""
        try:
            search_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button.searchbar-submit-button"))
            )
            search_button.click()
            logger.info("Clicked search button")
            time.sleep(3) # Wait for results to load
            return True
        
        except Exception as e:
            logger.error(f"Failed to click search button: {e}")
            return False



    def search_doctors(self, specialty: str, department: Department, max_pages: int = 2) -> List[Dict]:
        """
        Search for doctors using Slenium to mimic real user behavior
        
        Returns:
            List of doctor data dictionaries
        """
        doctors_data = []

        try:
            # Navigate to Doctolib search page
            logger.info(f"Navigating to Doctolib search for {specialty} in {department.name}")

            self.driver.get("https://www.doctolib.fr/search")

            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

            # TODO: Figure out the exact search form interactions
            # This is a placeholder - will inspect page structure

            # Attempt to intercept API calls
            doctors_data = self.intercept_api_calls(specialty, department, max_pages)

        except Exception as e:
            logger.error(f"Selenium search failed: {e}")

        return doctors_data
    


    def intercept_api_calls(self, specialty: str, department: Department, max_pages: int) -> List[Dict]:
        """
        Intercept network calls to get the raw API data
        May be easier than parsing HTML
        """
        doctors_data = []

        try:
            # Anable network monitoring
            self.driver.execute_script("""
                window.interceptedData = [];
                const originalFetch = window.fetch;
                window.fetch = function(...args) {
                    return originalFetch.apply(this, args).then(response => {
                        if (args[0].includes('/phs_proxy/raw')) {
                            response.clone().json().then(data => {
                                window.interceptedData.push(data);
                            });
                        }
                        return response;
                    });
                };
            """)

            # Now trigger the search - will need to figure out the exact UI interactions
            # This is tricky, required manual testing

            # Wait for data to be intercepted
            time.sleep(5)

            # Get intercepted data
            intercepted_data = self.driver.execture_script("return window.interceptedData;")
            logger.info(f"Intercepted {len(intercepted_data)} API calls")

            # Process the data
            for data in intercepted_data:
                if 'healthcareProviders' in data:
                    doctors_data.extend(data['healthcareProviders'])

        except Exception as e:
            logger.error(f"API interception failed: {e}")

        return doctors_data
            


    def save_doctor_to_db(self, doctor_dict: Dict, db: Session):
        return self.legacy_scraper.save_doctor_to_db(doctor_dict, db)
    


    def close(self):  # ← INDENTED INSIDE CLASS
        """Clean up the WebDriver"""
        print("🧹 close() called")
        if self.driver:
            self.driver.quit()
            print("✅ WebDriver closed")
    

# =============================================================================
# TEST FUNCTION - OUTSIDE THE CLASS
# =============================================================================
def test_selenium_setup():
    """Test the complete Selenium setup - STANDALONE FUNCTION"""
    print("Testing Selenium setup...")
    scraper = None

    try:
        scraper = SeleniumDoctolibScraper(headless=False)

        print("WebDriver initialized successfully!")
        print("Navigating to Doctolib...")

        # Simple test: Go to page, check title
        scraper.driver.get("https://www.doctolib.fr")

        # Wait for page to load
        WebDriverWait(scraper.driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        # Handle cookie popup
        scraper.handle_cookie_popup()

        print(f"Page title: {scraper.driver.title}")
        print("Selenium setup is working!")

        # Keep browser open for 10 seconds to check popup
        print("Browser will close in 10 seconds...")
        time.sleep(10)

        return True
    
    except Exception as e:
        print(f"Selenium test failed: {e}")
        return False
    
    finally:
        # Always close driver
        if scraper and scraper.driver:
            scraper.driver.quit()
            print("WebDriver closed")


def test_search_functionality():
    """Test that we can perform a basic search"""
    print("🧪 Testing search functionality...")
    scraper = None
    
    try:
        scraper = SeleniumDoctolibScraper(headless=False)
        
        # Navigate and handle cookies
        scraper.driver.get("https://www.doctolib.fr/search")
        WebDriverWait(scraper.driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        scraper.handle_cookie_popup()
        
        # Perform a simple search
        print("🔍 Testing search for 'médecin généraliste' in 'Bordeaux'...")
        scraper.enter_specialty("médecin généraliste")
        scraper.enter_location("Bordeaux")
        scraper.click_search()
        
        # # Wait for any results to load
        # WebDriverWait(scraper.driver, 10).until(
        #     EC.presence_of_element_located((By.CSS_SELECTOR, ".dl-search-results, [data-testid], .search-results, .results"))
        # )
        # SIMPLIFIED: Just wait for URL to change and check we're on results page
        WebDriverWait(scraper.driver, 10).until(
            lambda driver: "speciality=medecin-generaliste" in driver.current_url
        )
        
        print("✅ Search completed successfully!")
        print("📄 Current URL:", scraper.driver.current_url)
        print("📄 Page title:", scraper.driver.title)

        # scraper.driver.save_screenshot("search_results.png")
        # print("📸 Screenshot saved as 'search_results.png'")

        # doctor_cards = scraper.driver.find_elements(By.CSS_SELECTOR, "[data-testid*='search'], .search-result, .doctor-card")
        # print(f"Found approximately {len(doctor_cards)} result elements")

        print("⏳ Browser will close in 15 seconds...")
        time.sleep(15)
        return True
        
    except Exception as e:
        print(f"❌ Search test failed: {e}")
        if scraper and scraper.driver:
            print("📄 Current URL on error:", scraper.driver.current_url)
            print("📄 Page title on error:", scraper.driver.title)
        return False
        
    finally:
        if scraper and scraper.driver:
            scraper.driver.quit()
            print("✅ WebDriver closed")

# Update the main block to test search instead of just setup:
if __name__ == "__main__":
    print("🚀 Testing search functionality...")
    success = test_search_functionality()
    print(f"🎉 Test completed: {'SUCCESS' if success else 'FAILED'}")