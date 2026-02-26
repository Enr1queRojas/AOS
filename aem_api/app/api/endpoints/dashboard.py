from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from ...api.dependencies import get_db
from ...db import models
from ...schemas.pydantic_models import LedgerTransactionResponse

router = APIRouter()

@router.get("/macro")
def get_macro_kpis(db: Session = Depends(get_db)):
    """
    Devuelve KPIs (promedio de éxito, latencia promedio del sistema, balance total en circulación).
    """
    total_txs = db.query(models.LedgerTransaction).count()
    successful_txs = db.query(models.LedgerTransaction).filter(models.LedgerTransaction.task_result == "SUCCESS").count()
    success_rate = (successful_txs / total_txs * 100) if total_txs > 0 else 0.0
    
    avg_latency = 1.25 # Simulated for demo

    total_balance = db.query(func.sum(models.AgentRecord.wallet_balance)).scalar() or 0.0
    
    return {
        "success_rate_percent": round(success_rate, 2),
        "avg_system_latency_ms": avg_latency,
        "total_balance_circulation": round(total_balance, 2)
    }

@router.get("/ledger", response_model=List[LedgerTransactionResponse])
def get_ledger(db: Session = Depends(get_db)):
    """
    Devuelve las últimas 50 transacciones ordenadas por fecha descendente.
    """
    transactions = (
        db.query(models.LedgerTransaction)
        .order_by(models.LedgerTransaction.timestamp.desc())
        .limit(50)
        .all()
    )
    return transactions
