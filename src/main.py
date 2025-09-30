# src/main.py
import logging
import os
import sys
# from sqlalchemy.orm import Session

sys.path.append(os.path.dirname(__file__))
    
from database import SessionLocal, engine, Base
from scraper import DoctolibScraper
from department_loader import DepartmentLoader
from models import Doctor, Department

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():

    """Main function to run the scraper"""
    logger.info("Starting Doctolib scraper...")

    # Create table if they don't exist
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created/verified")
    except Exception as e:
        logger.error(f"Error creating tables: {e}")
        return

    db = SessionLocal()

    try:
        # Load department first
        loader = DepartmentLoader(db)
        department_payloads_path = os.path.join(os.path.dirname(__file__), "..", "department_payloads")
        loader.load_all_departments(department_payloads_path) # Path from project root

        # Initialize scraper
        scraper = DoctolibScraper()

        # Test with sample data first
        logger.info("🧪 Testing with sample data...")
        if scraper.test_with_sample_data(db):
        # if scraper.test_data_extraction_only():
            doctor_count = db.query(Doctor).count()
            logger.info(f"✅ Sample data test successful! Total doctors in database: {doctor_count}")
        else:
            logger.error("❌ Sample data test failed")

        # # Setup session
        # if not scraper.setup_session():
        #     logger.error("Failed to setup session, cannot proceed with scraping")
        #     db.close()
        #     return

        # # Get specific departments to scrape (start small)
        # target_departments = ["Paris", "Rhône"]
        # specialty = "medecin-generaliste"

        # for dept_name in target_departments:
        #     department = loader.get_department_by_name(dept_name)
        #     if department:
        #         logger.info(f"Scraping {specialty} in {department.name}")
        #         # Small test = scrape just 2 pages (40 docs)
        #         scraper.scrape_department(specialty, department, db, max_pages=2)
        #     else:
        #         logger.warning(f"Department {dept_name} not found in database")

        # Print summary
        doctor_count = db.query(Doctor).count()
        logger.info(f"Scraping complete! Total doctors in database: {doctor_count}")

    except Exception as e:
        logger.error(f"Scraping failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        db.rollback()
    finally:
        db.close()
        logger.info("Database connection closed")

if __name__ == "__main__":
    main()