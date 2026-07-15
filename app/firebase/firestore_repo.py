"""
Firestore collection helpers — Step 6 of the pipeline (Store).

Collections:
  signals    -> latest live signal per instrument (overwritten each cycle)
  history    -> append-only log of every generated signal (for track record)
  users      -> user profiles + subscription state
"""

from datetime import datetime
from typing import Optional, List
from app.firebase.firebase_init import get_firestore
from app.utils.logger import get_logger

logger = get_logger("firestore_repo")

SIGNALS_COLLECTION = "signals"
HISTORY_COLLECTION = "history"
USERS_COLLECTION = "users"


def save_live_signal(instrument: str, data: dict):
    db = get_firestore()
    data["updated_at"] = datetime.utcnow().isoformat()
    db.collection(SIGNALS_COLLECTION).document(instrument).set(data)
    logger.info(f"Saved live signal for {instrument}")


def append_history(instrument: str, data: dict):
    db = get_firestore()
    data["created_at"] = datetime.utcnow().isoformat()
    db.collection(HISTORY_COLLECTION).add(data)
    logger.info(f"Appended history record for {instrument}")


def get_live_signal(instrument: str) -> Optional[dict]:
    db = get_firestore()
    doc = db.collection(SIGNALS_COLLECTION).document(instrument).get()
    return doc.to_dict() if doc.exists else None


def get_all_live_signals() -> List[dict]:
    db = get_firestore()
    docs = db.collection(SIGNALS_COLLECTION).stream()
    return [d.to_dict() for d in docs]


def get_history(instrument: Optional[str] = None, limit: int = 50) -> List[dict]:
    db = get_firestore()
    query = db.collection(HISTORY_COLLECTION)
    if instrument:
        query = query.where("instrument", "==", instrument)
    query = query.order_by("created_at", direction="DESCENDING").limit(limit)
    return [d.to_dict() for d in query.stream()]


def get_user(uid: str) -> Optional[dict]:
    db = get_firestore()
    doc = db.collection(USERS_COLLECTION).document(uid).get()
    return doc.to_dict() if doc.exists else None


def save_user(uid: str, data: dict):
    db = get_firestore()
    db.collection(USERS_COLLECTION).document(uid).set(data, merge=True)


def update_subscription(uid: str, plan: str, expiry_iso: str):
    db = get_firestore()
    db.collection(USERS_COLLECTION).document(uid).update({
        "is_subscribed": True,
        "subscription_plan": plan,
        "subscription_expiry": expiry_iso,
    })
    logger.info(f"Updated subscription for user {uid}: plan={plan}")
