from imap_tools import MailBox, AND
import datetime
import sys
from src.config import EMAIL_CONFIG, FILTERS

class EmailService:
    def __init__(self):
        self.server = EMAIL_CONFIG['server']
        self.user = EMAIL_CONFIG['email']
        self.password = EMAIL_CONFIG['password']
        self.folder = EMAIL_CONFIG['folder']

    def fetch_emails(self, last_uid=0):
        tasks = []
        max_uid = last_uid

        print(f"   [IMAP] Connecting to {self.folder}...")
        
        try:
            with MailBox(self.server).login(self.user, self.password, self.folder) as mailbox:
                # --- FORCE DATE TO PAST (2025) ---
                start_dt = datetime.date(2026, 1, 1) 
                
                if last_uid == 0:
                    print(f"   [IMAP] Searching for emails since {start_dt}...")
                    emails = mailbox.fetch(AND(date_gte=start_dt), reverse=True)
                else:
                    print(f"   [IMAP] Searching for emails newer than UID {last_uid}...")
                    emails = mailbox.fetch(AND(uid=f"{last_uid + 1}:*"), reverse=True)

                count_total = 0
                for msg in emails:
                    count_total += 1
                    try:
                        uid = int(msg.uid)
                        if uid > max_uid: max_uid = uid
                    except: continue

                    # 1. Check Subject Keywords
                    subject_lower = msg.subject.lower()
                    is_po = any(k.lower() in subject_lower for k in FILTERS['subject_keywords'])
                    
                    if not is_po:
                        # Silently skip non-matches to keep console clean
                        continue

                    print(f"   [FOUND] '{msg.subject}'")

                    # 2. Check Blocked Keywords
                    if any(k.lower() in subject_lower for k in FILTERS['blocked_keywords']):
                        print(f"       -> [SKIP] Blocked keyword found.")
                        continue

                    # 3. Check Attachments (CRITICAL STEP)
                    if not msg.attachments:
                        print(f"       -> [SKIP] No attachments found.")
                        continue

                    valid_atts = []
                    for att in msg.attachments:
                        ext = att.filename.split('.')[-1].lower()
                        # Add the dot back for comparison (e.g., "pdf" -> ".pdf")
                        if f".{ext}" in FILTERS['allowed_extensions']:
                            valid_atts.append(att)
                            print(f"       -> [KEEP] Found valid file: {att.filename}")
                        else:
                            print(f"       -> [IGNORE] Invalid extension: {att.filename}")

                    if valid_atts:
                        tasks.append({
                            'subject': msg.subject,
                            'body': msg.text or msg.html,
                            'date': msg.date,
                            'sender': msg.from_,
                            'attachments': valid_atts
                        })
                
                print(f"   [IMAP] Scanned {count_total} emails. Queued {len(tasks)} for processing.")
                        
        except Exception as e:
            print(f"   [IMAP ERROR] {e}")
            
        return tasks, max_uid