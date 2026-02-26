from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class SettleRequest(BaseModel):
    resource_used: str
    c_real: float
    l_real: float
    task_quality_q: float
    is_failure: bool

class RefactorRequest(BaseModel):
    agent_id: str

class AgentBase(BaseModel):
    wallet_balance: float
    skill_level: float
    complexity: float

class AgentResponse(AgentBase):
    id: str
    updated_at: datetime
    
    class Config:
        from_attributes = True

class LedgerTransactionResponse(BaseModel):
    id: int
    agent_id: str
    resource_used: str
    cost_paid: float
    reward_earned: float
    net_profit: float
    task_result: str
    timestamp: datetime
    
    class Config:
        from_attributes = True

class MarketTickerResponse(BaseModel):
    resource_name: str
    dynamic_price: float
    market_demand: float
