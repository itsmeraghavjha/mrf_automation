import google.generativeai as genai
import json
from src.config import GEMINI_API_KEY

genai.configure(api_key=GEMINI_API_KEY)

def extract_from_text(subject, body, content):
    model = genai.GenerativeModel("gemini-1.5-flash")
    
    prompt = f"""
    You are a Logistics Data Expert. Extract PO details to strict JSON.
    
    CONTEXT:
    Subject: {subject}
    Body: {body}
    File Content: {content}
    
    REQUIRED OUTPUT STRUCTURE (JSON):
    {{
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
        text = response.text.replace("```json", "").replace("```", "")
        start = text.find('{')
        end = text.rfind('}') + 1
        if start != -1 and end != -1:
            return json.loads(text[start:end])
    except Exception as e:
        print(f"   [LLM Error] {e}")
    return None