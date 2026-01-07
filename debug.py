import os
from dotenv import load_dotenv
from imap_tools import MailBox

# Load your credentials
load_dotenv()

SERVER = os.getenv("EMAIL_SERVER")
USER = os.getenv("EMAIL_USER")
PASSWORD = os.getenv("EMAIL_PASSWORD")
FOLDER = os.getenv("EMAIL_FOLDER", "INBOX")

print(f"--- DIAGNOSTIC MODE ---")
print(f"Connecting to {SERVER}...")
print(f"Target Folder: {FOLDER}")

try:
    with MailBox(SERVER).login(USER, PASSWORD, FOLDER) as mailbox:
        # 1. List all available folders
        print("\n[1] AVAILABLE FOLDERS:")
        for f in mailbox.folder.list():
            print(f"   - {f.name}")

        # 2. Fetch last 10 emails (Read OR Unread)
        print(f"\n[2] RECENT 10 EMAILS IN '{FOLDER}':")
        # limit=10, reverse=True (Newest first)
        for msg in mailbox.fetch(limit=10, reverse=True):
            print(f"   ------------------------------------------------")
            print(f"   Subject: {msg.subject}")
            print(f"   Date:    {msg.date}")
            print(f"   Flags:   {msg.flags}")
            
            # Check if our keywords would catch this
            is_po = any(k in msg.subject.lower() for k in ["po", "order", "purchase"])
            status = "MATCH" if is_po else "IGNORED (Keyword Mismatch)"
            print(f"   Result:  {status}")

except Exception as e:
    print(f"\n[CRITICAL ERROR] {e}")