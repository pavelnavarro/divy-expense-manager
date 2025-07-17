# backend/routes/frontend_routes.py

from flask import Blueprint, render_template, redirect, url_for
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.models.personal import PersonalExpense, BudgetCategory
from backend.models.shared import Group, SharedExpense, Split
from backend.extensions import db
from backend.utils.split_logic import calculate_balances_from_splits
from datetime import datetime

frontend_bp = Blueprint('frontend', __name__)

@frontend_bp.route('/')
def index():
    # If logged in, go to dashboard; otherwise to login
    return redirect(url_for('frontend.dashboard'))

@frontend_bp.route('/dashboard')
@jwt_required()
def dashboard():
    user_id = int(get_jwt_identity())

    # Personal total spent this month
    since = datetime(datetime.utcnow().year, datetime.utcnow().month, 1)
    personal_exps = (
        PersonalExpense.query
        .filter_by(user_id=user_id)
        .filter(PersonalExpense.transaction_date >= since)
        .all()
    )
    personal_total = sum(e.amount for e in personal_exps)

    # Shared balance across your groups
    groups = Group.query.filter(Group.members.any(id=user_id)).all()
    shared_balance = 0.0
    for grp in groups:
        for exp in SharedExpense.query.filter_by(group_id=grp.id):
            splits = Split.query.filter_by(expense_id=exp.id).all()
            bal = calculate_balances_from_splits(splits, exp.paid_by)
            shared_balance += bal.get(user_id, 0)

    # Budget status
    budgets = BudgetCategory.query.filter_by(user_id=user_id).all()
    if budgets:
        over = any(b.current_spending > b.monthly_limit for b in budgets)
        budget_status = "Over budget" if over else "Under budget"
    else:
        budget_status = "No budget set"

    # Recent 5 personal expenses
    recent_exps = sorted(
        personal_exps,
        key=lambda e: e.transaction_date,
        reverse=True
    )[:5]

    return render_template(
        'dashboard.html',
        personal_total=personal_total,
        shared_balance=shared_balance,
        budget_status=budget_status,
        recent_exps=recent_exps
    )
@frontend_bp.route('/personal')
@jwt_required()
def personal_expenses():
    # The page will fetch via JS from /api/personal/expenses
    return render_template('personal_expenses.html')

@frontend_bp.route('/shared')
@jwt_required()
def shared_expenses():
    # The page will fetch via JS from /api/shared/groups etc.
    return render_template('shared_expenses.html')

@frontend_bp.route('/payment-center')
@jwt_required()
def payment_center():
    return render_template('payment_center.html')

@frontend_bp.route('/analytics')
@jwt_required()
def analytics():
    return render_template('analytics.html')

@frontend_bp.route('/settings')
@jwt_required()
def settings():
    return render_template('settings.html')

@frontend_bp.route('/login', methods=['GET'])
def login_page():
    return render_template('login.html'), 200

@frontend_bp.route('/register', methods=['GET'])
def register_page():
    return render_template('register.html'), 200

@frontend_bp.route('/logout', methods=['GET'])
def logout_page():
    # we’re using JWT in the client, so logout is simply clearing the token in JS
    # we’ll just redirect to login.html and let the client-side script wipe any stored token
    return redirect(url_for('frontend.login_page'))