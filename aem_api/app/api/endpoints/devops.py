from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ...api.dependencies import get_db
from ...db import models
from ...schemas.pydantic_models import RefactorRequest
from ...core.market_logic import shared_amm, current_usage

router = APIRouter()

@router.post("/refactor")
def refactor_agent(req: RefactorRequest, db: Session = Depends(get_db)):
    """
    Refactors the agent reducing its complexity and increasing skills 
    in exchange for premium market cost.
    """
    agent = db.query(models.AgentRecord).filter(models.AgentRecord.id == req.agent_id).first()
    if not agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
        
    resource = "Refactor_DevOps_Resource"
    premium_cost = shared_amm.get_price(resource)
    
    if agent.wallet_balance < premium_cost:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient funds for Refactor")
        
    agent.wallet_balance -= premium_cost
    agent.complexity = max(agent.complexity - 1.5, 1.0)
    agent.skill_level += 1.0
    
    if resource in current_usage:
        current_usage[resource] += 1.0
    
    transaction = models.LedgerTransaction(
        agent_id=agent.id,
        resource_used=resource,
        cost_paid=premium_cost,
        reward_earned=0.0,
        net_profit=-premium_cost,
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
