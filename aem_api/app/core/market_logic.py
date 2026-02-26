from typing import Dict

class AutomatedMarketMaker:
    """
    Automated Market Maker (AMM)
    Orchestrates dynamic prices for computational resources based on 
    concurrent demand and base capacity.
    """
    def __init__(self, base_prices: Dict[str, float], capacities: Dict[str, float], k: float = 0.1, omega: float = 0.8):
        self.base_prices = base_prices
        self.capacities = capacities
        self.k = k
        self.omega = omega  # Smoothing factor to avoid high volatility
        self.current_prices = base_prices.copy()
        
    def update_prices(self, usage: Dict[str, float]) -> Dict[str, float]:
        """
        Adjusts price based on usage (U_r) and capacity (L_r).
        Formula: p_{r,t+1} = p_{r,base} * (1 + k * (U_{r,t} / L_r))
        With smoothing for stability: omega * p_current + (1 - omega) * p_target
        """
        for r, p_base in self.base_prices.items():
            u_r = usage.get(r, 0.0)
            l_r = self.capacities.get(r, 1.0) # Avoid division by zero
            
            # Target price based on demand
            p_target = p_base * (1 + self.k * (u_r / l_r))
            
            # Smoothing to prevent violent price swings
            self.current_prices[r] = self.omega * self.current_prices[r] + (1 - self.omega) * p_target
            
        return self.current_prices

    def get_price(self, resource_name: str) -> float:
        return self.current_prices.get(resource_name, self.base_prices.get(resource_name, 1.0))

# Global instance for the microservice
base_prices = {
    "GPT-3.5": 1.0,
    "GPT-4o": 5.0, 
    "Refactor_DevOps_Resource": 10.0
}
capacities = {
    "GPT-3.5": 100.0,
    "GPT-4o": 20.0,
    "Refactor_DevOps_Resource": 5.0
}
amm = AutomatedMarketMaker(base_prices=base_prices, capacities=capacities)

# Dictionary to track cumulative usage in the current cycle for each resource
current_usage = {k: 0.0 for k in base_prices.keys()}

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
    R = T_base * [ alpha(Q) + beta(max((1 - C_real/C_max),0)) + gamma(max(((L_max - L_real)/L_max), 0)) ] - P_fail
    """
    if is_failure:
        return -p_fail
    
    term1 = alpha * q
    term2 = beta * max(1.0 - (c_real / c_max), 0.0) if c_max > 0 else 0
    term3 = gamma * max((l_max - l_real) / l_max, 0.0) if l_max > 0 else 0
    
    reward = t_base * (term1 + term2 + term3)
    return reward
