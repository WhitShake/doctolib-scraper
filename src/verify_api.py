# src/verify_api.py
import json
import requests

def verify_api_response():
    """Verify the quality and structure of the API response"""
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Referer': 'https://www.doctolib.fr/search',
    }
    
    test_payload = {
        "keyword": "medecin-generaliste",
        "location": {
            "place": {
                "id": 693478,
                "name": "France", 
                "country": "fr",
                "type": "country"
            }
        },
        "filters": {}
    }
    
    response = requests.post(
        'https://www.doctolib.fr/phs_proxy/raw?page=0',
        headers=headers,
        json=test_payload
    )
    
    if response.status_code == 200:
        data = response.json()
        
        print("=== API RESPONSE VERIFICATION ===")
        print(f"Total results: {data.get('total', 'Unknown')}")
        print(f"Doctors in this page: {len(data.get('healthcareProviders', []))}")
        print()
        
        # Show first doctor's structure
        if data.get('healthcareProviders'):
            first_doctor = data['healthcareProviders'][0]
            print("=== FIRST DOCTOR STRUCTURE ===")
            print(json.dumps(first_doctor, indent=2, ensure_ascii=False)[:1000] + "...")
            
            # Check for key fields
            key_fields = ['firstName', 'name', 'speciality', 'location', 'onlineBooking']
            print("\n=== KEY FIELDS PRESENT ===")
            for field in key_fields:
                exists = field in first_doctor
                print(f"{field}: {'✅' if exists else '❌'}")
        
        # Save sample for reference
        with open('sample_api_response.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print("\n💾 Sample response saved to 'sample_api_response.json'")

if __name__ == "__main__":
    verify_api_response()