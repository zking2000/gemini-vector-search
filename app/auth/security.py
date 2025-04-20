import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_credentials():
    """
    Get API credentials from environment variables (reference only, authentication no longer used)
    """
    username = os.getenv("API_USERNAME", "admin")
    password = os.getenv("API_PASSWORD", "password")
    return {"username": username, "password": password}

# Removed verify_credentials function and HTTP basic authentication logic 