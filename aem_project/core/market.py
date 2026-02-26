from typing import Dict

class AutomatedMarketMaker:
    """
    Automated Market Maker (AMM)
    Orquesta los precios dinámicos de los recursos computacionales basados en
    demanda concurrente y disponibilidad base.
    """
    def __init__(self, base_prices: Dict[str, float], capacities: Dict[str, float], k: float = 0.1, omega: float = 0.8):
        self.base_prices = base_prices
        self.capacities = capacities
        self.k = k
        self.omega = omega  # Smoothing factor to avoid high volatility
        self.current_prices = base_prices.copy()
        
    def update_prices(self, usage: Dict[str, float]) -> Dict[str, float]:
        """
        Ajusta el precio basándose en el uso (U_r) y la capacidad (L_r).
        Formula: p_{r,t+1} = p_{r,base} * (1 + k * (U_{r,t} / L_r))
        Con un smoothing para estabilidad: omega * p_current + (1 - omega) * p_target
        """
        for r, p_base in self.base_prices.items():
            u_r = usage.get(r, 0.0)
            l_r = self.capacities.get(r, 1.0) # Evita división por 0
            
            # Precio objetivo según demanda
            p_target = p_base * (1 + self.k * (u_r / l_r))
            
            # Suavizado para evitar oscilaciones violentas
            self.current_prices[r] = self.omega * self.current_prices[r] + (1 - self.omega) * p_target
            
        return self.current_prices
