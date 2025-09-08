#src/main.py
import requests
from config import USER_AGENT, BASE_URL, API_ENDPOINT

headers = {
    'User_Agent' : USER_AGENT,
    'Content_Type' : 'application/json',
}

url = f"{BASE_URL}{API_ENDPOINT}?page=0"
print(f"Ready to make a request to: {url}")
print(f"With User-Agent: {USER_AGENT}")
# Request code here