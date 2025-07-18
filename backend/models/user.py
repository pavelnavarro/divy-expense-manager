# backend/models/user.py

from datetime import datetime
from backend.extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.dialects.postgresql import JSON

class User(db.Model):
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    google_calendar_token = db.Column(JSON, nullable=True)
    
    # -- relationships --
    # personal expenses
    personal_expenses = db.relationship('PersonalExpense', backref='user', lazy='dynamic')
    # which groups this user belongs to (via the group_members association table)
    #groups = db.relationship(
    #    'Group',
    #    secondary='group_members',
    #    backref=db.backref('users', lazy='dynamic'),
    #    lazy='dynamic'
    #)
    # splits owed/to be paid
    splits = db.relationship('Split', backref='user', lazy='dynamic')
    # payments sent and received
    payments_sent = db.relationship(
        'Payment',
        foreign_keys='Payment.from_user',
        backref='sender',
        lazy='dynamic'
    )
    payments_received = db.relationship(
        'Payment',
        foreign_keys='Payment.to_user',
        backref='recipient',
        lazy='dynamic'
    )

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.username}>"
