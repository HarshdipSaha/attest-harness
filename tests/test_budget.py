import pytest
from attest_harness.budget import Budget, BudgetExceeded

def test_budget_accumulates_and_raises():
    b = Budget(cap_usd=1.0)
    b.charge(in_tokens=100_000, out_tokens=0, usd_in_1k=0.005, usd_out_1k=0.0)  # $0.50
    assert abs(b.spent - 0.5) < 1e-9
    with pytest.raises(BudgetExceeded):
        b.charge(200_000, 0, 0.005, 0.0)  # would be $1.50
