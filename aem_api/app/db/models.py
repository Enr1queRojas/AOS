from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey
from sqlalchemy.sql import func
from .database import Base

class AgentRecord(Base):
    __tablename__ = "agent_records"

    id = Column(String, primary_key=True, index=True)
    wallet_balance = Column(Float, default=0.0)
    skill_level = Column(Float, default=1.0)
    complexity = Column(Float, default=1.0)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class LedgerTransaction(Base):
    __tablename__ = "ledger_transactions"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(String, ForeignKey("agent_records.id"))
    resource_used = Column(String, index=True)
    cost_paid = Column(Float, default=0.0)
    reward_earned = Column(Float, default=0.0)
    net_profit = Column(Float, default=0.0)
    task_result = Column(String)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())


class MarketLog(Base):
    __tablename__ = "market_logs"

    id = Column(Integer, primary_key=True, index=True)
    resource_name = Column(String, index=True)
    dynamic_price = Column(Float, default=0.0)
    market_demand = Column(Float, default=0.0)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
