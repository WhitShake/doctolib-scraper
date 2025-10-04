# src/scraper.py
import json
import os
import requests
import logging
import time
from typing import Dict, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from models import Doctor, Department
from data_processors import extract_doctor_data, validate_doctor_data

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DoctolibScraper:
    def __init__(self):
        self.session = requests.Session()
        self.base_url = "https://www.doctolib.fr"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': 'https://www.doctolib.fr/search',
            'Content-Type': 'application/json',
            'Origin': 'https://www.doctolib.fr',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
        }
        self.session.headers.update(self.headers)
        self.request_delay = 3 # 3 seconds btw requests to not overwhelm API


    
    def setup_session(self, max_retries=3):
        """Visit the main page first with retries and rate limiting"""

        for attempt in range(max_retries):
            try:
                logger.info(f"Setting up session with Doctolib (attempt {attempt + 1}/{max_retries}...)")

                # Add random delay between retries
                if attempt > 0:
                    delay = 5 * attempt # 5, 10, 15 seconds
                    logger.info(f"Waiting {delay} seconds before retry...")
                    time.sleep(delay)

                response = self.session.get(
                    'https://www.doctolib.fr',
                    timeout=10
                )

                if response.status_code == 200:
                    logger.info("Session setup successful")
                    return True
                elif response.status_code == 429:
                    logger.warning(f"Rate limited on attempt {attempt + 1}")
                    continue
                else:
                    logger.warning(f"Session setup returned status {response.status_code}")

            except Exception as e:
                logger.error(f"Session setup failed: {e}")

        logger.error("All session setup attempts failed.")
        return False


    # def setup_session(self):
    #     """Visit the main page first to get proper cookies and session"""
    #     try:
    #         logger.info("Setting up session with Doctolib...")
    #         response = self.session.get(
    #             'https://www.doctolib.fr',
    #             timeout=10
    #         )
    #         if response.status_code == 200:
    #             logger.info("Session setup successful")
    #             return True
    #         else:
    #             logger.warning(f"Session setup returned status {response.status_code}")
    #             return False
    #     except Exception as e:
    #         logger.error(f"Session setup failed: {e}")
    #         return False

    # Creates the stored payload files for each department
    # Params: specialty=str "medecine generaliste", department=Department object - What is Dict doing here?
    def create_search_payload(self, specialty: str, department: Department) -> Dict:
        """Create search payload for a specific department"""
        payload = {
            "keyword": specialty,
            "location": {
                "place": {
                    "id": department.doctolib_id,
                    "name": department.name,
                    "country": "fr",
                    "type": department.type,
                    "viewport": {
                        "northeast": {
                            "lat": float(department.viewport_ne_lat),
                            "lng": float(department.viewport_ne_lng),
                        },
                        "southwest": {
                            "lat": float(department.viewport_sw_lat),
                            "lng": float(department.viewport_sw_lng),
                        }
                    },
                    "gpsPoint": {
                        "lat": float(department.latitude),
                        "lng": float(department.longitude)
                    },
                    "zipcodes": department.zipcodes
                }
            },
            "filters": {}
        }
        print("DEBUG - Payload types:")
        # Work through this
        for key, value in payload['location']['place'].items():
            if hasattr(value, '__class__'):
                print(f"  {key}: {type(value)}")
        
        return payload
    

    def search_doctors_in_department(self, specialty: str, department: Department, page: int = 0) -> Optional[Dict]:
        """Search for doctors in a specific department"""

        # Creates payload for the specified department
        payload = self.create_search_payload(specialty, department)

        try:
            logger.debug(f"Sending request to Doctolib API for {department.name}, page {page}")

            # POST request to search endpoint
            response = self.session.post(
                f'{self.base_url}/phs_proxy/raw?page={page}',
                # What is this doing? Is it empty or is this the full response visible in Network tab?
                json=payload,
                timeout=30
            )

            logger.debug(f"Response status: {response.status_code}")
            logger.debug(f"Response headers: {dict(response.headers)}")

            if response.status_code == 200:
                data = response.json()
                logger.info(f"Successfully received data for {department.name} - {len(data.get('healthcareProviders', []))} doctors")
                return data
            elif response.status_code == 403:
                logger.error(f"Access forbidden for {department.name}. Possible blocking.")
                if response.text:
                    logger.debug(f"Response text: {response.text[:500]}")
            elif response.status_code == 429:
                logger.error(f"Rate limited for {department.name}. Need to slow down.")
            else:
                logger.error(f"Unexpected status {response.status_code} for {department.name}")
                return None
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Search request failed for {department.name} as {e}")
            return None




    # def save_doctor_to_db(self, doctor_dict: Dict, db: Session):
    #     """Save parsed doctor data to database using data structure"""

    #     try:
    #         #Remove any 'id' fields that might conflict with primary key
    #         # Dig more into this
    #         if 'id' in doctor_dict:
    #             logger.warning(f"Removing 'id' field to avoid primary key conflict: {doctor_dict['id']}")
    #             del doctor_dict['id']
            
    #         # Ensure required fields have values - Review this
    #         required_fields = ['doctolib_id', 'specialty', 'address', 'city']
    #         for field in required_fields:
    #             if not doctor_dict.get(field):
    #                 logger.warning(f"Missing required field {field} for doctor {doctor_dict.get('doctolib_id', 'unknown')}")
    #                 # Set default values for critical fields
    #                 if field == 'doctolib_id':
    #                     doctor_dict['doctolib_id'] = f"unknown-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    #                 elif field == 'specialty':
    #                     doctor_dict['specialty'] = 'Médecin généraliste'
    #                 elif field in ['address', 'city']:
    #                     doctor_dict[field] = 'Non spécifié'

    #         # Check if doctor already exists
    #         # Why are we exiting if the doc doesn't exist? Does this exit the conditional or the function?
    #         doctolib_id = doctor_dict.get('doctolib_id')
    #         if not doctolib_id:
    #             logger.error("No doctolib_id found in doctor_dict")
    #             return False
            
    #         existing_doctor = db.query(Doctor).filter(
    #             Doctor.doctolib_id == doctolib_id
    #         ).first()

    #         if existing_doctor:
    #             # Update existing record
    #             for key, value in doctor_dict.items():
    #                 if hasattr(existing_doctor, key) and not key.startswith('_'):
    #                     setattr(existing_doctor, key, value)
    #             existing_doctor.updated_at = datetime.now(timezone.utc)
    #             existing_doctor.last_seen = datetime.now(timezone.utc)
    #             logger.info(f"Updated doctor: {doctor_dict.get('last_name', doctor_dict.get('organization_name', 'Unknown'))}")

    #         else:
    #             # Create new record - use direct Doctor creation
    #             # What does '**' do? 
    #             doctor = Doctor(**doctor_dict)
    #             # Create new record
    #             # doctor = create_doctor_from_json(doctor_dict, doctor_dict['department_id'])
    #             db.add(doctor)
    #             logger.info(f"Added new doctor: {doctor_dict.get('last_name', doctor_dict.get('organization_name', 'Unknown'))}")

    #         db.commit()
    #         return True
        
    #     except Exception as e:
    #         logger.error(f"❌ Error saving doctor to database: {e}")
    #         logger.error(f"Doctor dict keys: {list(doctor_dict.keys()) if doctor_dict else 'None'}")
    #         # logger.error(f"Doctor dict keys: {list(doctor_dict.keys()) if doctor_dict else 'None'}")
    #         import traceback
    #         logger.error(traceback.format_exc())
    #         db.rollback()
    #         return False


    # Should this be above save_doc_to_db?
    def scrape_department(self, specialty: str, department: Department, db: Session, max_pages: int = 5):

        """Scrape all doctors for a specialty in a specific department"""

        logger.info(f"Scraping {specialty} in {department.name} (max {max_pages} pages)")

        # For every page of search results
        for page in range(max_pages):
            logger.info(f"Page {page + 1} for {department.name}...")

            # Creates the payload object of the Department (not doctor)
            data = self.search_doctors_in_department(specialty, department, page)
            if not data:
                logger.warning(f"No data received for page {page}, stopping")
                break

            # Access the list value assigned to key 'healthcareProviders' and save as 'doctors'. 'doctors' is a list of dicts.
            doctors = data.get('healthcareProviders', [])
            if not doctors:
                logger.info("No more doctors found, completed department")
                break

            logger.info(f"Found {len(doctors)} doctors on page {page + 1}")

            # Iterate through the list of doctors
            for doctor_data in doctors:
                # Passes each dict element (single doctor's data) in doctors list to processor
                parsed_data = extract_doctor_data(doctor_data, department.id)
                # Adds processed doctor data to db
                self.save_doctor_to_db(parsed_data, db)

            # Rate limiting for politeness
            time.sleep(self.request_delay)

        logger.info(f"Completed scraping {department.name}")



    # Still needed?
    def search_doctors_alternative(self, specialty: str, department: Department, page: int = 0):
        """Alternative search method using different endpoint"""
        params = {
            'speciality_id': 556,  # Médecin généraliste ID
            'ref_visit_motive_ids[]': [2067, 2068],  # Common visit motives
            'page': page
        }
        
        try:
            response = self.session.get(
                f'{self.base_url}/search_json',
                params=params,
                timeout=30
            )
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            logger.error(f"Alternative search failed: {e}")
        return None


    # Still needed?
    # In src/scraper.py - add this method to the DoctolibScraper class
    def test_with_sample_data(self, db: Session):
        """Test our data processing with sample API response"""
        try:
            # Import here to avoid circular imports
            from data_processors import extract_doctor_data
            
            # Use your existing sample_api_response.json file
            sample_file_path = os.path.join(os.path.dirname(__file__), '..', 'sample_api_response.json')
            
            with open(sample_file_path, 'r', encoding='utf-8') as f:
                sample_data = json.load(f)
            
            doctors = sample_data.get('healthcareProviders', [])
            logger.info(f"Found {len(doctors)} sample doctors to process")
            
            processed_count = 0
            for i, doctor_data in enumerate(doctors):
                try:
                    logger.debug(f"Processing doctor {i+1}: {doctor_data.get('id', 'Unknown ID')}")

                    # Use department_id=1 for testing (assuming you have at least one department)
                    parsed_data = extract_doctor_data(doctor_data, department_id=1)
                    if not validate_doctor_data(parsed_data):
                        logger.error(f"Skipping invalid doctor data: {doctor_data.get('id', 'unknown')}")
                        continue

                    logger.debug(f"Extracted data keys: {list(parsed_data.keys())}")

                    if self.save_doctor_to_db(parsed_data, db):
                        processed_count += 1

                except Exception as e:
                    logger.error(f"Error processing sample doctor {i+1}: {e}")
                    logger.error(f"Doctor data: {doctor_data}")
                    import traceback
                    logger.error(traceback.format_exc())
                    continue
            
            logger.info(f"✅ Test completed! Successfully processed {processed_count}/{len(doctors)} sample doctors")
            return processed_count > 0
            
        except FileNotFoundError:
            logger.error("❌ sample_api_response.json file not found")
            return False
        except Exception as e:
            logger.error(f"❌ Test failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False


    # Still needed?
    # Add this temporary test method
    def test_data_extraction_only(self):
        """Test just the data extraction without saving to DB"""
        try:
            from data_processors import extract_doctor_data
            
            sample_file_path = os.path.join(os.path.dirname(__file__), '..', 'sample_api_response.json')
            
            with open(sample_file_path, 'r', encoding='utf-8') as f:
                sample_data = json.load(f)
            
            doctors = sample_data.get('healthcareProviders', [])
            logger.info(f"Testing data extraction on {len(doctors)} doctors")
            
            for i, doctor_data in enumerate(doctors[:2]):  # Just test first 2
                try:
                    parsed_data = extract_doctor_data(doctor_data, department_id=1)
                    logger.info(f"✅ Doctor {i+1} extraction successful")
                    logger.info(f"   Keys: {list(parsed_data.keys())}")
                    logger.info(f"   doctolib_id: {parsed_data.get('doctolib_id')}")
                    logger.info(f"   first_name: {parsed_data.get('first_name')}")
                    logger.info(f"   last_name: {parsed_data.get('last_name')}")
                except Exception as e:
                    logger.error(f"❌ Doctor {i+1} extraction failed: {e}")
                    
            return True
            
        except Exception as e:
            logger.error(f"❌ Extraction test failed: {e}")
            return False