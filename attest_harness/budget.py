class BudgetExceeded(RuntimeError): ...

class Budget:
    def __init__(self, cap_usd: float):
        self.cap = cap_usd; self.spent = 0.0
    def charge(self, in_tokens: int, out_tokens: int, usd_in_1k: float, usd_out_1k: float) -> float:
        cost = in_tokens / 1000 * usd_in_1k + out_tokens / 1000 * usd_out_1k
        if self.spent + cost > self.cap:
            raise BudgetExceeded(f"spent {self.spent:.2f} + {cost:.2f} > cap {self.cap:.2f}")
        self.spent += cost
        return cost
