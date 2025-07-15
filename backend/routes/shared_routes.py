from flask import Blueprint, request, jsonify
from backend.models.shared import Group, SharedExpense, Split, Payment
from backend.utils.split_logic import calculate_balances_from_splits, minimize_cash_flow,filter_members
from backend.utils.gemini_utils import split_expense_with_context,extract_from_receipt
from backend.app import db

shared_bp = Blueprint('shared', __name__)

@shared_bp.route('/shared/add', methods=['POST'])
def add_shared_expense():
    # logic to receive request data, process, save to DB
    data = request.json
    description = data.get('description')
    amount = float(data.get('amount'))
    group_id = int(data.get('group_id'))
    paid_by_id = int(data.get('paid_by'))  # user ID of payer
    excluded_members = data.get('excluded_members', [])
    context_note = data.get('context', '')

    group = Group.query.get(group_id)
    members = [user.id for user in group.members]
    included_members = filter_members(members, excluded_members)

    split_result = split_expense_with_context(description, amount, included_members, context_note)

    expense = SharedExpense(
    group_id=group_id,
    paid_by=paid_by_id,
    amount=amount,
    description=description
    )
    db.session.add(expense)
    db.session.flush()

    share = round(amount / len(included_members), 2)
    for uid, owed in split_result.items():
        split = Split(
            expense_id=expense.id,
            user_id=uid,
            amount_owed=round(owed, 2),
            is_paid=(uid == paid_by_id)
        )
        db.session.add(split)

@shared_bp.route('/shared/upload-receipt', methods=['POST'])
def upload_receipt():
    image = request.files['receipt']
    group_id = request.form.get('group_id')
    paid_by = request.form.get('paid_by')
    context_note = request.form.get('context', '')

    # Read image data
    image_data = image.read()

    # Gemini parses image
    gemini_result = extract_from_receipt(image_data, context_note)

    # Use Gemini result to extract fields (maybe parse text?)
    # Example output: vendor, total amount, category
    # For now, you can treat `gemini_result` as a string (or JSON if formatted)

    return jsonify({"gemini_output": gemini_result})

@shared_bp.route('/shared/import-card-history', methods=['POST'])
def import_mock_card_data():
    # Simulate a list of transactions (normally pulled from Plaid)
    transactions = request.json.get('transactions', [])
    group_id = request.json.get('group_id')
    paid_by = request.json.get('paid_by')
    context_note = request.json.get('context', '')

    created = []

    for txn in transactions:
        description = txn['description']
        amount = txn['amount']

        # Optional: call categorize_expense_text() or split_expense_with_context()
        split_result = split_expense_with_context(description, amount, [], context_note)

        expense = SharedExpense(
            group_id=group_id,
            paid_by=paid_by,
            amount=amount,
            description=description,
            notes=context_note
        )
        db.session.add(expense)
        db.session.flush()

        for uid, owed in split_result.items():
            split = Split(
                expense_id=expense.id,
                user_id=uid,
                amount_owed=owed
            )
            db.session.add(split)
        created.append(description)

    db.session.commit()
    return jsonify({"imported": created})

@shared_bp.route('/shared/<int:group_id>/history', methods=['GET'])
def get_group_history(group_id):
    expenses = SharedExpense.query.filter_by(group_id=group_id).order_by(SharedExpense.created_at.desc()).all()
    
    expense_list = [{
        "id": e.id,
        "description": e.description,
        "amount": e.amount,
        "paid_by": e.paid_by,
        "category": e.category,
        "notes": e.notes,
        "created_at": e.created_at.isoformat()
    } for e in expenses]

    # Payments are not tied directly to group, but you can filter by user IDs in the group
    group = Group.query.get_or_404(group_id)
    user_ids = [user.id for user in group.members]

    payments = Payment.query.filter(
        Payment.from_user.in_(user_ids),
        Payment.to_user.in_(user_ids)
    ).order_by(Payment.created_at.desc()).all()

    payment_list = [{
        "id": p.id,
        "from_user": p.from_user,
        "to_user": p.to_user,
        "amount": p.amount,
        "status": p.status,
        "created_at": p.created_at.isoformat()
    } for p in payments]

    return jsonify({
        "expenses": expense_list,
        "payments": payment_list
    })

@shared_bp.route('/shared/<int:expense_id>/delete', methods=['DELETE'])
def delete_shared_expense(expense_id):
    expense = SharedExpense.query.get_or_404(expense_id)

    # Delete all related splits first
    Split.query.filter_by(expense_id=expense.id).delete()

    # Then delete the expense
    db.session.delete(expense)
    db.session.commit()

    return jsonify({"message": f"Expense {expense_id} deleted successfully"})


@shared_bp.route('/shared/<int:group_id>/pay', methods=['POST'])
def record_group_payment(group_id):
    data = request.json
    from_user = data.get('from_user')
    to_user = data.get('to_user')
    amount = data.get('amount')
    status = data.get('status', 'pending')

    if not all([from_user, to_user, amount]):
        return jsonify({"error": "Missing required fields"}), 400

    payment = Payment(
        from_user=from_user,
        to_user=to_user,
        amount=amount,
        status=status
    )

    db.session.add(payment)
    db.session.commit()

    return jsonify({"message": "Payment recorded successfully"})