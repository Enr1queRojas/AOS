from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ...api.dependencies import get_db
from ...db import models
from ...schemas.pydantic_models import AgentResponse, SettleRequest
from ...core.market_logic import calculate_reward, AutomatedMarketMaker

router = APIRouter()
amm = AutomatedMarketMaker()

@router.get("/{agent_id}/wallet", response_model=AgentResponse)
def get_wallet(agent_id: str, db: Session = Depends(get_db)):
    """
    Devuelve el saldo y stats del agente.
    """
    agent = db.query(models.AgentRecord).filter(models.AgentRecord.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
    return agent

@router.post("/{agent_id}/settle")
def settle_transaction(agent_id: str, request: SettleRequest, db: Session = Depends(get_db)):
    """
    Recibe el SettleRequest. Calcula la recompensa matemática, descuenta el costo del recurso,
    actualiza el AgentRecord e inserta una LedgerTransaction.
    """
    agent = db.query(models.AgentRecord).filter(models.AgentRecord.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
    
    cost = amm.get_price(request.resource_used)
    
    if agent.wallet_balance < cost and not request.is_failure:
         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient funds")

    # Constantes matemáticas
    T_BASE = 10.0
    ALPHA = 1.0
    BETA = 0.5
    GAMMA = 0.5
    C_MAX = 5.0
    L_MAX = 10.0
    P_FAIL = 5.0
    
    reward = calculate_reward(
        t_base=T_BASE,
        alpha=ALPHA,
        beta=BETA,
        gamma=GAMMA,
        q=request.task_quality_q,
        c_real=request.c_real,
        c_max=C_MAX,
        l_real=request.l_real,
        l_max=L_MAX,
        p_fail=P_FAIL,
        is_failure=request.is_failure
    )
    
    cost_paid = cost if not request.is_failure else 0.0
    net_profit = reward - cost_paid
    agent.wallet_balance += net_profit
    
    transaction = models.LedgerTransaction(
        agent_id=agent.id,
        resource_used=request.resource_used,
        cost_paid=cost_paid,
        reward_earned=reward,
        net_profit=net_profit,
        task_result="FAILURE" if request.is_failure else "SUCCESS"
    )
    
    db.add(transaction)
    db.commit()
    db.refresh(agent)
    
    return {
        "message": "Transaction settled",
        "reward_earned": reward,
        "cost_paid": cost_paid,
        "net_profit": net_profit,
        "new_balance": agent.wallet_balance
    }
