# backend/models/personal.py

from datetime import datetime
from backend.extensions import db

class PersonalExpense(db.Model):
    __tablename__ = 'personal_expenses'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(100), nullable=False)       # from Gemini
    gemini_confidence = db.Column(db.Float, nullable=True)     # AI confidence
    receipt_image_url = db.Column(db.String(255), nullable=True)
    is_recurring = db.Column(db.Boolean, default=False)
    transaction_date = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<PersonalExpense {self.description} - ${self.amount}>"

class BudgetCategory(db.Model):
    __tablename__ = 'budget_categories'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    monthly_limit = db.Column(db.Float, nullable=False)
    current_spending = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<BudgetCategory {self.name} (limit ${self.monthly_limit})>"
