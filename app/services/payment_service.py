"""
Payment Service — Razorpay integration.

Flow:
  User -> Choose Plan -> Razorpay Order -> Client pays -> Webhook Verify ->
  Subscription Active -> Firestore Update -> Dashboard Unlock
"""

from datetime import datetime, timedelta
from fastapi import HTTPException
from app.razorpay.client import create_order, verify_payment_signature, verify_webhook_signature
from app.schemas.user import CreateOrderRequest, CreateOrderResponse, VerifyPaymentRequest
from app.services.subscription_service import PLANS, subscription_service
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger("payment_service")


class PaymentService:
    async def create_order(self, uid: str, payload: CreateOrderRequest) -> CreateOrderResponse:
        plan = PLANS.get(payload.plan_id)
        if not plan:
            raise HTTPException(status_code=400, detail="Invalid plan_id")

        order = create_order(amount_inr=plan["price_inr"], receipt=f"{uid}_{payload.plan_id}_{datetime.utcnow().timestamp()}")
        logger.info(f"Created Razorpay order {order['id']} for user {uid}, plan {payload.plan_id}")

        return CreateOrderResponse(
            order_id=order["id"],
            amount=order["amount"],
            razorpay_key_id=settings.RAZORPAY_KEY_ID,
        )

    async def verify_and_activate(self, uid: str, payload: VerifyPaymentRequest, plan_id: str):
        """Direct client-side verification path (in addition to webhook, for instant UX)."""
        valid = verify_payment_signature(
            payload.razorpay_order_id, payload.razorpay_payment_id, payload.razorpay_signature
        )
        if not valid:
            raise HTTPException(status_code=400, detail="Payment signature verification failed")

        await subscription_service.activate_subscription(uid, plan_id)
        logger.info(f"Payment verified and subscription activated for user {uid}")
        return {"status": "success", "message": "Subscription activated"}

    async def handle_webhook(self, payload_body: bytes, signature: str, event_data: dict):
        """Source of truth — webhook confirms payment server-to-server regardless of client state."""
        if not verify_webhook_signature(payload_body, signature):
            raise HTTPException(status_code=400, detail="Invalid webhook signature")

        event = event_data.get("event")
        if event == "payment.captured":
            payment_entity = event_data["payload"]["payment"]["entity"]
            notes = payment_entity.get("notes", {})
            uid = notes.get("uid")
            plan_id = notes.get("plan_id")
            if uid and plan_id:
                await subscription_service.activate_subscription(uid, plan_id)
                logger.info(f"Webhook activated subscription for user {uid}, plan {plan_id}")
            else:
                logger.warning("Webhook payment.captured missing uid/plan_id in notes")

        return {"status": "ok"}


payment_service = PaymentService()
