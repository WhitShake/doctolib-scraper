# src/main.py
import logging
from sqlalchemy.orm import Session
from .database import SessionLocal
from .scraper import DoctolibScraper
from .models import Base, Doctor, Practice
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    #Initialize database
    from .database import engine
    Base.metadata.create_all(bind=engine)

    #Initialize scraper
    scraper = DoctolibScraper()

    # Define search params
    specialties = ["medecin-generaliste"]
    locations = ["Paris", "Marseille", "Lyon"]

    db = SessionLocal()
    try:
        for specialty in specialties:
            for location in locations:
                logger.info(f"Scraping {specialty} in {location}")

                doctors_data = scraper.scrape_specialty(specialty, location, max_pages=3)

                for doctor_data in doctors_data:
                    new_doctor = Doctor(
                        id=doctor_data.get("id"),
                        last_name=doctor_data.get("nom"),
                        first_name=doctor_data.get("prenom"),
                        specialty=doctor_data["profession"]["specialite"]["libelle"],
                        # if doctor_data.get("profession")
                        # else None,
                        city_id=db_city.city_id,
                        address=doctor_data.get("voie"),
                        office_name=doctor_data.get("complement"),
                        city=doctor_data.get("ville"),
                        postal_code=doctor_data.get("codePostal"),
                        latitude=doctor_data.get("geocode", {}).get("latitude"),
                        longitude=doctor_data.get("geocode", {}).get("longitude"),
                        phone_number=doctor_data.get("coordonnees", {}).get("numTel"),
                        sector_1_agmt = doctor_data[''],
                    )
                    db.add(new_doctor)
                db.commit()
                logger.info(f"Saved {len(doctors_data)} doctors for {specialty} in {location}")

    except Exception as e:
        logger.error(f"Scraping failed: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()