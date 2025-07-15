import os
from google import genai
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel("gemini-2.5-flash")

def categorize_expense_text(description, context_notes=None):
    """Use Gemini to suggest a category and insight from a text-only expense"""
    prompt = f"""
You are an expense categorization assistant.

Description: {description}
Notes: {context_notes or "None"}

Please return:
1. Suggested category (like Food, Rent, Subscriptions)
2. Whether it's recurring (Yes/No)
3. A short spending insight (1 sentence)
"""
    response = model.generate_content(prompt)
    return response.text

def split_expense_with_context(description, amount, members, context_note):
    """Gemini suggests how to split a group expense based on user notes and participants"""
    member_list = ", ".join(members)
    prompt = f"""
You are helping divide a shared expense of ${amount}.

Description: {description}
Participants: {member_list}
Context: {context_note}

Please return:
- Who should be included/excluded
- How much each participant should owe
- Justification in 1–2 lines
"""
    response = model.generate_content(prompt)
    return response.text

def extract_from_receipt(image_data_bytes, context_note=""):
    """Gemini parses a receipt image and returns key data."""
    response = model.generate_content(
        contents=[
            {
                "role": "user",
                "parts": [
                    {"text": f"Extract vendor, total, and category from this receipt. {context_note}"},
                    {
                        "inline_data": {
                            "mime_type": "image/jpeg",
                            "data": image_data_bytes
                        }
                    }
                ]
            }
        ]
    )
    return response.text
