# backend/routes/frontend_routes.py

from flask import Blueprint, render_template, redirect, url_for
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.models.user import User
from backend.models.personal import PersonalExpense, BudgetCategory
from backend.models.shared import Group, SharedExpense, Split
from backend.utils.split_logic import calculate_balances_from_splits
from datetime import datetime
from flask_jwt_extended import (jwt_required, get_jwt_identity, verify_jwt_in_request)

frontend_bp = Blueprint('frontend', __name__)

@frontend_bp.route('/')
def index():
    verify_jwt_in_request(optional=True)
    uid = get_jwt_identity()

    if uid:                          # user already logged in
        return redirect(url_for('frontend.dashboard'))

    # no token ⇒ show public landing page
    return render_template('index.html'), 200

@frontend_bp.route('/login', methods=['GET'])
def login_page():
    return render_template('login.html'), 200

@frontend_bp.route('/register', methods=['GET'])
def register_page():
    return render_template('register.html'), 200

@frontend_bp.route('/dashboard', methods=['GET'])
@jwt_required()
def dashboard():
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    username = user.username if user else 'User'

    # Personal total spent this month
    month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    personal_exps = (
        PersonalExpense.query
        .filter_by(user_id=user_id)
        .filter(PersonalExpense.transaction_date >= month_start)
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
        username=username,
        personal_total=personal_total,
        shared_balance=shared_balance,
        budget_status=budget_status,
        recent_exps=recent_exps,
        groups=groups
    )

@frontend_bp.route('/expenses', methods=['GET'])
@jwt_required()
def personal_expenses():
    return render_template('expenses.html'), 200

@frontend_bp.route('/add-expense', methods=['GET'])
@jwt_required()
def add_expense_page():
    return render_template('add_expense.html'), 200

@frontend_bp.route('/shared', methods=['GET'])
@jwt_required()
def shared_expenses():
    return render_template('shared_expenses.html'), 200

@frontend_bp.route('/group/<int:group_id>', methods=['GET'])
@jwt_required()
def group_detail(group_id):
    return render_template('group_detail.html', group_id=group_id), 200

@frontend_bp.route('/logout', methods=['GET'])
def logout_page():
    return redirect(url_for('frontend.login_page'))

@frontend_bp.route('/groups', methods=['GET'])
@jwt_required()
def groups_page():
    user_id = int(get_jwt_identity())
    return render_template('groups.html', user_id=user_id)
