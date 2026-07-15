from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from app.services.history_service import history_service
from app.middleware.auth_middleware import require_active_subscription

router = APIRouter(prefix="/signals", tags=["Signals"])


@router.get("/live")
async def get_all_live_signals(user: dict = Depends(require_active_subscription)):
    """All current live signals across forex, crypto, stocks, and NIFTY50 trend."""
    return history_service.get_all_current_signals()


@router.get("/live/{instrument}")
async def get_live_signal(instrument: str, user: dict = Depends(require_active_subscription)):
    signal = history_service.get_current_signal(instrument.upper())
    if not signal:
        raise HTTPException(status_code=404, detail="No live signal found for this instrument")
    return signal
