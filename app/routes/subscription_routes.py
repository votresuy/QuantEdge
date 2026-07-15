from fastapi import APIRouter, Depends, Request, Header, HTTPException
from app.schemas.user import CreateOrderRequest, CreateOrderResponse, VerifyPaymentRequest
from app.services.subscription_service import subscription_service
from app.services.payment_service import payment_service
from app.middleware.auth_middleware import get_current_user

router = APIRouter(prefix="/subscription", tags=["Subscription & Payment"])


@router.get("/plans")
async def get_plans():
    return subscription_service.get_plans()


@router.get("/status")
async def get_status(user: dict = Depends(get_current_user)):
    active = await subscription_service.is_active(user["uid"])
    return {"is_active": active, "plan": user.get("subscription_plan"), "expiry": user.get("subscription_expiry")}


@router.post("/create-order", response_model=CreateOrderResponse)
async def create_order(payload: CreateOrderRequest, user: dict = Depends(get_current_user)):
    return await payment_service.create_order(user["uid"], payload)


@router.post("/verify-payment")
async def verify_payment(payload: VerifyPaymentRequest, plan_id: str, user: dict = Depends(get_current_user)):
    return await payment_service.verify_and_activate(user["uid"], payload, plan_id)


@router.post("/webhook")
async def razorpay_webhook(request: Request, x_razorpay_signature: str = Header(...)):
    """Server-to-server webhook — the authoritative source of truth for payment confirmation."""
    body = await request.body()
    event_data = await request.json()
    return await payment_service.handle_webhook(body, x_razorpay_signature, event_data)
