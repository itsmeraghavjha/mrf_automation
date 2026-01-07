import gspread
from googleapiclient.discovery import build
from src.services.drive_service import DriveService
from src.config import REPORTS_FOLDER_ID
import datetime

MAX_ROWS_PER_SHEET = 5000 

class SheetsService:
    def __init__(self):
        self.drive_manager = DriveService()
        self.creds = self.drive_manager.creds
        self.gc = gspread.authorize(self.creds)
        self.drive_service = build('drive', 'v3', credentials=self.creds)
        self.active_files = {} 

    def get_target_sheet_id(self, date_obj):
        date_str = date_obj.strftime("%Y-%m-%d")
        if date_str in self.active_files:
            return self.active_files[date_str]

        base_name = f"MRF_Report_{date_str}"
        query = f"name contains '{base_name}' and '{REPORTS_FOLDER_ID}' in parents and trashed = false"
        results = self.drive_service.files().list(q=query, orderBy="createdTime desc", fields="files(id)").execute()
        files = results.get('files', [])

        if files:
            self.active_files[date_str] = files[0]['id']
            return files[0]['id']
        else:
            return self._create_new_spreadsheet(base_name, date_str)

    def _create_new_spreadsheet(self, file_name, date_str):
        print(f"   [Sheets] Creating new Report: {file_name}")
        sh = self.gc.create(file_name)
        new_id = sh.id
        
        file = self.drive_service.files().get(fileId=new_id, fields='parents').execute()
        previous_parents = ",".join(file.get('parents'))
        self.drive_service.files().update(
            fileId=new_id, addParents=REPORTS_FOLDER_ID, removeParents=previous_parents
        ).execute()

        ws1 = sh.sheet1
        ws1.update_title("Sheet1")
        ws1.append_row([
            "PO Number", "Date", "Customer", "Vendor", "Ship To Code", "Ship To Address", 
            "Delivery Date", "Expiry Date", "GSTIN", "Total Amount", "Item Count", 
            "Is Update?", "Timestamp", "Drive Link"
        ])
        
        ws2 = sh.add_worksheet(title="Sheet2", rows=1000, cols=20)
        ws2.append_row([
            "PO Number (FK)", "Material Code", "Description", "UOM", "HSN", 
            "Qty", "Unit Price", "MRP", "Tax Rate", "Tax Amount", "Line Total", "Timestamp"
        ])

        self.active_files[date_str] = new_id
        return new_id

    def upsert_po(self, data, email_date_obj, drive_link=""):
        sheet_id = self.get_target_sheet_id(email_date_obj)
        sh = self.gc.open_by_key(sheet_id)
        ws1 = sh.sheet1
        ws2 = sh.worksheet("Sheet2")
        
        po_num = str(data.get('po_number')).strip()
        existing_pos = ws1.col_values(1)
        
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # --- Update Sheet1 (Headers) ---
        row = [
            po_num, data.get('po_date'), data.get('customer_name'), data.get('standardized_vendor_name'),
            data.get('ship_to_code'), data.get('ship_to_address'), data.get('expected_delivery_date'),
            data.get('expiry_date'), data.get('vendor_gstin'), data.get('total_amount'),
            len(data.get('items', [])), "YES" if data.get('is_update') else "NO", timestamp, drive_link
        ]

        if po_num in existing_pos:
            print(f"   [Sheets] Updating existing PO: {po_num}")
            row_idx = existing_pos.index(po_num) + 1
            ws1.update(values=[row], range_name=f"A{row_idx}:N{row_idx}")
            
            # --- FIX: Clean up old items in Sheet2 before appending new ones ---
            try:
                # This logic finds all rows matching the PO and deletes them
                # We iterate backwards to prevent index shifting issues
                s2_po_col = ws2.col_values(1)
                rows_to_delete = [i + 1 for i, x in enumerate(s2_po_col) if x == po_num]
                
                if rows_to_delete:
                    # Batch deletion is tricky in gspread without raw API, doing reverse loop
                    for r_idx in reversed(rows_to_delete):
                        ws2.delete_rows(r_idx)
            except Exception as e:
                print(f"   [Sheets Warning] Failed to clear old items: {e}")

        else:
            ws1.append_row(row)

        # --- Update Sheet2 (Items) ---
        items_list = data.get('items', [])
        if items_list:
            item_rows = []
            for item in items_list:
                item_rows.append([
                    po_num, item.get('material_code'), item.get('description'), item.get('uom'),
                    item.get('hsn_code'), item.get('qty'), item.get('unit_price'), item.get('mrp'),
                    item.get('tax_rate_percent'), item.get('tax_amount'), item.get('line_total'), timestamp
                ])
            ws2.append_rows(item_rows)