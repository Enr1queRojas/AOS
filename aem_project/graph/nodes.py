import random
import math
import requests
from typing import Dict, Any
from core.state import AgenticState

API_BASE_URL = "http://localhost:8000/api/v1"

def get_operative_node(amm=None):
    def operative_node(state: AgenticState) -> AgenticState:
        """
        Nodo Operativo (Cliente HTTP):
        Obtiene precios del AEM Central Server y elige recurso con Softmax.
        """
        tau = 2.0
        try:
            resp = requests.get(f"{API_BASE_URL}/market/ticker", timeout=5)
            ticker = resp.json() if resp.status_code == 200 else {}
        except Exception:
            ticker = {"GPT-3.5": 1.0, "GPT-4o": 5.0, "Refactor_DevOps_Resource": 10.0}
            
        expected_rewards = {
            "GPT-3.5": 5.0,
            "GPT-4o": 15.0, 
            "Refactor_DevOps_Resource": 20.0
        }
        
        utilities = {}
        for r, expected_r in expected_rewards.items():
            price_r = ticker.get(r, 0.0)
            utilities[r] = expected_r - price_r
            
        max_u = max(utilities.values()) if utilities else 0
        exp_u = {r: math.exp((u - max_u) / tau) for r, u in utilities.items()}
        sum_exp = sum(exp_u.values()) if exp_u else 1
        probs = {r: e / sum_exp for r, e in exp_u.items()}
        
        rand_val = random.random()
        cumulative = 0.0
        chosen_resource = "GPT-3.5"
        for r, p in probs.items():
            cumulative += p
            if rand_val <= cumulative:
                chosen_resource = r
                break
                
        cost_paid = ticker.get(chosen_resource, 1.0)
        
        if chosen_resource == "GPT-3.5":
            c_real = random.uniform(1.0, 3.0)
            l_real = random.uniform(0.5, 1.5)
        elif chosen_resource == "GPT-4o":
            c_real = random.uniform(5.0, 10.0)
            l_real = random.uniform(1.0, 3.0)
        else:
            c_real = random.uniform(15.0, 20.0)
            l_real = random.uniform(3.0, 6.0)
            
        metrics_update = {
            "C_real": c_real,
            "L_real": l_real,
            "chosen_resource": chosen_resource,
            "cost_paid": cost_paid
        }
        
        return {
            "metrics": metrics_update, 
            "market_ticker": ticker,
            "history": [f"Operativo (API): Eligió {chosen_resource} (Precio Ticker: {cost_paid:.2f})"]
        }
    return operative_node


def get_evaluator_node(SessionLocal=None):
    def evaluator_node(state: AgenticState) -> Dict[str, Any]:
        """
        Nodo Evaluador (Cliente HTTP):
        Evalúa Q(calidad) localmente y envía liquidación al AEM Central Server.
        """
        metrics = state["metrics"]
        chosen_resource = metrics.get("chosen_resource", "GPT-3.5")
        agent_id = state.get("agent_id", "Agent_007")
        
        # Calcular Q y Fallo (Lógica local simulada de interacción)
        resource_multiplier = 1.2 if chosen_resource == "GPT-4o" else 1.0
        q_base = (state["skill_level"] / (state["complexity"] + 0.1)) * resource_multiplier
        q = min(max(q_base + random.uniform(-0.1, 0.1), 0.0), 1.0)
        
        l_real = metrics.get("L_real", 1.0)
        c_real = metrics.get("C_real", 1.0)
        
        fail_prob = min((state["complexity"] * 0.1) + (l_real * 0.05), 0.9)
        if chosen_resource == "GPT-4o":
            fail_prob *= 0.5 
            
        is_failure = random.random() < fail_prob
        
        # Payload de Liquidación al Servidor Central
        payload = {
            "resource_used": chosen_resource,
            "c_real": c_real,
            "l_real": l_real,
            "task_quality_q": q,
            "is_failure": is_failure
        }
        
        try:
            resp = requests.post(f"{API_BASE_URL}/agents/{agent_id}/settle", json=payload, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                new_wallet = data.get("wallet_balance", state["agent_wallet"])
                reward = data.get("reward", 0.0)
                net_profit = data.get("net_profit", 0.0)
            else:
                new_wallet = state["agent_wallet"]
                reward = 0.0
                net_profit = 0.0
        except Exception:
            new_wallet = state["agent_wallet"]
            reward = 0.0
            net_profit = 0.0
            
        result_str = "FALLO" if is_failure else "EXITO"
        history_entry = f"Evaluador (API): Tarea {result_str}. Q={q:.2f}. Resp API -> Wallet={new_wallet:.2f}, Beneficio={net_profit:.2f}"
        
        return {
            "agent_wallet": new_wallet,
            "metrics": {"Q": q, "is_failure": is_failure, "reward": reward, "net_profit": net_profit},
            "history": [history_entry]
        }
    return evaluator_node


def get_broker_node(amm=None, SessionLocal=None):
    def broker_node(state: AgenticState) -> Dict[str, Any]:
        """
        Nodo Broker Deprecado: Actúa de pasarela. El mercado se actualiza en el server con su propio update_prices.
        """
        return {
            "history": ["Broker: Omitido. El mercado operado centralmente en la AEM API."]
        }
    return broker_node


def get_devops_node(SessionLocal=None):
    def devops_node(state: AgenticState) -> Dict[str, Any]:
        """
        Nodo DevOps (Cliente HTTP): Pide un refactor a la API.
        """
        agent_id = state.get("agent_id", "Agent_007")
        try:
            resp = requests.post(
                f"{API_BASE_URL}/devops/refactor", 
                json={"agent_id": agent_id},
                timeout=5
            )
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "complexity": data.get("new_complexity", state["complexity"]),
                    "skill_level": data.get("new_skill_level", state["skill_level"]),
                    "agent_wallet": data.get("wallet_balance", state.get("agent_wallet")),
                    "history": ["DevOps (API): !Refactorización Exitosa delegada al servidor!"]
                }
            else:
                 return {"history": [f"DevOps (API): Fallo al refactorizar - HTTP {resp.status_code}"]}
        except Exception as e:
            return {"history": [f"DevOps (API): Error de conexion - {e}"]}
    return devops_node


def bankruptcy_node(state: AgenticState) -> Dict[str, Any]:
    """Nodo final cuando un agente quiebra por falta de fondos."""
    return {"history": ["Bancarrota: El agente se quedó sin fondos y ha sido liquidado del mercado."]}
