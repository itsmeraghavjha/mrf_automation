import os
import time
import sys
import shutil
from src.services.email_service import EmailService
from src.services.drive_service import DriveService
from src.services.sheet_service import SheetsService
from src.services.llm_service import extract_from_text
from src.utils.parsers import extract_text_from_file

CHECKPOINT_FILE = "checkpoint.txt"
CHECK_INTERVAL = 60
TEMP_DIR = "temp_processing"

def get_checkpoint():
    if os.path.exists(CHECKPOINT_FILE):
        try:
            with open(CHECKPOINT_FILE, 'r') as f:
                return int(f.read().strip())
        except: pass
    return 0

def save_checkpoint(uid):
    with open(CHECKPOINT_FILE, 'w') as f:
        f.write(str(uid))

def identify_vendor(subject, sender):
    s = subject.lower()
    if "reliance" in s: return "Reliance_Retail"
    if "heritage" in s: return "Heritage_Internal"
    return "Others"

def process_attachment(att, email_data, drive_svc, sheet_svc):
    if not os.path.exists(TEMP_DIR): os.makedirs(TEMP_DIR)
    local_path = os.path.join(TEMP_DIR, att.filename)
    
    try:
        # Save
        with open(local_path, 'wb') as f:
            f.write(att.payload)

        # Extract Text
        file_text, is_grn = extract_text_from_file(local_path)
        if is_grn:
            print(f"   [SKIP] GRN Detected: {att.filename}")
            return
        if not file_text:
            print(f"   [SKIP] Unreadable: {att.filename}")
            return

        # Upload
        date = email_data['date']
        vendor = identify_vendor(email_data['subject'], email_data['sender'])
        folder_path = ["MRF-POs", vendor, str(date.year), f"{date.month:02d}"]
        
        folder_id = drive_svc.get_or_create_path(folder_path)
        with open(local_path, 'rb') as f:
            file_id, _ = drive_svc.upload_file(f.read(), att.filename, folder_id)
            drive_link = f"https://drive.google.com/file/d/{file_id}/view"

        # AI Extract
        print(f"   [AI] Processing {att.filename}...")
        data = extract_from_text(email_data['subject'], email_data['body'], file_text)
        
        if data:
            sheet_svc.upsert_po(data, date, drive_link)
            print(f"   [SUCCESS] Saved PO: {data.get('po_number')}")
        else:
            print("   [FAIL] AI extraction failed.")

    except Exception as e:
        print(f"   [ERROR] File Error: {e}")
    finally:
        if os.path.exists(local_path): os.remove(local_path)

def run_pipeline():
    last_uid = get_checkpoint()
    email_svc = EmailService()
    drive_svc = DriveService()
    sheet_svc = SheetsService()
    
    print(f"\n[-] Checking for emails (Last UID: {last_uid})...")
    tasks, max_uid = email_svc.fetch_emails(last_uid)
    
    if not tasks:
        print("[-] No new tasks.")
        return

    print(f"[-] Processing {len(tasks)} emails...")
    for task in tasks:
        print(f"\n--- Email: {task['subject']} ---")
        for att in task['attachments']:
            process_attachment(att, task, drive_svc, sheet_svc)
            time.sleep(2) # Safety delay
    
    if max_uid > last_uid:
        save_checkpoint(max_uid)

if __name__ == "__main__":
    if os.path.exists(TEMP_DIR): shutil.rmtree(TEMP_DIR)
    print("=== MRF AUTOMATION SERVICE STARTED ===")
    while True:
        try:
            run_pipeline()
            time.sleep(CHECK_INTERVAL)
        except KeyboardInterrupt:
            sys.exit()
        except Exception as e:
            print(f"[CRITICAL] {e}")
            time.sleep(30)