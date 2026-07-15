"""
Notification Service — alerts users when a new high-confidence signal fires.
Uses Firebase Cloud Messaging (FCM) for push notifications.
"""

from firebase_admin import messaging
from app.utils.logger import get_logger

logger = get_logger("notification_service")

MIN_CONFIDENCE_FOR_ALERT = 70.0


class NotificationService:
    async def notify_new_signal(self, fcm_tokens: list[str], instrument: str, action: str, confidence: float):
        if confidence < MIN_CONFIDENCE_FOR_ALERT or not fcm_tokens:
            return

        title = f"New {action} Signal: {instrument}"
        body = f"Confidence: {confidence}% — check the app for entry, SL, and targets."

        message = messaging.MulticastMessage(
            notification=messaging.Notification(title=title, body=body),
            tokens=fcm_tokens,
        )
        try:
            response = messaging.send_multicast(message)
            logger.info(f"Notification sent for {instrument}: {response.success_count} succeeded, {response.failure_count} failed")
        except Exception as e:
            logger.error(f"Notification send failed for {instrument}: {e}")


notification_service = NotificationService()
