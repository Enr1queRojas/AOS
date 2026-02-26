class AutomatedMarketMaker:
    def __init__(self):
        # Initial dummy values for dynamic market prices
        self.prices = {
            "api_call": 1.5,
            "database_query": 0.5,
            "compute_cycle": 2.0
        }
        self.demands = {
            "api_call": 100.0,
            "database_query": 50.0,
            "compute_cycle": 200.0
        }

    def get_prices(self):
        return [
            {
                "resource_name": res,
                "dynamic_price": price,
                "market_demand": self.demands[res]
            }
            for res, price in self.prices.items()
        ]

    def get_price(self, resource_name: str) -> float:
        return self.prices.get(resource_name, 1.0)


def calculate_reward(
    t_base: float,
    alpha: float,
    beta: float,
    gamma: float,
    q: float,
    c_real: float,
    c_max: float,
    l_real: float,
    l_max: float,
    p_fail: float,
    is_failure: bool
) -> float:
    """
    R = T_base * [ alpha(Q) + beta(1 - C_real/C_max) + gamma((L_max - L_real)/L_max) ] - P_fail
    """
    if is_failure:
        return -p_fail
        
    term1 = alpha * q
    term2 = beta * (1 - c_real / c_max) if c_max > 0 else 0
    term3 = gamma * ((l_max - l_real) / l_max) if l_max > 0 else 0
    
    reward = t_base * (term1 + term2 + term3)
    return reward
