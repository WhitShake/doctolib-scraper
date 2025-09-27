# src/department_loader.py

import json
import os
from typing import Dict, List
from sqlalchemy.orm import Session
from models import Department
from database import SessionLocal
from datetime import datetime, timezone
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DepartmentLoader:
    def __init__(self, db: Session): # Where the db gets stored
        self.db = db # Stores the session as an instance variable

    def load_department_from_json(self, file_path: str) -> Department:
        """Load a single department from JSON file"""
        try:
            # with open() - opens the file safely and auto-closes
            # file_path = department_loader/paris.json, 'r' = opens in read only
            with open(file_path ,'r', encoding='utf-8') as f:
                # Reads entire JSON file and converts to Python dict
                payload = json.load(f)

            place_data = payload['location']['place']

            #Create department object
            department = Department(
                name=place_data['name'],
                doctolib_id=place_data['id'],
                place_id=place_data.get('placeId'),
                type=place_data['type'],

                # Geographic coordinates (center point)
                latitude=place_data['gpsPoint']['lat'],
                longitude=place_data['gpsPoint']['lng'],

                # Bounding box
                viewport_ne_lat=place_data['viewport']['northeast']['lat'],
                viewport_ne_lng=place_data['viewport']['northeast']['lng'],
                viewport_sw_lat=place_data['viewport']['southwest']['lat'],
                viewport_sw_lng=place_data['viewport']['southwest']['lng'],

                # Zipcodes
                zipcodes=place_data.get('zipcodes', [])
            )

            # Returns the payload as a Python dict
            return department
    
        except Exception as e:
            logger.error(f"Error loading department from {file_path}: {e}")
            return None
        

    def load_all_departments(self, directory_path: str = "department_payloads"):
        """Load all departments from JSON files in a directory"""
        # Check if directory exists
        if not os.path.exists(directory_path):
            logger.error(f"Directory {directory_path} does not exist")
            return
        
        # Find all JSON files in the directory
        json_files = [f for f in os.listdir(directory_path) if f.endswith('.json')]
        logger.info(f"Found {len(json_files)} department files")

        loaded_count = 0
        updated_count = 0

        # Process each file
        for json_file in json_files:
            # Build full path: "department_payloads/paris.json"
            file_path = os.path.join(directory_path, json_file)
            # Load and parse the JSON into a department object
            department = self.load_department_from_json(file_path)

            # Check if department already exists in db
            # If load_department_from_json() returns a dict
            if department:
                # Returns the first matching doctolib ID from the db or None
                # query(Department) - starts a query for Department objects
                existing = self.db.query(Department).filter(
                    Department.doctolib_id == department.doctolib_id
                ).first()

                # If there was a match
                if existing:
                    # Update fields we want to keep current
                    existing.name = department.name
                    existing.place_id = department.place_id
                    existing.type = department.type
                    
                    # Geographic data (might get more accurate over time)
                    existing.latitude = department.latitude
                    existing.longitude = department.longitude
                    
                    # Bounding box (could change with map updates)
                    existing.viewport_ne_lat = department.viewport_ne_lat
                    existing.viewport_ne_lng = department.viewport_ne_lng
                    existing.viewport_sw_lat = department.viewport_sw_lat
                    existing.viewport_sw_lng = department.viewport_sw_lng
                    
                    # Zipcodes (rarely change, but possible)
                    existing.zipcodes = department.zipcodes
                    
                    # Update timestamp to show when we last refreshed this department
                    existing.last_scraped = datetime.now(timezone.utc)
                    updated_count += 1
                    logger.info(f"Updated department: {department.name}")

                else:
                    # Add new record
                    logger.info(f"Adding department: {department.name}")
                    self.db.add(department)
                    loaded_count += 1

        self.db.commit()
        logger.info(f"Successfully loaded {loaded_count} new departments and updated {updated_count} existing ones")

    
    def get_department_by_name(self, name: str) -> Department:
        """Get department by name"""
        return self.db.query(Department).filter(Department.name == name).first()
    

    def list_all_departments(self) -> List[Department]:
        """List all departments in database"""
        return self.db.query(Department).all()
    

def main():
    """Main finction to load departments"""
    db = SessionLocal()
    # DepartmentLoader is the class, passes the db to its constructor
    # Gives db the access to this session
    loader = DepartmentLoader(db)

    try:
        # Load departments from JSON files
        loader.load_all_departments()

        # List what we have
        departments = loader.list_all_departments()
        print("\n=== LOADED DEPARTMENTS ===")
        for dept in departments:
            print(f"✅ {dept.name} (ID: {dept.doctolib_id}) - {len(dept.zipcodes or [])} zipcodes")

        print(f"\nTotal: {len(departments)} departments ready for scraping")

    except Exception as e:
        logger.error(f"Error in main: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    main()