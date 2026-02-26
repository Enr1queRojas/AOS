import sys
import os
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Dict, Any

# Añadir ruta para importar módulos de aem_project
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from aem_project.core.market import AutomatedMarketMaker
from aem_project.db.database import engine, SessionLocal
from aem_project.db import models

# Inicializar Base de Datos
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="AEM Central Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializar Mercado (In-memory para demostración o stateful module)
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
# Diccionario para trackear uso acumulado en este ciclo para cada recurso
current_usage = {k: 0.0 for k in base_prices.keys()}

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Esquemas Pydantic
class SettleRequest(BaseModel):
    resource_used: str
    c_real: float
    l_real: float
    task_quality_q: float
    is_failure: bool

class RefactorRequest(BaseModel):
    agent_id: str

@app.get("/api/v1/market/ticker")
def get_ticker(db: Session = Depends(get_db)):
    """
    Devuelve los precios calculados por el AMM y registra el MarketLog.
    """
    # Actualiza precios globalmente (se puede mejorar acoplando al ciclo real de liquidación)
    prices = amm.update_prices(current_usage)
    
    # Limpiar el usage después del ciclo de mercado
    for k in current_usage.keys():
        current_usage[k] *= 0.1 # Decay / reseteo parcial
        
    for res_name, price in prices.items():
        demand = current_usage.get(res_name, 0.0)
        log = models.MarketLog(
            resource_name=res_name,
            dynamic_price=price,
            market_demand=demand
        )
        db.add(log)
    db.commit()
    
    return prices

@app.post("/api/v1/agents/{agent_id}/settle")
def settle_agent(agent_id: str, req: SettleRequest, db: Session = Depends(get_db)):
    """
    Recibe las métricas, calcula recompensa compuesta y asienta la LedgerTransaction.
    """
    agent = db.query(models.AgentRecord).filter(models.AgentRecord.id == agent_id).first()
    if not agent:
        # Auto-registro si no existe para simplificar el flujo
        agent = models.AgentRecord(id=agent_id, wallet_balance=100.0, skill_level=1.0, complexity=1.0)
        db.add(agent)
        db.commit()
        db.refresh(agent)
        
    prices = amm.current_prices
    cost_paid = prices.get(req.resource_used, 1.0)
    
    # Registrar uso para el iterador de mercado
    if req.resource_used in current_usage:
        current_usage[req.resource_used] += 1.0
        
    # Variables y fórmula R
    t_base = 25.0
    alpha, beta, gamma = 0.5, 0.3, 0.2
    c_max = 20.0
    l_max = 6.0
    
    p_fail = 15.0 if req.is_failure else 0.0
    
    # Cálculo Q, Beta, Gamma components
    term_alpha = alpha * req.task_quality_q
    term_beta = beta * max(1.0 - (req.c_real / c_max), 0.0)
    term_gamma = gamma * max((l_max - req.l_real) / l_max, 0.0)
    
    reward = t_base * (term_alpha + term_beta + term_gamma) - p_fail
    
    net_profit = reward - cost_paid
    agent.wallet_balance += net_profit
    
    txn = models.LedgerTransaction(
        agent_id=agent.id,
        resource_used=req.resource_used,
        cost_paid=cost_paid,
        reward_earned=reward,
        net_profit=net_profit,
        task_result="FAILURE" if req.is_failure else "SUCCESS"
    )
    db.add(txn)
    db.commit()
    db.refresh(agent)
    
    return {
        "wallet_balance": agent.wallet_balance,
        "net_profit": net_profit,
        "reward": reward,
        "cost_paid": cost_paid
    }

@app.post("/api/v1/devops/refactor")
def refactor_agent(req: RefactorRequest, db: Session = Depends(get_db)):
    """
    Refactoriza al agente reduciendo su complejidad y aumentando sus skills a cambio del costo premium.
    """
    agent = db.query(models.AgentRecord).filter(models.AgentRecord.id == req.agent_id).first()
    if not agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
        
    resource = "Refactor_DevOps_Resource"
    premium_cost = amm.current_prices.get(resource, 10.0)
    
    if agent.wallet_balance < premium_cost:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient funds for Refactor")
        
    agent.wallet_balance -= premium_cost
    agent.complexity = max(agent.complexity - 1.5, 1.0)
    agent.skill_level += 1.0
    
    if resource in current_usage:
        current_usage[resource] += 1.0
    
    txn = models.LedgerTransaction(
        agent_id=agent.id,
        resource_used=resource,
        cost_paid=premium_cost,
        reward_earned=0.0,
        net_profit=-premium_cost,
        task_result="REFACTOR_SUCCESS"
    )
    db.add(txn)
    db.commit()
    db.refresh(agent)
    
    return {
        "wallet_balance": agent.wallet_balance,
        "new_complexity": agent.complexity,
        "new_skill_level": agent.skill_level,
    }
