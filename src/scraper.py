# src/scraper.py
import requests
import logging
import time
import random
from typing import Dict, Optional, List
from .auth import DoctoLibSession

logger = logging.getLogger(__name__)

class DoctolibScraper:
    def __init__(self):
        self.auth_manager = DoctoLibSession()
        self.session = None

    def initialize(self):
        """Initialize the scraper with an authenticated session"""
        logger.info("Initializing Doctolib scraper...")
        self.session = self.auth_manager.get_authenticated_session()

    def search_doctors(self, specialty: str, location: str, page: int = 0):
        """Search for doctors with the given parameters"""

        payload = {
            "keyword": "medecin-generaliste",
            "location": {
                "place": {
                    "id": 6902,
                    "placeId": "ChIJM1PaREO_yRIRIAKX_aUZCAQ",
                    "name": "Marseille",
                    "nameWithPronoun": "à Marseille",
                    "locality": "Marseille",
                    "country": "fr",
                    "type": "locality",
                    "gpsPoint": {
                        "lat": 43.296482,
                        "lng": 5.36978
                    },
                    "viewport": {
                        "northeast": {
                            "lat": 43.39116,
                            "lng": 5.5323519
                        },
                        "southwest": {
                            "lat": 43.169621,
                            "lng": 5.277926
                        }
                    },
                    "streetName": None,
                    "streetNumber": None,
                    "slug": "marseille",
                    "zipcodes": [
                        "13000", "13001", "13002", "13003", "13004", "13005", "13006", 
                        "13007", "13008", "13009", "13010", "13011", "13012", "13013", 
                        "13014", "13015", "13016", "13273", "13332", "13915", "13276", 
                        "13304", "13285", "13331", "13326", "13282", "13387", "13471", 
                        "13425", "13385", "13281", "13362", "13201", "13233", "13354", 
                        "13572", "13274", "13275", "13235", "13384", "13313", "13381", 
                        "13297", "13254", "13395", "13213", "13284"
                    ]
                }
            },
            "filters": {}
        }

        url = f"http://www.doctolib.fr/phs_proxy/raw?page={page}"

        try: 
            delay = random.uniform(2, 5)
            logger.info(f"Waiting {delay:.2f} seconds before request...")
            time.sleep(delay)

            logger.info(f"Searching for {specialty} in {location} (page {page})")
            response = self.session.post(url, json=payload, timeout=30)

            #Debug Info
            logger.info(f"Status Code: {response.status_code}")
            logger.info(f"Response Length: {len(response.text)}")

            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"API returned status {response.status_code}: {response.text[:500]}")
                return None
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            return None
    

    def scrape_specialty(self, specialty: str, location: str, max_pages: int = 10) -> List[Dict]:

        """Scrape multiple pages for a specialty"""

        if not self.session:
            self.initialize()

        all_doctors = []

        for page in range(max_pages):
            logger.info(f"Scraping page {page} for {specialty} in {location}")

            data = self.search_doctors(specialty, location, page)

            if not data:
                logger.warning(f"Failed to get data for page {page}")
                break

            # Exctract doctors from reponse
            doctors = data.get('healthcareProviders', [])
            if not doctors:
                logger.info("No more doctors found, stopping pagination")
                break

            all_doctors.extend(doctors)
            logger.info(f"Found {len(doctors)} doctors on oage {page}")

            # Delay between pages
            time.sleep(random.uniform(3, 7))
            
        return all_doctors