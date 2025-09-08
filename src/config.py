# src/config.py
import os
from dotenv import load_dotenv

#Load variables from .env file
load_dotenv()

USER_AGENT = os.getenv('USER_AGENT')
# Add other config settings here

BASE_URL = "https://doctolib.fr"
API_ENDPOINT = "/phs_proxy/raw"