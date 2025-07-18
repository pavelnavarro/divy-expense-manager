# backend/utils/gemini_utils.py

import os
import json
import re
from dotenv import load_dotenv
from google.generativeai import configure, GenerativeModel

# Load API key from .env
load_dotenv()
_API_KEY = os.getenv("GEMINI_API_KEY")

# Initialize Gemini
if _API_KEY:
    configure(api_key=_API_KEY)
    _MODEL = GenerativeModel("gemini-2.5-flash")
else:
    _MODEL = None


def categorize_expense_text(description: str, context_notes: str = None):
    """
    Use Gemini to suggest a category, recurrency, and an insight for a single expense.
    Returns a dict, e.g.
      {
        "category": "Food",
        "recurring": "No",
        "insight": "You spent more than usual on dining out this week."
      }
    On failure or missing API key, returns a minimal fallback.
    """
    if not _MODEL:
        return {"category": "Other", "recurring": "Unknown", "insight": ""}

    prompt = f"""
You are an expense categorization assistant.

Description: {description}
Notes: {context_notes or 'None'}

Please respond in JSON with:
{{"category": "...", "recurring": "Yes/No", "insight": "..."}}
"""
    try:
        resp = _MODEL.generate_content(prompt).text
        return json.loads(resp)
    except Exception:
        # if it didn't come back as JSON, return raw text
        return {"raw": resp}


def split_expense_with_context(
    description: str,
    amount: float,
    participants: list[str],
    context_notes: str = "",
):
    """
    Ask Gemini how to split a shared expense.

    `participants` is a list of usernames (e.g. ['daniel', 'ana', 'luis'])
    Returns a dict: {username → amount_owed}
    """

    # Detect exclusions like: "Exclude Daniel", "excluding ana"
    excluded = []
    lowered_context = context_notes.lower()
    for name in participants:
        # detect if the name appears near 'exclude', 'excluding', 'except', etc.
        pattern = rf"\b(exclude|excluding|except)\b[^.]*\b{name.lower()}\b"
        if re.search(pattern, lowered_context):
            excluded.append(name)

    # Keep only those not mentioned as excluded
    included = [p for p in participants if p not in excluded]

    if not included:
        return {"error": "All participants were excluded or none found."}

    # fallback (if Gemini disabled)
    if not _MODEL:
        share = round(amount / len(included), 2)
        return {p: share for p in included}

    # Build prompt
    members_csv = ", ".join(included)
    prompt = f"""
You are helping divide a shared expense of ${amount:.2f}.

Description: {description}
Participants: {members_csv}
Context: {context_notes or 'None'}

Please respond in JSON with a map of each participant to what they owe, e.g.:
{{"alice": 12.5, "bob": 12.5}}
"""

    try:
        response_text = _MODEL.generate_content(prompt).text
        return json.loads(response_text)
    except Exception:
        return {"raw": response_text}

def extract_from_receipt(image_data_bytes: bytes, context_notes: str = ""):
    """
    Use Gemini’s vision endpoint to parse a receipt image.
    Returns either a parsed dict (if valid JSON) or the raw text.
    """
    if not _MODEL:
        return "No Gemini model configured."

    # Build the multi-part prompt
    user_part = {
        "role": "user",
        "parts": [
            {"text": f"Extract vendor, total, and category from this receipt. {context_notes}"},
            {
                "inline_data": {
                    "mime_type": "image/jpeg",
                    "data": image_data_bytes
                }
            }
        ],
    }
    try:
        resp = _MODEL.generate_content(contents=[user_part]).text
        # try JSON parse
        return json.loads(resp)
    except Exception:
        return resp

