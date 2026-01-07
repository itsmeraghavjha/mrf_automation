import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Email Configuration
EMAIL_CONFIG = {
    "server": os.getenv("EMAIL_SERVER", "imap.gmail.com"),
    "email": os.getenv("EMAIL_USER"),
    "password": os.getenv("EMAIL_PASSWORD"),
    "folder": os.getenv("EMAIL_FOLDER", "INBOX")
}

# API Keys & IDs
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
REPORTS_FOLDER_ID = os.getenv("REPORTS_FOLDER_ID")

# Filtering Rules
FILTERS = {
    "subject_keywords": ["PO", "Purchase Order", "Order"], # Case insensitive
    "allowed_extensions": [".pdf", ".xlsx", ".csv", ".xls"],
    
    "blocked_keywords": [
        "GRN", 
        "Goods Receipt", 
        "Acknowledgement", 
        "Delivered", 
        "Thank you", 
        "Accepted",
        "Payment",
        "marketing", "newsletter", "update", 
        "insurance", "policy", "policies", "compliance", "regulatory"  
    ]
}
# Project Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CREDENTIALS_FILE = os.path.join(BASE_DIR, 'credentials.json')
TOKEN_FILE = os.path.join(BASE_DIR, 'token.json')