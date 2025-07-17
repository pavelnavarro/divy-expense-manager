# backend/routes/shared_routes.py

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.extensions import db
from backend.models.shared import Group, SharedExpense, Split, Payment
from backend.models.user import User
from backend.utils.split_logic import calculate_balances_from_splits, minimize_cash_flow, filter_members
from backend.utils.gemini_utils import split_expense_with_context, extract_from_receipt

shared_bp = Blueprint('shared', __name__)

#
# Group endpoints
#

@shared_bp.route('/groups', methods=['POST'])
@jwt_required()
def create_group():
    """Create a new group with a list of member IDs."""
    data = request.get_json() or {}
    name       = data.get('name')
    member_ids = data.get('members', [])
    created_by = int(get_jwt_identity())

    if not name:
        return jsonify(error="Missing group name"), 400
    
    group = Group(name=name, created_by=created_by)
    db.session.add(group)
    db.session.flush()  # so group.id is available

    # always include creator
    creator = User.query.get(created_by)
    if creator:
       group.members.append(creator)

    users = User.query.filter(User.id.in_(member_ids)).all()
    group.members.extend(users)
    db.session.commit()

    return jsonify(
        message="Group created",
        group_id=group.id,
        members=[u.id for u in users]
    ), 201

@shared_bp.route('/groups/<int:user_id>', methods=['GET'])
def get_user_groups(user_id):
    """List all groups a user belongs to."""
    user = User.query.get_or_404(user_id)
    groups = user.groups.all()

    result = [{
        "group_id": g.id,
        "name": g.name,
        "created_by": g.created_by,
        "created_at": g.created_at.isoformat()
    } for g in groups]

    return jsonify(groups=result), 200

@shared_bp.route('/groups', methods=['GET'])
@jwt_required()
def get_my_groups():
    user_id = int(get_jwt_identity())
    user = User.query.get_or_404(user_id)
    groups = user.groups.all()
    result = [{
        "id": g.id,
        "name": g.name,
        "created_at": g.created_at.isoformat(),
        "created_by": g.created_by,
        "members": [{"id": u.id, "username": u.username} for u in g.members]
    } for g in groups]
    return jsonify(result), 200

@shared_bp.route('/group/<int:group_id>', methods=['GET'])
def get_group_info(group_id):
    """Get basic info and member list for a group."""
    group = Group.query.get_or_404(group_id)
    return jsonify({
        "id": group.id,
        "name": group.name,
        "created_by": group.created_by,
        "members": [{"id": u.id, "username": u.username} for u in group.members]
    }), 200

#
# Shared expense endpoints
#

@shared_bp.route('/expense', methods=['POST'])
def add_shared_expense():
    """
    Add a new shared expense.
    Expects JSON: description, amount, group_id, paid_by,
                  excluded_members (opt), context (opt)
    """
    data = request.get_json() or {}
    description = data.get('description')
    amount = float(data.get('amount', 0))
    group_id = data.get('group_id')
    paid_by = data.get('paid_by')
    excluded = data.get('excluded_members', [])
    context = data.get('context', '')

    group = Group.query.get_or_404(group_id)
    member_ids = [u.id for u in group.members]
    included_users = [u for u in group.members if u.id not in excluded]
    included = [u.id for u in included_users]
    participants = [u.username for u in included_users]

    splits_suggestion = split_expense_with_context(description, amount, participants, context)

    # Fallback to equal split if Gemini returns invalid data
    if (
        not isinstance(splits_suggestion, dict)
        or any(not isinstance(v, (int, float)) for v in splits_suggestion.values())
    ):
        share = round(amount / len(included), 2) if included else 0
        splits_suggestion = {uid: share for uid in included}

    expense = SharedExpense(
        group_id=group_id,
        paid_by=paid_by,
        amount=amount,
        description=description,
        notes=context
    )
    db.session.add(expense)
    db.session.flush()

    for uid, owed in splits_suggestion.items():
        db.session.add(Split(
            expense_id=expense.id,
            user_id=uid,
            amount_owed=round(owed, 2),
            is_paid=(uid == paid_by)
        ))

    db.session.commit()
    return jsonify(
        message="Expense added",
        expense_id=expense.id,
        splits=splits_suggestion  
    ), 201

@shared_bp.route('/expense/receipt', methods=['POST'])
def upload_receipt():
    """
    Upload a receipt image and get back the parsed fields from Gemini.
    Expects multipart/form-data: file under 'receipt', plus form fields group_id/paid_by/context.
    """
    image = request.files.get('receipt')
    context = request.form.get('context', '')

    if not image:
        return jsonify(error="Missing receipt file"), 400

    data = image.read()
    result = extract_from_receipt(data, context)
    return jsonify(gemini_output=result), 200

