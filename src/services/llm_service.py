import google.generativeai as genai
import json
from src.config import GEMINI_API_KEY

genai.configure(api_key=GEMINI_API_KEY)

def extract_from_text(subject, body, content):
    # FIX: Use response_mime_type for native JSON output
    model = genai.GenerativeModel(
        "gemini-1.5-flash",
        generation_config={"response_mime_type": "application/json"}
    )
    
    prompt = f"""
    You are a Logistics Data Expert. Extract PO details to strict JSON.
    
    CONTEXT:
    Subject: {subject}
    Body: {body}
    File Content: {content}
    
    INSTRUCTIONS:
    1. Identify the Vendor from the text and populate "standardized_vendor_name". 
       Use CamelCase or Underscores (e.g., "Reliance_Retail", "Heritage_Foods", "MRF_Internal").
       If uncertain, use "Others".
    2. Extract all PO fields and line items accurately.
    
    REQUIRED OUTPUT STRUCTURE (JSON):
    {{
        "standardized_vendor_name": "string",
        "po_number": "string",
        "customer_name": "string",
        "vendor_name": "string",
        "ship_to_code": "string",
        "ship_to_address": "string",
        "po_date": "YYYY-MM-DD",
        "expected_delivery_date": "YYYY-MM-DD",
        "expiry_date": "YYYY-MM-DD",
        "vendor_gstin": "string",
        "total_amount": float,
        "is_update": boolean,
        "items": [
            {{
                "material_code": "string",
                "description": "string",
                "uom": "string",
                "hsn_code": "string",
                "qty": float,
                "unit_price": float,
                "mrp": float,
                "tax_rate_percent": float,
                "tax_amount": float,
                "line_total": float
            }}
        ]
    }}
    """
    
    try:
        response = model.generate_content(prompt)
        # FIX: No more manual string slicing needed
        return json.loads(response.text)
    except Exception as e:
        print(f"   [LLM Error] {e}")
    return None