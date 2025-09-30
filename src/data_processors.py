# src/data_processors.py
"""
Utility functions for processing and transforming Doctolib API data
"""
import json
from typing import Dict, Any
from models import Doctor


def extract_doctor_data(doctor_json, department_id):
    """Extract all available data from Doctolib doctor JSON"""
    
    # Determine if this is an individual or organization
    is_organization = doctor_json.get('firstName') is None and doctor_json.get('name') is not None

    # Handle null values
    online_booking = doctor_json.get('onlineBooking') or {}
    matched_visit_motive = doctor_json.get('matchedVisitMotive') or {}

    # Extract city information and get or create city ID
    city_name = doctor_json['location']['city']
    postal_code = doctor_json['location']['zipcode']
    
    return {
        'doctolib_id': doctor_json['id'],
        'profile_url': doctor_json['link'],
        
        # Name handling for individuals vs organizations
        'first_name': doctor_json.get('firstName'),
        'last_name': doctor_json.get('name') if not is_organization else None,
        'organization_name': doctor_json.get('name') if is_organization else None,
        'is_organization': is_organization,
        
        'title': doctor_json.get('title'),
        'gender': doctor_json.get('gender'),
        'specialty': doctor_json['speciality']['name'],
        'specialty_slug': doctor_json['speciality']['slug'],
        'regulation_sector': doctor_json.get('regulationSector'),
        'practitioner_type': doctor_json.get('type'),
        
        # Location
        'address': doctor_json['location']['address'],
        'city': city_name,
        'postal_code': postal_code,
        'latitude': doctor_json['location']['lat'],
        'longitude': doctor_json['location']['lng'],
        
        # References
        'reference_id': doctor_json['references']['id'],
        'practice_id': doctor_json['references']['practiceId'],
        'legacy_id': doctor_json['references']['legacyId'],
        
        # Online services
        'offers_online_booking': bool(doctor_json.get('onlineBooking')),
        'offers_telehealth': online_booking.get('telehealth', False),
        'online_booking_details': doctor_json.get('onlineBooking'),
        
        # Various JSON fields
        'payment_methods': doctor_json.get('paymentMeans', []),
        'languages': doctor_json.get('languages', []),
        'services': doctor_json.get('services', []),
        'administrative_areas': doctor_json.get('administrativeArea', []),
        
        # Visit motive
        'visit_motive_id': matched_visit_motive.get('visitMotiveId'),
        'visit_motive_name': matched_visit_motive.get('name'),
        'visit_motive_agenda_ids': matched_visit_motive.get('agendaIds'),
        'visit_motive_insurance_sector': matched_visit_motive.get('insuranceSector'),
        
        # Clinic specific
        'organization_status': doctor_json.get('organizationStatus'),
        'cloudinary_public_id': doctor_json.get('cloudinaryPublicId'),
        'exact_match': doctor_json.get('exactMatch', False),
        'minimum_fee': doctor_json.get('minimumFee'),
        
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

def create_doctor_from_json(doctor_json: Dict[str, Any], department_id: int) -> Doctor:
    """Create a Doctor model instance from JSON data"""
    extracted_data = extract_doctor_data(doctor_json, department_id)
    return Doctor(**extracted_data)