# src/base_scraper.py
from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import logging
from models import Doctor

logger = logging.getLogger(__name__)

class BaseDoctolibScraper(ABC):
    """Base class with common functionality for all scrapers"""

    def save_doctor_to_db(self, doctor_dict: Dict, db: Session) -> bool:
        """Common database saving logic used by all scrapers"""
        try:
            # Remove any 'id' field that might conflict with primary key
            if 'id' in doctor_dict:
                del doctor_dict['id']

            doctolib_id = doctor_dict.get('doctolib_id')
            if not doctolib_id:
                logger.error(f"No doctolib_id found in doctor_dict")
                return False
            
            existing_doctor = db.query(Doctor).filter(
                Doctor.doctolib_id == doctolib_id
            ).first()

            if existing_doctor:
                # Update existing record
                for key, value in doctor_dict.items():
                    if hasattr(existing_doctor, key) and not key.startswith('_'):
                        setattr(existing_doctor, key, value)
                    existing_doctor.updated_at = datetime.now(timezone.utc)
                    existing_doctor.last_name = datetime.now(timezone.utc)
                    logger.info(f"Updated doctor: {doctor_dict.get('last_name', doctor_dict.get('organization_name', 'Unknown'))}")

            else:
                # Create new record
                doctor = Doctor(**doctor_dict)
                db.add(doctor)
                logger.info(f"Added new doctor: {doctor_dict.get('last_name', doctor_dict.get('organization_name', 'Unknown'))}")

            db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error saving doctor to database: {e}")
            db.rollback()
            return False
        
    @abstractmethod
    def search_doctors(self, specialty: str, department, max_pages: int = 2) -> List[Dict]:
        """Abstract method - each scraper implements its own search logic"""
        pass