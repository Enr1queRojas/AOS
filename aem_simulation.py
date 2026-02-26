import math
import random
from typing import TypedDict, Dict, Any, Literal, Annotated
import operator
from langgraph.graph import StateGraph, START, END

# ==========================================
# 1. Definición del Estado de la Simulación
# ==========================================

def merge_dicts(a: dict, b: dict) -> dict:
    """Función reducer para diccionarios."""
    c = a.copy()
    c.update(b)
    return c

def merge_lists(a: list, b: list) -> list:
    """Función reducer para listas."""
    return a + b

class AgenticState(TypedDict):
    """
    Estado del sistema distribuido a lo largo del LangGraph para representar
    a un agente operando en un mercado computacional.
    """
    agent_id: str
    agent_wallet: float
    skill_level: float
    complexity: float
    current_task: Dict[str, Any]
    metrics: Annotated[Dict[str, Any], merge_dicts]
    market_ticker: Dict[str, float] # Se sobrescribe el ticker
    history: Annotated[list[str], merge_lists]


# ==========================================
# 2. Nodo Broker y AMM (Automated Market Maker)
# ==========================================

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

# Instancia global del mercado (singleton para la simulación)
amm = AutomatedMarketMaker(
    base_prices={"GPT-3.5": 0.5, "GPT-4o": 5.0, "Refactor_DevOps_Resource": 15.0},
    capacities={"GPT-3.5": 100.0, "GPT-4o": 10.0, "Refactor_DevOps_Resource": 2.0}
)


# ==========================================
# 3. Nodos del LangGraph
# ==========================================

def operative_node(state: AgenticState) -> AgenticState:
    """
    Nodo Operativo (El Agente):
    Elige qué LLM/Recurso utilizar basándose en una política Softmax 
    que evalúa la Utilidad Esperada (E[R] - Precio).
    """
    tau = 2.0 # Temperatura paramétrica para el softmax
    ticker = state.get("market_ticker", amm.base_prices)
    
    # Expectativas heurísticas del agente (cuánto cree que ganará usando X recurso)
    # Refactor_DevOps_Resource tiene una alta utilidad subjetiva por sus beneficios a largo plazo,
    # aunque sea caro a corto plazo.
    expected_rewards = {
        "GPT-3.5": 5.0,
        "GPT-4o": 15.0, 
        "Refactor_DevOps_Resource": 20.0
    }
    
    utilities = {}
    for r, expected_r in expected_rewards.items():
        price_r = ticker.get(r, 0.0)
        u_r = expected_r - price_r
        utilities[r] = u_r
        
    # Selección de política Softmax
    max_u = max(utilities.values()) # Estabilidad numérica
    exp_u = {r: math.exp((u - max_u) / tau) for r, u in utilities.items()}
    sum_exp = sum(exp_u.values())
    probs = {r: e / sum_exp for r, e in exp_u.items()}
    
    rand_val = random.random()
    cumulative = 0.0
    chosen_resource = "GPT-3.5"
    for r, p in probs.items():
        cumulative += p
        if rand_val <= cumulative:
            chosen_resource = r
            break
            
    # Ejecuta tarea simulada y registra consumo real (Tokens y Latencia)
    cost_paid = ticker.get(chosen_resource, 1.0)
    
    if chosen_resource == "GPT-3.5":
        c_real = random.uniform(1.0, 3.0)
        l_real = random.uniform(0.5, 1.5)
    elif chosen_resource == "GPT-4o":
        c_real = random.uniform(5.0, 10.0)
        l_real = random.uniform(1.0, 3.0)
    else: # Refactor_DevOps_Resource
        c_real = random.uniform(15.0, 20.0) # Alto consumo
        l_real = random.uniform(3.0, 6.0)   # Alta latencia
        
    metrics_update = {
        "C_real": c_real,
        "L_real": l_real,
        "chosen_resource": chosen_resource,
        "cost_paid": cost_paid
    }
    
    return {
        "metrics": metrics_update, 
        "history": [f"Operativo: Eligió {chosen_resource} (Coste pagado: {cost_paid:.2f})"]
    }

