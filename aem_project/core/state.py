import math
import random
from typing import TypedDict, Dict, Any, Literal, Annotated
import operator

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
