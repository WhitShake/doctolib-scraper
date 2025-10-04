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
import sys

from models import Doctor, Department
from data_processors import extract_doctor_data
# from scraper import DoctolibScraper

try:
    from base_scraper import BaseDoctolibScraper
except ImportError:
    # Fallback for direct execution
    from src.base_scraper import BaseDoctolibScraper

print("Script starting...")
print(f"Python path: {sys.executable}")

logger = logging.getLogger(__name__)

# =============================================================================
# DEBUG PRINT - This runs when file is imported/executed
# =============================================================================
print("🚀 selenium_scraper.py is loading...")

class SeleniumDoctolibScraper(BaseDoctolibScraper):
    def __init__(self, headless: bool = True):
        """
        Initialize selenium WebDriver
        Args:
            headless: Run browser in background (True) or visible (False)
        """
        super().__init__() # Call parent constructor if needed - Why would I need that?
        self.headless = headless
        self.driver = None
        self.setup_driver()
        # self.legacy_scraper = DoctolibScraper() # Reuse existing scraper

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



    def search_doctors(self, specialty: str, department, max_pages: int = 2) -> List[Dict]:
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

            # Handle cookie popup
            self.handle_cookie_popup()

            # Enter search terms and implement search
            self.enter_specialty(specialty)
            self.enter_location(department.name) # Department name as location
            self.click_search()

            # Wait for search to complete
            WebDriverWait(self.driver, 10).until(
                lambda driver: "specialty" in driver.current_url
            )

            # TODO: Extract doctor data from the results page
            # Currently intercepting API calls instead
            doctors_data = self.intercept_api_calls(specialty, department, max_pages)

        except Exception as e:
            logger.error(f"Selenium search failed: {e}")

        return doctors_data
    


    def intercept_api_calls(self, specialty: str, department: Department, max_pages: int) -> List[Dict]:
        """
        Intercept network calls to get the raw API data
        """
        doctors_data = []

        try:
            # Enable network monitoring before triggering search
            logger.info("Setting up network interception...")

            # Clear any previous intercepted data
            self.driver.execture_script("window.interceptData = [];")

            # Monitor fetch requests
            self.driver.execute_script("""
                const originalFetch = window.fetch;
                window.fetch = function(...args) {
                    return originalFetch.apply(this, args).then(response => {
                        // Clone the response to read it without consuming
                        const clonedResponse = response.clone();

                        // Check if this is a doctor search API call
                        if (args[0] && args[0].includes('/search_results') ||
                                        args[0].includes('/search/') ||
                                        args[0].includes('/api/'))) {
                            clonedResponse.json().then(data => {
                                console.log('Intercepted API call:', args[0], data);
                                if(!window.interceptedData) window.interceptedData = [];
                                window.interceptedData.push({
                                    url: args[0],
                                    data: data,
                                    timestamp: new Date().toISOString()
                                });
                            }).catch(e => {/* Not JSON */});
                        }
                        return response;
                    });
                };
            """)

            # Also monitor XMLHttpRequest
            self.driver.execture_script("""
                const originalXHR = window.XMLHttpRequest;
                window.XMLHttpRequest = function() {
                    const xhr = new originalXHR();
                    const originalOpen = xhr.open;
                    const originalSend = xhr.send;
                    
                    xhr.open = function(method, url) {
                        this._url = url;
                        return originalOpen.apply(this, arguments);
                    };
                    
                    xhr.send = function(data) {
                        this.addEventListener('load', function() {
                            if (this._url && (this._url.includes('/search_results') ||
                                            this._url.includes('/search/') ||
                                            this._url.includes('/api/'))) {
                                try {
                                    const responseData = JSON.parse(this.responseText);
                                    console.log('Intercepted XHR call:', this._url, responseData);
                    
                                    if (!window.interceptedData) window.interceptedData = [];
                                    window.interceptedData.push({
                                        url: this._url,
                                        data: responseData,
                                        timestamp: new Date().toISOString()
                                    });
                                } catch(e) {/* Not JSON */}
                            }
                        });
                        return originalSend.apply(this, arguments);
                    };
                    
                    return xhr;
                };
            """)
            
            logger.info("Network interception setup complete")

            # The search should already be triggered by search_doctors method
            # Wait for results to load and API calls to be made
            logger.info("Waiting for API calls to be intercepted...")
            time.sleep(5)

            # Try to scroll to trigger pagination/loading more results
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)

            # Get intercepted data
            intercepted_data = self.driver.execute_script("return window.interceptedData || [];")

            logger.info(f"Intercepted {len(intercepted_data)} API calls")

            # Process intercepted data
            for i, call in enumerate(intercepted_data):
                logger.info(f"   Call {i+1}: {call.get('url', 'Unknown URL')}")
                data = call.get('data', {})

                # Look for dactor data in various possible structures
                if 'data' in data and 'doctors' in data['data']:
                    doctors_data.extend(data['data']['doctors'])
                    logger.info(f"   Found {len(data['data']['doctors'])} doctors")
                elif 'doctors' in data:
                    doctors_data.extend(data['doctors'])
                    logger.info(f"   Found {len(data['professionals'])} professionals")
                elif 'items' in data:
                    doctors_data.extend(data['items'])
                    logger.info(f"   Found {len(data['items'])} items")

            logger.info(f"Total doctors extracted: {len(doctors_data)}")
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
    """Legacy test - keeping for reference. Replaced by test_integration()"""
    print("This is a legacy test. Use test_integration() instead.")
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



