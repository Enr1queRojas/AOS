from typing import Literal
from core.state import AgenticState

def router_broker_or_devops(state: AgenticState) -> Literal["bancarrota", "devops", "broker"]:
    """
    Post-Evaluation Router:
    - 'bancarrota': If wallet <= 0.
    - 'devops': If deep refactoring (Resource C) was chosen.
    - 'broker': Normal flow to AMM.
    """
    wallet = state.get("agent_wallet", 0.0)
    chosen_resource = state["metrics"].get("chosen_resource", "")
    
    if wallet <= 0.0:
        return "bancarrota"
        
    if chosen_resource == "Refactor_DevOps_Resource":
        return "devops"
        
    return "broker"

def router_continue(state: AgenticState) -> Literal["siguiente_tarea", "fin"]:
    """Decides whether to execute the next simulated iteration or end."""
    # We now check for 'Evaluador (API)' instead of 'Evaluador:'
    task_count = len([h for h in state.get("history", []) if h.startswith("Evaluador (API)")])
    
    if task_count >= 5: # Ends after simulating 5 tasks
        return "fin"
    return "siguiente_tarea"
