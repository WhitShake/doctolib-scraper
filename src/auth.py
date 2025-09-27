# src/auth.py
import requests
from bs4 import BeautifulSoup as bs
import logging

logger = logging.getLogger(__name__)

class DoctoLibSession:
    def __init__(self):
        self.session = requests.Session()
        self.setup_headers()
    
    def setup_headers(self):
        """Set up base headers to look like real browser"""
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
        })

    def get_scrf_token(self):
        """Visit main page to get fresh CSRF token"""
        logger.info("Fetching CSRF token from DoctoLib...")
        response = self.session.get('https://www.doctolib.fr')
        response.raise_for_status()

        # Parse html to find CSRF token
        soup = bs(response.content, 'html.parser')
        csrf_meta = soup.find('meta', attrs={'name': 'csrf-token'})

        if csrf_meta:
            csrf_token = csrf_meta.get('content')
            logger.info(f"Found CSRF token: {csrf_token[:20]}...")
            return csrf_token
        else:
            raise Exception("Could not find CSRF token")
        
        
def setup_api_headers(self, csrf_token):
    """Set up session for API requests"""
    self.session.headers.update({
        'Accept': 'application/json, text/plain, */*',
        'Content-Type': 'application/json',
        'X-CSRF-Token': csrf_token,
        'Referer': 'https://www.doctolib.fr/search',
        'Origin': 'https://www.doctolib.fr',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
    })

def get_authenticated_session(self):
    """Get a fully authenticated session ready for API calls"""
    csrf_token = self.get_csrf_token()
    self.setup_api_headers(csrf_token)
    return self.session