def test_integration():
    """Test Selenium scraper with actual database integration"""
    from database import SessionLocal
    from models import Department
    from data_processors import extract_doctor_data

    print("Testing Selenium + Database integration...")
    scraper = None
    db = SessionLocal()

    try:
        # Create instance of S. scraper, browser will not run in background
        scraper = SeleniumDoctolibScraper(headless=False)

        # Get a test department
        test_department = db.query(Department).filter(Department.name.ilike("%Ain%")).first()

        if not test_department:
            print("No Ain department found in database")
            return False
        
        print(f"Testing search in: {test_department.name}")

        # Use the search_doctors method (inherited interface)
        doctors_data = scraper.search_doctors(
            specialty="médecin généraliste",
            department=test_department,
            max_pages=1
        )

        print(f"Found {len(doctors_data)} raw doctor records via Selenium")

        # TODO: Process and save docs to db via data_processors.extract_doctor_data
        saved_count = 0
        for doctor_data in doctors_data:
            try:
                # Extract structured data using existing processor
                processed_doctor = extract_doctor_data(doctor_data)

                if processed_doctor:
                    # Save to db using inherited method
                    success = scraper.save_doctor_to_db(processed_doctor, db)
                    if success:
                        saved_count += 1
                    else:
                        print(f"Failed to save doctor: {processed_doctor.get('last_name', 'Unknown')}")

                else:
                    print("failed to process doctor data")

            except Exception as e:
                print(f"Error processing doctor: {e}")
                continue
        
        print(f"Successfully saved {saved_count}/{len(doctors_data)} doctors to database")

        return saved_count > 0
    
    except Exception as e:
        print(f"Integrations test failed: {e}")
        return False
    
    finally:
        if scraper and scraper.driver:
            scraper.driver.quit()
        db.close()


# if __name__ == "__main__":
#     print("🚀 Testing Selenium + Database integration...")
#     success = test_integration()
#     print(f"🎉 Test completed: {'SUCCESS' if success else 'FAILED'}")

def test_inheritance():
    """Quick test to verify inheritance is working"""
    try:
        scraper = SeleniumDoctolibScraper(headless=False)
        print("✅ Selenium scraper created successfully")
        print(f"✅ Has save_doctor_to_db method: {hasattr(scraper, 'save_doctor_to_db')}")
        print(f"✅ Has search_doctors method: {hasattr(scraper, 'search_doctors')}")
        scraper.driver.quit()
        return True
    except Exception as e:
        print(f"❌ Inheritance test failed: {e}")
        return False
    
# Update main temporarily to test inheritance first:
if __name__ == "__main__":
    print("🚀 Testing inheritance structure...")
    if test_inheritance():
        print("🎉 Inheritance working! Now testing integration...")
        success = test_integration()
        print(f"🎉 Integration test: {'SUCCESS' if success else 'FAILED'}")
    else:
        print("❌ Inheritance test failed - fix base class first")