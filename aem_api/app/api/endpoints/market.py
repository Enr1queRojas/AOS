from fastapi import APIRouter
from typing import List
from ...schemas.pydantic_models import MarketTickerResponse
from ...core.market_logic import AutomatedMarketMaker

router = APIRouter()
amm = AutomatedMarketMaker()

@router.get("/ticker", response_model=List[MarketTickerResponse])
def get_ticker():
    """
    Devuelve los precios actuales instanciando o consultando la lógica del AMM.
    """
    return amm.get_prices()
