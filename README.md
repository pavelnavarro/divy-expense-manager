# Divy – Personal & Social Expense Manager 💸

Divy is a modern web application that helps users manage both personal and shared expenses, making group finances simple, transparent, and stress-free.

## 🚀 Core Features

- **Track personal & group expenses** easily  
- **Create groups** (roommates, trips, events, etc.)  
- **Smart split logic** that minimizes transactions  
- **AI-powered insights** and upcoming receipt scanning  

## 💡 The Problem

- 68% of millennials say money stress affects relationships  
- 76% of young adults don’t use budgeting tools  
- Students overspend ~$1,200/year due to poor expense visibility  
- 43% avoid group activities due to awkward reimbursements  

Divy tackles this by making group expense management simple, automated, and social.

## 🧠 AI-Powered Assistance

- Smart suggestions on “who pays whom”
- Funny, human-like comments from Gemini AI
- Future: expense classification and receipt parsing

## 🔒 Authentication

- Secure JWT-based login and registration  
- Google OAuth 2.0 for Google Calendar integration  

## 📅 Google Calendar Integration

- Reminders are created for group members 3 days after an expense  
- Users can connect their Google Calendar accounts seamlessly  

## 📸 Receipt Scanner (Coming Soon)

- Upload a receipt image instead of typing an amount  
- Uses Gemini to extract amounts, payer, and purpose  

## 🛠️ Tech Stack

- **Backend:** Python, Flask, SQLAlchemy, SQLite  
- **Frontend:** HTML, CSS, JavaScript (vanilla)  
- **AI Integration:** Gemini 2.5 Flash (Google)  
- **Calendar:** Google Calendar API  
- **Auth:** JWT + Google OAuth  

## 🧪 Testing

- Unit-tested key functions (`split_logic.py`, Gemini helpers)  
- Frontend behavior tested via manual test cases  

## 📂 Project Structure

