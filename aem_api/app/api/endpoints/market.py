from fastapi import APIRouter, Depends
from typing import List
from sqlalchemy.orm import Session
from ...api.dependencies import get_db
from ...db import models
from ...schemas.pydantic_models import MarketTickerResponse
from ...core.market_logic import shared_amm

router = APIRouter()

@router.get("/ticker", response_model=List[MarketTickerResponse])
def get_ticker():
    """Returns the current dynamic prices calculated by the shared AMM."""
    return shared_amm.get_prices()

@router.post("/reset")
def reset_market(db: Session = Depends(get_db)):
    """Resets the AMM prices and clears the ledger."""
    db.query(models.LedgerTransaction).delete()
    db.commit()
    
    shared_amm.current_prices = shared_amm.base_prices.copy()
    
    return {"message": "Market reset successfully"}
