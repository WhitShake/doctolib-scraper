# src/config.py
import os
from dotenv import load_dotenv

#Load variables from .env file
load_dotenv()

USER_AGENT = os.getenv('USER_AGENT')
BASE_URL = "https://www.doctolib.fr"
API_ENDPOINT = "/phs_proxy/raw"

# This is the exact payload structure from the DevTools, converted to Python
PAYLOAD = {
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
            "streetName": None,  # null in DevTools becomes None in Python
            "streetNumber": None,
            "slug": "marseille",
            # IMPORTANT: You can shorten the zipcodes list for testing!
            "zipcodes": ["13000", "13001", "13002", "13003", "13004", "13005"]
        }
    },
    "filters": {}
}
# Add other config settings here

BASE_URL = "https://doctolib.fr"
API_ENDPOINT = "/phs_proxy/raw"