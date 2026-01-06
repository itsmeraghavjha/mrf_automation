from imap_tools import MailBox, AND
import datetime
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

        try:
            with MailBox(self.server).login(self.user, self.password, self.folder) as mailbox:
                if last_uid == 0:
                    start_dt = datetime.date(2026, 1, 6) # Adjust start date as needed
                    emails = mailbox.fetch(AND(date_gte=start_dt), reverse=False)
                else:
                    emails = mailbox.fetch(AND(uid=f"{last_uid + 1}:*"), reverse=False)

                for msg in emails:
                    try:
                        uid = int(msg.uid)
                        if uid > max_uid: max_uid = uid
                    except: continue

                    # Filter Check
                    if not any(k in msg.subject.lower() for k in FILTERS['subject_keywords']): continue
                    if any(k in msg.subject.lower() for k in FILTERS['blocked_keywords']): continue
                    
                    # Attachment Check
                    valid_atts = []
                    for att in msg.attachments:
                        ext = att.filename.split('.')[-1].lower()
                        if f".{ext}" in FILTERS['allowed_extensions']:
                            valid_atts.append(att)

                    if valid_atts:
                        tasks.append({
                            'subject': msg.subject,
                            'body': msg.text or msg.html,
                            'date': msg.date,
                            'sender': msg.from_,
                            'attachments': valid_atts
                        })
                        
        except Exception as e:
            print(f"   [Email Error] {e}")
            
        return tasks, max_uid