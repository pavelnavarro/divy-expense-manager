from flask import Blueprint, request, jsonify
from backend.models.shared import Group, SharedExpense, Split, Payment
from backend.utils.split_logic import calculate_balances_from_splits, minimize_cash_flow,filter_members
from backend.utils.gemini_utils import split_expense_with_context,extract_from_receipt
from backend.extensions import db

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
        
    db.session.commit()  # Saves to DB

    return jsonify({"message": "Expense added", "expense_id": expense.id}), 201 

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

@shared_bp.route('/shared/<int:group_id>/balances', methods=['GET'])
def get_group_balances(group_id):
    group = Group.query.get_or_404(group_id)

    # Get all expenses in the group
    expenses = SharedExpense.query.filter_by(group_id=group_id).all()

    # Initialize balances dictionary
    net_balances = {}

    for expense in expenses:
        splits = Split.query.filter_by(expense_id=expense.id).all()
        balances = calculate_balances_from_splits(splits, expense.paid_by)

        # Accumulate each user's balance
        for uid, value in balances.items():
            net_balances[uid] = net_balances.get(uid, 0) + value

    # Optional: Return a simplified transaction list using greedy algo
    simplified_transactions = minimize_cash_flow(net_balances.copy())

    return jsonify({
        "net_balances": net_balances,
        "simplified_transactions": simplified_transactions
    })

@shared_bp.route('/shared/group/create', methods=['POST'])
def create_group():
    data = request.json
    group_name = data.get('name')
    member_ids = data.get('members', [])  # list of user IDs
    created_by = data.get('created_by')   # user ID

    if not group_name or not created_by:
        return jsonify({"error": "Missing group name or creator"}), 400

    # Create the group
    group = Group(name=group_name, created_by=created_by)

    # Add members (User objects)
    from backend.models.user import User
    users = User.query.filter(User.id.in_(member_ids)).all()
    group.members.extend(users)

    db.session.add(group)
    db.session.commit()

    return jsonify({
        "message": "Group created successfully",
        "group_id": group.id,
        "members": [user.id for user in users]
    }), 201

@shared_bp.route('/shared/groups/<int:user_id>', methods=['GET'])
def get_user_groups(user_id):
    from backend.models.user import User
    user = User.query.get_or_404(user_id)

    groups = user.groups.all()  # Because of lazy='dynamic' in the relationship

    result = []
    for group in groups:
        result.append({
            "group_id": group.id,
            "group_name": group.name,
            "created_by": group.created_by,
            "created_at": group.created_at.isoformat()
        })

    return jsonify({"groups": result})

@shared_bp.route('/shared/<int:group_id>/balances', methods=['GET'])
def get_group_balances(group_id):
    group = Group.query.get_or_404(group_id)
    members = [user.id for user in group.members]

    # Aggregate unpaid splits
    all_splits = Split.query.join(SharedExpense).filter(
        SharedExpense.group_id == group_id,
        Split.is_paid == False
    ).all()

    # Group splits by expense
    expense_splits_map = {}
    for split in all_splits:
        expense_splits_map.setdefault(split.expense_id, []).append(split)

    # Calculate net balances
    net_balances = {}
    for expense_id, splits in expense_splits_map.items():
        expense = SharedExpense.query.get(expense_id)
        balances = calculate_balances_from_splits(splits, expense.paid_by)
        for user_id, amount in balances.items():
            net_balances[user_id] = net_balances.get(user_id, 0) + amount

    # Convert user_id → username (optional, for frontend clarity)
    from backend.models.user import User
    id_to_name = {user.id: user.username for user in User.query.filter(User.id.in_(net_balances))}

    # Human-readable balances
    readable_balances = {id_to_name[uid]: round(amt, 2) for uid, amt in net_balances.items()}

    # Minimize transactions
    transactions = minimize_cash_flow({id_to_name[k]: v for k, v in net_balances.items()})

    return jsonify({
        "balances": readable_balances,
        "settlements": transactions
    })

@shared_bp.route('/shared/group/create', methods=['POST'])
def create_group():
    data = request.json
    name = data.get('name')
    created_by = data.get('created_by')  # user ID
    member_ids = data.get('members', [])

    if not name or not created_by:
        return jsonify({"error": "Missing group name or creator ID"}), 400

    # Create group
    group = Group(name=name, created_by=created_by)
    db.session.add(group)
    db.session.flush()  # get group.id before committing

    # Add members
    from backend.models.user import User
    users = User.query.filter(User.id.in_(member_ids)).all()
    for user in users:
        group.members.append(user)

    db.session.commit()
    return jsonify({
        "message": "Group created",
        "group_id": group.id,
        "name": group.name,
        "members": [user.username for user in group.members]
    })

@shared_bp.route('/shared/group/<int:group_id>', methods=['GET'])
def get_group_info(group_id):
    group = Group.query.get_or_404(group_id)
    return jsonify({
        "id": group.id,
        "name": group.name,
        "created_by": group.created_by,
        "members": [{"id": u.id, "username": u.username} for u in group.members]
    })

