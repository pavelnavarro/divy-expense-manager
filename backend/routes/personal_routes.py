# backend/routes/personal_routes.py

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from backend.extensions import db
from backend.models.personal import PersonalExpense
from backend.models.user import User
from backend.utils.gemini_utils import categorize_expense_text
from backend.utils.google_calendar import create_calendar_reminder

personal_bp = Blueprint('personal', __name__)

def _parse_iso_datetime(s: str) -> datetime | None:
    try:
        return datetime.fromisoformat(s)
    except Exception:
        return None

@personal_bp.route('/expenses', methods=['POST'])
@jwt_required()
def add_personal_expense():
    user_id = int(get_jwt_identity())
    data = request.get_json() or {}

    # Campos obligatorios
    amount = data.get('amount')
    description = data.get('description')
    tx_date = data.get('transaction_date')
    is_recurring = bool(data.get('is_recurring', False))

    if amount is None or not description or not tx_date:
        return jsonify(error="`amount`, `description` and `transaction_date` are required"), 400

    try:
        amount = float(amount)
    except ValueError:
        return jsonify(error="`amount` must be a number"), 400

    when = _parse_iso_datetime(tx_date)
    if not when:
        return jsonify(error="`transaction_date` must be ISO‑formatted"), 400

    # Categoría via Gemini
    ai_resp = categorize_expense_text(description, context_notes=None)
    if not isinstance(ai_resp, dict):
        try:
            parsed = {}
            for line in ai_resp.splitlines():
                k, v = line.split(":", 1)
                parsed[k.strip().lower()] = v.strip()
            ai_resp = parsed
        except Exception:
            ai_resp = {}

    category = ai_resp.get('category', 'Uncategorized')
    confidence = ai_resp.get('confidence')

    # Crear y guardar el gasto
    exp = PersonalExpense(
        user_id=user_id,
        amount=amount,
        description=description,
        category=category,
        gemini_confidence=confidence,
        is_recurring=is_recurring,
        transaction_date=when
    )
    db.session.add(exp)
    db.session.flush()  # para obtener exp.id

    # Si es recurrente y el usuario tiene token de Google Calendar, crear recordatorio
    if is_recurring and current_app.config.get('ENABLE_CALENDAR') and hasattr(User, 'google_calendar_token'):
        user = User.query.get(user_id)
        if user and getattr(user, 'google_calendar_token', None):
            try:
                ev_id = create_calendar_reminder(
                    user_token=user.google_calendar_token,
                    expense_description=description,
                    amount=amount,
                    due_date=when
                )
                exp.calendar_event_id = ev_id
            except Exception:
                current_app.logger.exception("Calendar reminder failed")

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify(error="Database error: " + str(e)), 500

    return jsonify(
        message="Personal expense added",
        expense={
            "id": exp.id,
            "amount": exp.amount,
            "description": exp.description,
            "category": exp.category,
            "confidence": exp.gemini_confidence,
            "transaction_date": exp.transaction_date.isoformat(),
            "is_recurring": exp.is_recurring
        }
    ), 201

@personal_bp.route('/expenses/import-mock', methods=['POST'])
@jwt_required()
def import_mock_transactions():
    user_id = int(get_jwt_identity())
    body = request.get_json() or {}
    txns = body.get('transactions', [])
    if not isinstance(txns, list):
        return jsonify(error="`transactions` must be an array"), 400

    imported = []
    for t in txns:
        desc = t.get('description')
        amt = t.get('amount')
        date_s = t.get('transaction_date')
        if not desc or amt is None or not date_s:
            continue
        try:
            amt = float(amt)
        except ValueError:
            continue

        when = _parse_iso_datetime(date_s) or datetime.utcnow()
        ai = categorize_expense_text(desc)
        if not isinstance(ai, dict):
            ai = {}
        category = ai.get('category', 'Uncategorized')

        exp = PersonalExpense(
            user_id=user_id,
            amount=amt,
            description=desc,
            category=category,
            transaction_date=when
        )
        db.session.add(exp)
        imported.append({"description": desc, "amount": amt})

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify(error="Import failed: " + str(e)), 500

    return jsonify(
        message=f"Imported {len(imported)} transactions",
        imported=imported
    ), 200

@personal_bp.route('/expenses', methods=['GET'])
@jwt_required()
def list_personal_expenses():
    user_id = int(get_jwt_identity())
    since_s = request.args.get('since')
    q = PersonalExpense.query.filter_by(user_id=user_id)
    if since_s:
        since = _parse_iso_datetime(since_s)
        if since:
            q = q.filter(PersonalExpense.transaction_date >= since)

    exps = q.order_by(PersonalExpense.transaction_date.desc()).all()
    result = [{
        "id": e.id,
        "amount": e.amount,
        "description": e.description,
        "category": e.category,
        "transaction_date": e.transaction_date.isoformat(),
        "is_recurring": e.is_recurring
    } for e in exps]

    return jsonify(expenses=result), 200

@personal_bp.route('/expenses/<int:expense_id>', methods=['DELETE'])
@jwt_required()
def delete_personal_expense(expense_id):
    user_id = int(get_jwt_identity())
    exp = PersonalExpense.query.filter_by(id=expense_id, user_id=user_id).first_or_404()
    db.session.delete(exp)
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify(error="Could not delete: " + str(e)), 500
    return jsonify(message=f"Expense {expense_id} deleted"), 200
