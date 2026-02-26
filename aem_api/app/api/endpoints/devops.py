from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ...api.dependencies import get_db
from ...db import models

router = APIRouter()

PREMIUM_COST = 50.0

@router.post("/request_refactor")
def request_refactor(agent_id: str, db: Session = Depends(get_db)):
    """
    Descuenta el costo premium del saldo del agente, reduce su complexity,
    aumenta su skill_level y registra la transacción.
    """
    agent = db.query(models.AgentRecord).filter(models.AgentRecord.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
        
    if agent.wallet_balance < PREMIUM_COST:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient funds for refactor")
        
    agent.wallet_balance -= PREMIUM_COST
    agent.complexity = max(0.1, agent.complexity - 0.2)
    agent.skill_level += 0.5
    
    transaction = models.LedgerTransaction(
        agent_id=agent.id,
        resource_used="devops_refactor",
        cost_paid=PREMIUM_COST,
        reward_earned=0.0,
        net_profit=-PREMIUM_COST,
        task_result="REFACTOR_SUCCESS"
    )
    
    db.add(transaction)
    db.commit()
    db.refresh(agent)
    
    return {
        "message": "Refactor successful",
        "new_complexity": agent.complexity,
        "new_skill_level": agent.skill_level,
        "new_balance": agent.wallet_balance
    }