def evaluator_node(state: AgenticState) -> AgenticState:
    """
    Nodo Evaluador (Oráculo / Dataset de Oro):
    Calcula la calidad de la respuesta (Q) y aplica la función de fallo.
    Luego recompensa al agente.
    """
    metrics = state["metrics"]
    chosen_resource = metrics.get("chosen_resource", "GPT-3.5")
    
    # 1. Función de Calidad (Q) en [0, 1]
    # Modificado por la skill del agente, la complejidad de la tarea y el LLM
    resource_multiplier = 1.2 if chosen_resource == "GPT-4o" else 1.0
    q_base = (state["skill_level"] / (state["complexity"] + 0.1)) * resource_multiplier
    q = min(max(q_base + random.uniform(-0.1, 0.1), 0.0), 1.0)
    
    # 2. Función de Falla (Golden Dataset)
    # Probabilidad de fallar aumenta con la complejidad de la tarea y la alta latencia
    l_real = metrics.get("L_real", 1.0)
    fail_prob = min((state["complexity"] * 0.1) + (l_real * 0.05), 0.9)
    # Reducir chance de fallo si se usa recurso potente
    if chosen_resource == "GPT-4o":
        fail_prob *= 0.5 
        
    is_failure = random.random() < fail_prob
    
    # 3. Cálculo de Recompensa Ecuación AEM
    t_base = 25.0  # Recompensa base
    alpha, beta, gamma = 0.5, 0.3, 0.2
    c_real = metrics.get("C_real", 1.0)
    c_max = 20.0
    l_max = 6.0
    
    p_fail = 15.0 if is_failure else 0.0
    
    reward = t_base * (
        alpha * q + 
        beta * max(1.0 - (c_real / c_max), 0.0) + 
        gamma * max((l_max - l_real) / l_max, 0.0)
    ) - p_fail
    
    # Descuenta el costo del recurso que el agente decidió usar del wallet
    cost_paid = metrics.get("cost_paid", 0.0)
    net_profit = reward - cost_paid
    new_wallet = state["agent_wallet"] + net_profit
    
    result_str = "FALLÓ" if is_failure else "ÉXITO"
    history_entry = f"Evaluador: Tarea {result_str}. Q={q:.2f}, R={reward:.2f}, Beneficio Neto={net_profit:.2f}, Wallet={new_wallet:.2f}"
    
    return {
        "agent_wallet": new_wallet,
        "metrics": {"Q": q, "is_failure": is_failure, "reward": reward, "net_profit": net_profit},
        "history": [history_entry]
    }

def broker_node(state: AgenticState) -> AgenticState:
    """
    Nodo Broker:
    Simula la liquidez y demanda del mercado afectando el Automated Market Maker (AMM).
    """
    chosen = state["metrics"].get("chosen_resource")
    
    # Simula el uso base del mercado para dar ruido orgánico a la demanda
    market_usage = {r: random.uniform(0.0, cap * 0.5) for r, cap in amm.capacities.items()}
    
    # Se agrega el impacto de la decisión particular de nuestro agente
    if chosen in market_usage:
        market_usage[chosen] += 1.0 
        
    # Actualiza los precios
    new_ticker = amm.update_prices(market_usage)
    
    # Copiamos profundamente el dict para LangGraph
    return {
        "market_ticker": new_ticker.copy(),
        "history": [f"Broker: Precios actualizados. {chosen} = {new_ticker.get(chosen, 0.0):.2f}"]
    }

def devops_node(state: AgenticState) -> AgenticState:
    """
    Nodo DevOps (Recurso C - Refactorización):
    Premia al agente que eligió y pudo pagar el recurso más alto. 
    Altera su Equilibrio de Markov bajándole permanentemente la `complexity`
    y subiéndole su `skill_level`.
    """
    wallet = state.get("agent_wallet", 0.0)
    if wallet >= 10.0:  # Si tiene solvencia despues del intento de refactor
        return {
            "complexity": max(state["complexity"] - 1.5, 1.0), 
            "skill_level": state["skill_level"] + 1.0,
            "agent_wallet": wallet - 10.0,  # "Impuesto" extra por deploy
            "history": ["DevOps: !Refactorización Exitosa! Complexity reducida, Skill aumentada."]
        }
    return {"history": ["DevOps: Intentó refactorizar pero wallet insuficiente tras costo operativo."]}