@shared_bp.route('/expense/import-mock', methods=['POST'])
def import_card_history():
    """
    Mock-import a list of card transactions.
    Expects JSON: { transactions: [{description,amount}, ...], group_id, paid_by, context }
    """
    data = request.get_json() or {}
    txns = data.get('transactions', [])
    group_id = data.get('group_id')
    paid_by = data.get('paid_by')
    context = data.get('context', '')

    created = []
    for txn in txns:
        desc = txn.get('description')
        amt = float(txn.get('amount', 0))
        suggestion = split_expense_with_context(desc, amt, [], context)

        if (
            not isinstance(suggestion, dict)
            or any(not isinstance(v, (int, float)) for v in suggestion.values())
        ):
            # no participants => no splits
            suggestion = {}

        exp = SharedExpense(
            group_id=group_id,
            paid_by=paid_by,
            amount=amt,
            description=desc,
            notes=context
        )
        db.session.add(exp)
        db.session.flush()

        for uid, owed in suggestion.items():
            db.session.add(Split(
                expense_id=exp.id,
                user_id=uid,
                amount_owed=round(owed, 2)
            ))

        created.append(desc)

    db.session.commit()
    return jsonify(imported=created), 200

@shared_bp.route('/group/<int:group_id>/history', methods=['GET'])
def get_group_history(group_id):
    """Return all expenses + payments for a group, newest first."""
    expenses = SharedExpense.query \
        .filter_by(group_id=group_id) \
        .order_by(SharedExpense.created_at.desc()) \
        .all()
    expense_list = [{
        "id": e.id,
        "description": e.description,
        "amount": e.amount,
        "paid_by": e.paid_by,
        "notes": e.notes,
        "created_at": e.created_at.isoformat()
    } for e in expenses]

    group = Group.query.get_or_404(group_id)
    uids = [u.id for u in group.members]
    payments = Payment.query \
        .filter(Payment.from_user.in_(uids), Payment.to_user.in_(uids)) \
        .order_by(Payment.created_at.desc()) \
        .all()
    payment_list = [{
        "id": p.id,
        "from_user": p.from_user,
        "to_user": p.to_user,
        "amount": p.amount,
        "status": p.status,
        "created_at": p.created_at.isoformat()
    } for p in payments]

    return jsonify(expenses=expense_list, payments=payment_list), 200

@shared_bp.route('/expense/<int:expense_id>', methods=['DELETE'])
def delete_shared_expense(expense_id):
    """Delete an expense and all its splits."""
    expense = SharedExpense.query.get_or_404(expense_id)
    Split.query.filter_by(expense_id=expense.id).delete()
    db.session.delete(expense)
    db.session.commit()
    return jsonify(message=f"Expense {expense_id} deleted"), 200

@shared_bp.route('/group/<int:group_id>/pay', methods=['POST'])
def record_group_payment(group_id):
    """Record a transfer from one user to another within a group."""
    data = request.get_json() or {}
    frm = data.get('from_user')
    to_user = data.get('to_user')
    amt = data.get('amount')
    status = data.get('status', 'pending')

    if not all([frm, to_user, amt]):
        return jsonify(error="Missing required fields"), 400

    payment = Payment(from_user=frm, to_user=to_user, amount=amt, status=status)
    db.session.add(payment)
    db.session.commit()
    return jsonify(message="Payment recorded"), 201

@shared_bp.route('/group/<int:group_id>/balances', methods=['GET'])
def get_group_balances(group_id):
    """
    Calculate net balances (who owes/is owed) and simplified settlement transactions.
    """
    group = Group.query.get_or_404(group_id)
    net = {}

    for exp in SharedExpense.query.filter_by(group_id=group_id):
        splits = Split.query.filter_by(expense_id=exp.id).all()
        bal = calculate_balances_from_splits(splits, exp.paid_by)
        for uid, v in bal.items():
            net[uid] = net.get(uid, 0) + v

    settlements = minimize_cash_flow(net.copy())
    return jsonify(net_balances=net, simplified_transactions=settlements), 200

@shared_bp.route('/users', methods=['GET'])
def list_users():
    users = User.query.all()
    return jsonify([{"id": u.id, "username": u.username} for u in users]), 200

@shared_bp.route('/groups/<int:group_id>', methods=['DELETE'])
@jwt_required()
def delete_group(group_id):
    user_id = int(get_jwt_identity())
    group = Group.query.get_or_404(group_id)

    # Solo el creador puede eliminar
    if group.created_by != user_id:
        return jsonify(error="Not authorized"), 403

    db.session.delete(group)
    db.session.commit()
    return jsonify(message="Group deleted"), 200