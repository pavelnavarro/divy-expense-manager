from collections import namedtuple
from backend.utils.split_logic import filter_members, calculate_balances_from_splits, minimize_cash_flow

Dummy = namedtuple("Dummy", ["user_id", "amount_owed"])

def test_filter_members():
    assert filter_members([1,2,3], [2]) == [1,3]

def test_calculate_balances_from_splits():
    splits = [Dummy(user_id=1, amount_owed=10), Dummy(user_id=2, amount_owed=20)]
    bal = calculate_balances_from_splits(splits, paid_by_id=3)
    # 1 owes 10, 2 owes 20, 3 is owed 30
    assert bal == {1: -10, 2: -20, 3: 30}

def test_minimize_cash_flow_simple():
    net = {1: -15, 2: 5, 3: 10}
    txns = minimize_cash_flow(net.copy())
    # Should settle 1→3 $10 and 1→2 $5 (order may vary)
    assert {"from": 1, "to": 3, "amount": 10} in txns
    assert {"from": 1, "to": 2, "amount": 5} in txns
