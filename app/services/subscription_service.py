"""Subscription Service — plan catalog and activation/expiry logic."""

from datetime import datetime, timedelta
from app.firebase.firestore_repo import update_subscription, get_user
from app.utils.logger import get_logger

logger = get_logger("subscription_service")

PLANS = {
    "monthly": {"plan_id": "monthly", "name": "Monthly Plan", "price_inr": 999, "duration_days": 30},
    "quarterly": {"plan_id": "quarterly", "name": "Quarterly Plan", "price_inr": 2499, "duration_days": 90},
    "yearly": {"plan_id": "yearly", "name": "Yearly Plan", "price_inr": 8999, "duration_days": 365},
}


class SubscriptionService:
    async def activate_subscription(self, uid: str, plan_id: str):
        plan = PLANS.get(plan_id)
        if not plan:
            raise ValueError(f"Unknown plan_id: {plan_id}")

        expiry = datetime.utcnow() + timedelta(days=plan["duration_days"])
        update_subscription(uid, plan_id, expiry.isoformat())
        logger.info(f"Subscription activated for {uid}: {plan_id}, expires {expiry.isoformat()}")

    async def is_active(self, uid: str) -> bool:
        user = get_user(uid)
        if not user or not user.get("is_subscribed"):
            return False
        expiry_str = user.get("subscription_expiry")
        if not expiry_str:
            return False
        expiry = datetime.fromisoformat(expiry_str)
        return datetime.utcnow() < expiry

    def get_plans(self) -> list[dict]:
        return list(PLANS.values())


subscription_service = SubscriptionService()
