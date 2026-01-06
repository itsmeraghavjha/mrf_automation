import os
import pandas as pd
import pdfplumber

EXCEL_ROW_LIMIT = 150

def is_grn_or_junk(text):
    """Detects if text belongs to a GRN (Goods Receipt) or Legal Terms page."""
    text_lower = text.lower()
    
    # GRN Detection
    if "goods receipt note" in text_lower: return True
    if "grn no" in text_lower and "po no" not in text_lower: return True

    # Legal Junk Detection
    if "terms and conditions" in text_lower or "general terms" in text_lower:
        # If it has Quantity/Price, it might be a valid footer, so we keep it.
        if "qty" not in text_lower and "quantity" not in text_lower:
            return True
            
    legal_keywords = ["indemnify", "jurisdiction", "arbitration", "force majeure"]
    if sum(1 for k in legal_keywords if k in text_lower) >= 2: return True
    
    return False

def extract_text_from_file(file_path):
    """Router: Extracts text based on file extension."""
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext == '.pdf':
        return _get_pdf_text(file_path)
    elif ext in ['.xlsx', '.xls', '.csv']:
        return _get_excel_text(file_path)
    return "", False

def _get_pdf_text(file_path):
    text = ""
    try:
        with pdfplumber.open(file_path) as pdf:
            if not pdf.pages: return "", False
            for i, page in enumerate(pdf.pages):
                extracted = page.extract_text() or ""
                
                # Check for junk/GRN
                if is_grn_or_junk(extracted):
                    if i == 0 and "goods receipt note" in extracted.lower():
                        return "", True # Entire file is GRN
                    continue # Skip just this page
                
                text += f"--- PAGE {i+1} ---\n{extracted}\n"
    except Exception as e:
        print(f"   [Parser Error] PDF: {e}")
        return "", False
    return text, False

def _get_excel_text(file_path):
    text = ""
    try:
        ext = os.path.splitext(file_path)[1].lower()
        if ext == '.csv':
            df = pd.read_csv(file_path)
            if "goods receipt note" in str(df.columns).lower(): return "", True
            text += f"--- CSV ---\n{df.head(EXCEL_ROW_LIMIT).to_csv(index=False)}"
        else:
            # Handle xls/xlsx
            engine = 'openpyxl' if ext == '.xlsx' else 'xlrd'
            xls = pd.read_excel(file_path, sheet_name=None, engine=engine)
            for sheet, df in xls.items():
                if "goods receipt note" in str(df.columns).lower(): return "", True
                text += f"--- SHEET: {sheet} ---\n{df.head(EXCEL_ROW_LIMIT).to_csv(index=False)}\n"
    except Exception as e:
        print(f"   [Parser Error] Excel: {e}")
        return "", False
    return text, False