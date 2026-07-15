from fastapi import APIRouter, Depends, Query
from typing import Optional
from app.services.history_service import history_service
from app.middleware.auth_middleware import require_active_subscription

router = APIRouter(prefix="/history", tags=["History"])


@router.get("")
async def get_history(
    instrument: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    user: dict = Depends(require_active_subscription),
):
    return history_service.get_signal_history(instrument=instrument.upper() if instrument else None, limit=limit)
