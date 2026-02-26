from fastapi import APIRouter
from typing import List
from ...schemas.pydantic_models import MarketTickerResponse
from ...core.market_logic import shared_amm

router = APIRouter()

@router.get("/ticker", response_model=List[MarketTickerResponse])
def get_ticker():
    """Returns the current dynamic prices calculated by the shared AMM."""
    return shared_amm.get_prices()