def bankruptcy_node(state: AgenticState) -> AgenticState:
    """Nodo final cuando un agente quiebra por falta de fondos."""
    return {"history": ["Bancarrota: El agente se quedó sin fondos y ha sido liquidado del mercado."]}


# ==========================================
# 4. Enrutamiento Condicional
# ==========================================

def router_broker_or_devops(state: AgenticState) -> Literal["bancarrota", "devops", "broker"]:
    """
    Enrutador Post-Evaluación:
    - 'bancarrota': Si el wallet del agente es menor o igual a 0.
    - 'devops': Si eligió la refactorización profunda (Resource C).
    - 'broker': Flujo normal hacia el AMM para ajustar el mercado.
    """
    wallet = state.get("agent_wallet", 0.0)
    chosen_resource = state["metrics"].get("chosen_resource", "")
    
    if wallet <= 0.0:
        return "bancarrota"
        
    if chosen_resource == "Refactor_DevOps_Resource":
        return "devops"
        
    return "broker"

def router_continue(state: AgenticState) -> Literal["siguiente_tarea", "fin"]:
    """Decide si ejecuta una siguiente iteración simulada o termina la simulación."""
    # Para la prueba corremos el grafo 5 veces, medido por longitud de history o un counter
    # Usaremos una heurística de longitud de historia para parar la simulación infinita
    task_count = len([h for h in state.get("history", []) if h.startswith("Evaluador:")])
    if task_count >= 5: # Termina después de simular 5 tareas
        return "fin"
    return "siguiente_tarea"


# ==========================================
# 5. Configuración del LangGraph StateGraph
# ==========================================

def build_aem_graph() -> StateGraph:
    graph = StateGraph(AgenticState)
    
    # Añadiendo nodos
    graph.add_node("operative", operative_node)
    graph.add_node("evaluator", evaluator_node)
    graph.add_node("broker", broker_node)
    graph.add_node("devops", devops_node)
    graph.add_node("bankruptcy", bankruptcy_node)
    
    # Flujo general: Start -> Operative -> Evaluator -> Router -> (Broker/DevOps/Bankruptcy)
    graph.add_edge(START, "operative")
    graph.add_edge("operative", "evaluator")
    
    # Enrutamiento basado en billetera y performance post-evaluador
    graph.add_conditional_edges(
        "evaluator",
        router_broker_or_devops,
        {
            "bancarrota": "bankruptcy",
            "devops": "devops",
            "broker": "broker"
        }
    )
    
    # La bancarrota conduce al final del ciclo de vida del agente
    graph.add_edge("bankruptcy", END)
    
    # DevOps redirige siempre al broker para actualizar mercado antes de seguir
    graph.add_edge("devops", "broker")
    
    # El broker decide si hacer la siguiente tarea o terminar la simulación
    graph.add_conditional_edges(
        "broker",
        router_continue,
        {
            "siguiente_tarea": "operative",
            "fin": END
        }
    )
    
    return graph.compile()

# ==========================================
# 6. Ejecución Local de Prueba (Sandbox)
# ==========================================

if __name__ == "__main__":
    initial_state = AgenticState(
        agent_id="Agent_007",
        agent_wallet=35.0, # Fondos iniciales moderados
        skill_level=3.0,
        complexity=5.0, # Tarea relativamente compleja inicial
        current_task={"type": "presupuesto_concierge", "data": "Extraer variables financieras"},
        metrics={},
        market_ticker=amm.base_prices.copy(),
        history=["Inicio: Agente instanciado en el mercado."]
    )

    app = build_aem_graph()
    
    print("🚀 Iniciando Simulación AEM (Agentic Economic Market)...")
    print("-" * 50)
    
    # Ejecuta el grafo de forma síncrona
    final_state = app.invoke(initial_state)
    
    print("\n📈 Historial de Transacciones y Tareas:")
    for h in final_state["history"]:
        print(f" -> {h}")
        
    print("-" * 50)
    print("\n🏦 Estado Final:")
    print(f"Wallet: {final_state['agent_wallet']:.2f} Tk")
    print(f"Skill Final: {final_state['skill_level']:.2f}")
    print(f"Complexity Restante: {final_state['complexity']:.2f}")
    print(f"Precios Finales AMM:")
    for res, price in final_state['market_ticker'].items():
        print(f" - {res}: {price:.4f}")
