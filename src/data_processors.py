# src/data_processors.py
"""
Utility functions for processing and transforming Doctolib API data
"""
import json
from typing import Dict, Any
from models import Doctor
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def extract_doctor_data(doctor_json, department_id):
    """Extract all available data from Doctolib doctor JSON"""

    def safe_get(data, path, default=None):
        """
        Safely navigate nested dictionaries without throwing KeyError or AttributeError
        
        Args:
            data: The dictionary to search in
            path: Dot-separated path like 'location.address' or 'speciality.name'
            default: Value to return if any part of the path is missing
        
        Examples:
            safe_get(doctor_json, 'location.city') → "Paris" or None
            safe_get(doctor_json, 'nonexistent.field', 'default') → "default"
        """

        keys = path.split('.') # Convert 'location.city' → ['location', 'city']
        current = data

        # Check if current level is a dict AND has the key
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key] # Move one level deeper into nested structure
            else:
                return default # Path broken, return default
        
        return current if current is not None else default
    
    # =========================================================================
    # Data prep to handle null objects/empty fields/orgs instead of individuals
    # =========================================================================

    # Determine if this is an individual or organization by checking if a first name exists
    # Some doctors are clinics (orgs) without first/last names
    is_organization = doctor_json.get('firstName') is None and doctor_json.get('name') is not None

    # Create safe versions of nested objects that might be null
    # Prevents "no attribute" get() errors for NoneType objects
    online_booking = doctor_json.get('onlineBooking') or {}
    matched_visit_motive = doctor_json.get('matchedVisitMotive') or {}
    location = doctor_json.get('location') or {}
    references = doctor_json.get('references') or {}

    # Determine if this is an individual or org.
    is_organization = doctor_json.get('firstName') is None and doctor_json.get('name') is not None
    
    return {
        # Primary identifiers
        'doctolib_id': doctor_json.get('id', 'unknown'),
        'profile_url': doctor_json.get('link', ''),
        
        # Name & personal info
        'first_name': doctor_json.get('firstName'),
        'last_name': doctor_json.get('name') if not is_organization else None,
        'organization_name': doctor_json.get('name') if is_organization else None,
        'is_organization': is_organization,
        'title': doctor_json.get('title'),
        'gender': doctor_json.get('gender'),

        # Professional details - critical with fallbacks
        'specialty': safe_get(doctor_json, 'speciality.name', 'Médecin généraliste'),
        'specialty_slug': safe_get(doctor_json, 'speciality.slug', 'médecin-généraliste'),
        'regulation_sector': doctor_json.get('regulationSector', 'unknown'),
        'practitioner_type': doctor_json.get('type', 'UNKNOWN'),
        
        # Location with null handling
        'address': location.get('address', ''),
        'city': location.get('city', ''),
        'postal_code': location.get('zipcode', ''),
        'latitude': location.get('lat'),
        'longitude': location.get('lng'),
        
        # References with null protection
        'reference_id': references.get('id'),
        'practice_id': references.get('practiceId'),
        'legacy_id': references.get('lagacyId', ''),
        
        # Online services
        'offers_online_booking': bool(doctor_json.get('onlineBooking')),
        'offers_telehealth': online_booking.get('telehealth', False),
        'online_booking_details': doctor_json.get('onlineBooking'),
        'accepts_new_patients': matched_visit_motive.get('allowNewPatients', True),
        
        # Various JSON fields
        'payment_methods': doctor_json.get('paymentMeans', []),
        'languages': doctor_json.get('languages', []),
        'services': doctor_json.get('services', []),
        'administrative_areas': doctor_json.get('administrativeArea', []),
        
        # Visit motive
        'visit_motive_id': matched_visit_motive.get('visitMotiveId'),
        'visit_motive_name': matched_visit_motive.get('name'),
        'visit_motive_agenda_ids': matched_visit_motive.get('agendaIds', []),
        'visit_motive_insurance_sector': matched_visit_motive.get('insuranceSector'),
        
        # Clinic/Org info
        'organization_status': doctor_json.get('organizationStatus'),
        'cloudinary_public_id': doctor_json.get('cloudinaryPublicId'),
        'exact_match': doctor_json.get('exactMatch', False),
        'minimum_fee': doctor_json.get('minimumFee'),
        
        # Relationship
        'department_id': department_id
    }


def extract_department_data(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Extract department information from a payload"""
    place = payload['location']['place']
    return {
        'name': place['name'],
        'doctolib_id': place['id'],
        'place_id': place.get('placeId'),
        'latitude': place['gpsPoint']['lat'],
        'longitude': place['gpsPoint']['lng'],
        'viewport_ne_lat': place['viewport']['northeast']['lat'],
        'viewport_ne_lng': place['viewport']['northeast']['lng'],
        'viewport_sw_lat': place['viewport']['southwest']['lat'],
        'viewport_sw_lng': place['viewport']['southwest']['lng'],
        'zipcodes': place['zipcodes'],
        'type': place['type']
    }

# Not being called?
def create_doctor_from_json(doctor_json: Dict[str, Any], department_id: int) -> Doctor:
    """Create a Doctor model instance from JSON data"""
    extracted_data = extract_doctor_data(doctor_json, department_id)
    return Doctor(**extracted_data)


def validate_doctor_data(doctor_dict: Dict) -> bool:
    """Validate that doctor data meets minimum requirements"""
    required_fields = ['doctolib_id', 'specialty']

    for field in required_fields:
        if not doctor_dict.get(field):
            logger.error(f"Missing required field: {field}")
            return False
        
        if not isinstance(doctor_dict.get('doctolib_id'), str):
            logger.error("doctolib_id must be a string")
            return False
        
        if not isinstance(doctor_dict.get('payment_methods'), list):
            logger.error("payment_methods must be a list")
            return False
        
        return True