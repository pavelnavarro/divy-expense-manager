from datetime import datetime
from backend.extensions import db

group_members = db.Table('group_members',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('group_id', db.Integer, db.ForeignKey('groups.id'), primary_key=True)
)

class Group(db.Model):
    __tablename__ = 'groups'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Many-to-many relationship
    members = db.relationship('User', secondary=group_members, backref='groups', lazy='dynamic')

    def __repr__(self):
        return f"<Group {self.name}>"

class SharedExpense(db.Model):
    __tablename__ = 'shared_expenses'
    
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'), nullable=False)
    paid_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(50))
    notes = db.Column(db.Text)  # for AI context like: "Juan paid for steak, others just sandwiches"
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    splits = db.relationship('Split', backref='shared_expense', lazy=True)

    def __repr__(self):
        return f"<SharedExpense ${self.amount} - {self.description}>"

class Split(db.Model):
    __tablename__ = 'splits'
    
    id = db.Column(db.Integer, primary_key=True)
    expense_id = db.Column(db.Integer, db.ForeignKey('shared_expenses.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount_owed = db.Column(db.Float, nullable=False)
    is_paid = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f"<Split: User {self.user_id} owes ${self.amount_owed}>"


class Payment(db.Model):
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)
    from_user = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    to_user = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default="pending")  # e.g., pending, completed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Payment ${self.amount} from {self.from_user} to {self.to_user}>"
