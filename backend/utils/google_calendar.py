# backend/utils/google_calendar.py

import os
import json
from datetime import timedelta, datetime
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

load_dotenv()

def create_calendar_reminder(
    user_token: str,
    expense_description: str,
    amount: float,
    due_date: datetime,
) -> str | None:
    """
    Create a Google Calendar reminder event for a (recurring) personal expense.

    Args:
      user_token: JSON-serialized OAuth2 credentials (from Google Calendar auth).
      expense_description: Short description of the expense.
      amount: Expense amount.
      due_date: When the reminder should fire.

    Returns:
      The Google Calendar event ID, or None if creation failed.
    """
    try:
        # Restore credentials from the stored token
        creds_info = json.loads(user_token)
        creds = Credentials.from_authorized_user_info(creds_info)

        service = build('calendar', 'v3', credentials=creds)

        event = {
            'summary': f'Expense Reminder: {expense_description}',
            'description': f'Reminder for upcoming expense of ${amount:.2f}: {expense_description}',
            'start': {
                'dateTime': due_date.isoformat(),
                'timeZone': 'UTC',  # adjust as needed
            },
            'end': {
                'dateTime': (due_date + timedelta(hours=1)).isoformat(),
                'timeZone': 'UTC',
            },
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'popup', 'minutes': 24 * 60},  # 24 h before
                    {'method': 'popup', 'minutes': 60},       # 1 h before
                ],
            },
        }

        created = service.events().insert(calendarId='primary', body=event).execute()
        return created.get('id')
    except Exception as e:
        # Log the error; route can choose to ignore a missing reminder
        print(f"[google_calendar] failed to create event: {e}")
        return None
