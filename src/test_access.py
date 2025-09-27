# src/test_access.py
import requests
import logging
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_basic_access():
    """Test if we can access Doctolib and get a basic response"""
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        # Test 1: Basic homepage access
        logger.info("Testing basic homepage access...")
        response = requests.get('https://www.doctolib.fr', headers=headers, timeout=10)
        logger.info(f"Homepage status: {response.status_code}")
        
        if response.status_code == 200:
            logger.info("✅ Successfully accessed homepage")
            # Check if we got a real page or a blocking page
            soup = BeautifulSoup(response.content, 'html.parser')
            title = soup.find('title')
            if title:
                logger.info(f"Page title: {title.text}")
        else:
            logger.error(f"❌ Failed to access homepage: {response.status_code}")
            return False
        
        # Test 2: Search page access
        logger.info("Testing search page access...")
        search_response = requests.get('https://www.doctolib.fr/search', headers=headers, timeout=10)
        logger.info(f"Search page status: {search_response.status_code}")
        
        # Test 3: Check for blocking indicators
        if any(indicator in response.text for indicator in ['cloudflare', 'access denied', 'blocked', 'captcha']):
            logger.warning("⚠️  Possible blocking detected")
        
        return True
        
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Network error: {e}")
        return False

def test_api_access():
    """Test if we can make API requests"""
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Referer': 'https://www.doctolib.fr/search',
    }
    
    # Try a simple API request (might fail without proper auth)
    test_payload = {
        "keyword": "medecin-generaliste",
        "location": {
            "place": {
                "id": 693478,  # France ID we found earlier
                "name": "France",
                "country": "fr",
                "type": "country"
            }
        },
        "filters": {}
    }
    
    try:
        logger.info("Testing API endpoint access...")
        response = requests.post(
            'https://www.doctolib.fr/phs_proxy/raw?page=0',
            headers=headers,
            json=test_payload,
            timeout=15
        )
        
        logger.info(f"API response status: {response.status_code}")
        
        if response.status_code == 200:
            logger.info("✅ API endpoint accessible")
            # Check if we got JSON or an error page
            if response.headers.get('content-type', '').startswith('application/json'):
                data = response.json()
                logger.info(f"Received JSON with {len(data.get('healthcareProviders', []))} doctors")
                return True
            else:
                logger.warning("⚠️  API returned non-JSON response (might be blocked)")
                logger.info(f"Response preview: {response.text[:200]}...")
        elif response.status_code == 403:
            logger.error("❌ Access forbidden - likely blocked by WAF")
        elif response.status_code == 429:
            logger.error("❌ Rate limited - too many requests")
        else:
            logger.error(f"❌ Unexpected status: {response.status_code}")
            
        return False
        
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ API request failed: {e}")
        return False

if __name__ == "__main__":
    print("=== DOCTOLIB ACCESS TEST ===")
    print()
    
    # Test basic access
    basic_ok = test_basic_access()
    print()
    
    # Test API access (might fail without proper session)
    api_ok = test_api_access()
    print()
    
    # Summary
    if basic_ok and api_ok:
        print("🎉 All tests passed! You can proceed with data collection.")
    elif basic_ok and not api_ok:
        print("⚠️  Basic access works, but API is blocked. We'll need to handle authentication.")
    else:
        print("❌ Basic access failed. Check your network connection or VPN.")