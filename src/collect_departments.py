# src/collect_departments.py
import json
import os
import requests
from typing import Dict, List

def get_authenticated_session():
    """Get a session with basic headers"""
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Referer': 'https://www.doctolib.fr/search',
    })
    return session

def test_department_search(session, department_name: str) -> bool:
    """Test if we can search for a specific department"""
    test_payload = {
        "keyword": "medecin-generaliste",
        "location": {
            "place": {
                "name": department_name,
                "country": "fr",
                "type": "department"  # We'll try this type
            }
        },
        "filters": {}
    }
    
    try:
        response = session.post(
            'https://www.doctolib.fr/phs_proxy/raw?page=0',
            json=test_payload,
            timeout=10
        )
        return response.status_code == 200
    except:
        return False

def setup_department_collection():
    """Create a structured approach to collect department data"""
    
    departments = [
        "Ain", "Aisne", "Allier", "Alpes-de-Haut-Provence", "Hautes-Alpes",
        "Alpes-Maritimes", "Ardèche", "Ardennes", "Ariège", "Aube", "Aude", 
        "Aveyron", "Bouches-du-Rhône", "Calvados", "Cantal", "Charente", 
        "Charente-Maritime", "Cher", "Corrèze", "Corse-du-Sud", "Haute-Corse", 
        "Côte d'Or", "Côtes d'Armor", "Creuse", "Dordogne", "Doubs", "Drôme", 
        "Eure", "Eure-et-Loir", "Finistère", "Gard", "Haute-Garonne", "Gers", 
        "Gironde", "Hérault", "Ille-et-Vilaine", "Indre", "Indre-et-Loire", 
        "Isère", "Jura", "Landes", "Loir-et-Cher", "Loire", "Haute-Loire", 
        "Loire-Atlantique", "Loiret", "Lot", "Lot-et-Garonne", "Lozère", 
        "Maine-et-Loire", "Manche", "Marne", "Haute-Marne", "Mayenne", 
        "Meurthe-et-Moselle", "Meuse", "Morbihan", "Moselle", "Nièvre", "Nord", 
        "Oise", "Orne", "Pas-de-Calais", "Puy-de-Dôme", "Pyrénées-Atlantiques", 
        "Hautes-Pyrénées", "Pyrénées-Orientales", "Bas-Rhin", "Haut-Rhin", 
        "Rhône", "Haute-Saône", "Saône-et-Loire", "Sarthe", "Savoie", 
        "Haute-Savoie", "Paris", "Seine-Maritime", "Seine-et-Marne", "Yvelines", 
        "Deux-Sèvres", "Somme", "Tarn", "Tarn-et-Garonne", "Var", "Vaucluse", 
        "Vendée", "Vienne", "Haute-Vienne", "Vosges", "Yonne", 
        "Territoire de Belfort", "Essonne", "Hauts-de-Seine", 
        "Seine-Saint-Denis", "Val-de-Marne", "Val d'Oise", "Guadeloupe", 
        "Martinique", "Guyane", "La Réunion", "Mayotte"
    ]
    
    # Create directory for raw payloads
    os.makedirs("department_payloads", exist_ok=True)
    
    session = get_authenticated_session()
    
    print("=== DOCTOLIB DEPARTMENT DATA COLLECTION ===")
    print("We'll test a few departments first to see if the simple search works.")
    print()
    
    # Test with a few departments first
    test_departments = ["Paris", "Rhône", "Bouches-du-Rhône", "Gironde"]
    
    for dept in test_departments:
        print(f"Testing search for: {dept}")
        if test_department_search(session, dept):
            print(f"✅ '{dept}' - Simple search works!")
        else:
            print(f"❌ '{dept}' - Will need manual payload collection")
    print()
    
    print("Now proceeding with manual collection for all departments...")
    print("For each department, you will:")
    print("1. Go to https://www.doctolib.fr")
    print("2. Search for the department name")
    print("3. Copy the API payload from Network tab")
    print("4. Paste it here")
    print()
    
    # Continue with the manual collection process...
    # [Rest of the previous collection script here]

if __name__ == "__main__":
    setup_department_collection()