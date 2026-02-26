from typing import Literal
from core.state import AgenticState

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
    task_count = len([h for h in state.get("history", []) if h.startswith("Evaluador:")])
    if task_count >= 5: # Termina después de simular 5 tareas
        return "fin"
    return "siguiente_tarea"
