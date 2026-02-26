from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ...api.dependencies import get_db
from ...db import models
from ...schemas.pydantic_models import AgentResponse, SettleRequest
from ...core.market_logic import calculate_reward, shared_amm

router = APIRouter()

@router.get("/{agent_id}/wallet", response_model=AgentResponse)
def get_wallet(agent_id: str, db: Session = Depends(get_db)):
    """
    Returns the wallet balance and stats of the agent.
    """
    agent = db.query(models.AgentRecord).filter(models.AgentRecord.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
    return agent

@router.post("/{agent_id}/settle")
def settle_transaction(agent_id: str, request: SettleRequest, db: Session = Depends(get_db)):
    """Calculates reward, updates wallet, and inserts ledger transaction."""
    agent = db.query(models.AgentRecord).filter(models.AgentRecord.id == agent_id).first()
    if not agent:
        # Auto-create agent for testing purposes if it doesn't exist
        agent = models.AgentRecord(id=agent_id, wallet_balance=35.0, skill_level=3.0, complexity=5.0)
        db.add(agent)
        db.commit()
        db.refresh(agent)
    
    # Get the price from the shared AMM
    cost = shared_amm.get_price(request.resource_used)
    
    if agent.wallet_balance < cost and not request.is_failure:
         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient funds")

    # Math constants
    T_BASE = 25.0
    ALPHA, BETA, GAMMA = 0.5, 0.3, 0.2
    C_MAX = 20.0
    L_MAX = 6.0
    P_FAIL = 15.0
    
    reward = calculate_reward(
        t_base=T_BASE, alpha=ALPHA, beta=BETA, gamma=GAMMA,
        q=request.task_quality_q, c_real=request.c_real, c_max=C_MAX,
        l_real=request.l_real, l_max=L_MAX, p_fail=P_FAIL, is_failure=request.is_failure
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
        "reward": reward,
        "cost_paid": cost_paid,
        "net_profit": net_profit,
        "wallet_balance": agent.wallet_balance
    }
