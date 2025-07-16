# backend/utils/split_logic.py

from typing import List, Dict, Any
from backend.models.shared import Split

def filter_members(members: List[int], excluded_members: List[int]) -> List[int]:
    """
    Remove any excluded IDs from the full member list.

    Args:
        members: List of all participant user IDs.
        excluded_members: List of user IDs to exclude.

    Returns:
        A new list containing only those IDs in `members` that are not in `excluded_members`.
    """
    return [m for m in members if m not in excluded_members]


def calculate_balances_from_splits(
    splits: List[Split],
    paid_by_id: int
) -> Dict[int, float]:
    """
    Given a list of Split rows for one expense, compute each user's net position.

    Negative = owes money, Positive = is owed money.

    Args:
      splits: Iterable of Split model instances (each has .user_id and .amount_owed).
      paid_by_id: The user_id who actually paid the bill.

    Returns:
      A dict mapping user_id → net balance.
    """
    balances: Dict[int, float] = {}
    total = 0.0

    # Each split is what someone owes
    for s in splits:
        balances[s.user_id] = balances.get(s.user_id, 0.0) - s.amount_owed
        total += s.amount_owed

    # The payer is “owed” the sum of all splits
    balances[paid_by_id] = balances.get(paid_by_id, 0.0) + total
    return balances


def minimize_cash_flow(balances: Dict[Any, float]) -> List[Dict[str, Any]]:
    """
    Given net balances for a group (negative = owes, positive = is owed),
    produce a minimal set of settlement transactions.

    Uses a greedy algorithm: match the largest debtor with the largest creditor.

    Args:
      balances: Dict of {participant → net balance}.

    Returns:
      List of {"from": debtor, "to": creditor, "amount": X} to settle all debts.
    """
    # Work on a mutable copy
    bal = {user: round(amount, 2) for user, amount in balances.items()}
    settlements: List[Dict[str, Any]] = []

    def biggest_creditor():
        return max(bal, key=lambda u: bal[u])

    def biggest_debtor():
        return min(bal, key=lambda u: bal[u])

    while True:
        creditor = biggest_creditor()
        debtor   = biggest_debtor()
        credit   = bal[creditor]
        debt     = -bal[debtor]

        # If outstanding balances are effectively zero, we’re done
        if credit < 1e-6 or debt < 1e-6:
            break

        amount = min(credit, debt)
        bal[creditor] = round(bal[creditor] - amount, 2)
        bal[debtor]   = round(bal[debtor]   + amount, 2)

        settlements.append({
            "from": debtor,
            "to": creditor,
            "amount": round(amount, 2)
        })

    return settlements
