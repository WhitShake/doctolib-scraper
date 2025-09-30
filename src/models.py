# src/models.py
from sqlalchemy import Column, Integer, String, Boolean, Float, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from database import Base


# Future Me:
"""If you're using SQLite for development (which is common), note that SQLite doesn't have 
built-in timezone support, but SQLAlchemy handles the conversion transparently. 
When you move to PostgreSQL or MySQL in production, the timezone awareness will work perfectly."""

class Doctor(Base):
    __tablename__ = "doctors"
    
    # Primary key and identifiers
    id = Column(Integer, primary_key=True, index=True)
    doctolib_id = Column(String, unique=True, index=True)  # "profile-200603;practice-1688;medecin-generaliste"
    profile_url = Column(String)  # "/medecin-generaliste/paris/audrey-biscay"
    
    # Basic information
    first_name = Column(String, nullable=True)  # Null for clinics
    last_name = Column(String, nullable=True)   # Null for clinics
    organization_name = Column(String, nullable=True)  # "Centre de Sante Benoit Frachon"
    title = Column(String, nullable=True)  # "Dr", null for clinics
    gender = Column(String, nullable=True)  # "female", "male", null
    
    # Professional details
    specialty = Column(String)  # "Médecin généraliste"
    specialty_slug = Column(String)  # "medecin-generaliste"
    regulation_sector = Column(String)  # "contracted_1"
    practitioner_type = Column(String)  # "INDIVIDUAL_PRACTITIONER", "ORGANIZATION"
    
    # Location information
    address = Column(String)
    city = Column(String)
    postal_code = Column(String)
    country = Column(String, default="fr")
    latitude = Column(Float(10, 7))
    longitude = Column(Float(10, 7))
    
    # Contact and identifiers
    phone_number = Column(String, nullable=True)
    reference_id = Column(Integer)  # 200603 (from references.id)
    practice_id = Column(Integer)  # 1688 (from references.practiceId)
    legacy_id = Column(String)  # "profile-200603;practice-1688;medecin-generaliste"
    
    # Online services
    offers_online_booking = Column(Boolean, default=False)
    offers_telehealth = Column(Boolean, default=False)
    accepts_new_patients = Column(Boolean, default=True)
    
    # Detailed service information (store as JSON for flexibility)
    online_booking_details = Column(JSON)  # agendaIds, topSpecialities, etc.
    payment_methods = Column(JSON)  # ["cash", "check", "credit_card"]
    languages = Column(JSON)  # ["fr", "en", "es"]
    services = Column(JSON)  # ["profile", "onlineBooking"]
    administrative_areas = Column(JSON)  # [] (usually empty)
    
    # Visit motive information
    visit_motive_id = Column(Integer, nullable=True)
    visit_motive_name = Column(String, nullable=True)
    visit_motive_agenda_ids = Column(JSON, nullable=True)
    visit_motive_insurance_sector = Column(JSON, nullable=True)
    
    # Clinic/organization specific
    is_organization = Column(Boolean, default=False)
    organization_status = Column(String, nullable=True)
    cloudinary_public_id = Column(String, nullable=True)  # Image reference
    exact_match = Column(Boolean, default=False)
    
    # Minimum fee (rarely used, but available)
    minimum_fee = Column(Float, nullable=True)
    
    # Foreign keys
    # city_id = Column(Integer, ForeignKey('cities.id'), nullable=True)
    department_id = Column(Integer, ForeignKey('departments.id'))

    # Timestamps - use timezone-aware datetimes
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), 
                        onupdate=lambda: datetime.now(timezone.utc))
    last_seen = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    # city = relationship("City", back_populates="doctors")
    department = relationship("Department", back_populates="doctors")



class Department(Base):
    __tablename__ = "departments"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Basic department info
    name = Column(String, index=True)
    doctolib_id = Column(Integer, unique=True, index=True) # Doctolib's internal ID
    place_id = Column(String) # Google Places ID
    type = Column(String)

    # Geographic coordinates
    latitude = Column(Float(10, 7)) # Center point lat
    longitude = Column(Float(10, 7)) # Center point lng

    # Bounding box (viewport) - stored as separate columns
    viewport_ne_lat = Column(Float(10, 7))
    viewport_ne_lng = Column(Float(10, 7))
    viewport_sw_lat = Column(Float(10, 7))
    viewport_sw_lng = Column(Float(10, 7))

    # Zipcodes (store as JSON array)
    zipcodes = Column(JSON)

    # Timestamps - use timezone-aware datetimes
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_scraped = Column(DateTime, nullable=True)
    last_updated = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    # cities = relationship("City", back_populates="department")
    doctors = relationship("Doctor", back_populates="department")



# class City(Base):
#     __tablename__ = "cities"

#     id = Column(Integer, primary_key=True, index=True)
#     name = Column(String, index=True)
#     postal_code = Column(String, index=True)
#     latitude = Column(Float(10, 7))
#     longitude = Column(Float(10, 7))
    
#     # Foreign key
#     department_id = Column(Integer, ForeignKey('departments.id'))
    
#     # Timestamps
#     created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
#     # Relationships
#     department = relationship("Department", back_populates="cities")
#     doctors = relationship("Doctor", back_populates="city")