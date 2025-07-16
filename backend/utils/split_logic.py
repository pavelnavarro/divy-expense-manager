def minimize_cash_flow(balances: dict):
    """
    Takes a dict of net balances like:
    {'Pavel': -30, 'Daniel': 20, 'Alexis': 10}
    Returns a list of settlements to minimize transactions:
    [{'from': 'Pavel', 'to': 'Daniel', 'amount': 20}, ...]
    """
    transactions = []
    people = list(balances.keys())

    def get_max_credit():
        return max(people, key=lambda x: balances[x])

    def get_max_debit():
        return min(people, key=lambda x: balances[x])

    while True:
        max_credit = get_max_credit()
        max_debit = get_max_debit()

        if abs(balances[max_debit]) < 1e-2:
            break  # All settled

        settled_amount = min(-balances[max_debit], balances[max_credit])
        balances[max_credit] -= settled_amount
        balances[max_debit] += settled_amount

        transactions.append({
            "from": max_debit,
            "to": max_credit,
            "amount": round(settled_amount, 2)
        })

    return transactions

def calculate_balances_from_splits(splits, paid_by_id):
    """
    Given a list of Split entries for an expense, return each user's net balance.
    Negative = owes, Positive = is owed
    """
    balances = {}
    total = 0

    for split in splits:
        balances[split.user_id] = balances.get(split.user_id, 0) - split.amount_owed
        total += split.amount_owed

    balances[paid_by_id] = balances.get(paid_by_id, 0) + total
    return balances

def filter_members(members, excluded_members):
    """
    Returns a list of members excluding those who opted out.

    Args:
        members (list): List of all user IDs or usernames.
        excluded_members (list): Subset to exclude.

    Returns:
        list: Filtered list.
    """
    return [member for member in members if member not in excluded_members]

