import requests
from django.conf import settings
from .models import Notification

def send_push_notification(
    player_id,
    title,
    message
):

    url = "https://api.onesignal.com/notifications"

    headers = {
        "accept": "application/json",
        "Authorization": f"Key {settings.ONESIGNAL_REST_API_KEY}",
        "content-type": "application/json"
    }

    payload = {
        "app_id": settings.ONESIGNAL_APP_ID,
        "include_player_ids": [player_id],
        "headings": {
            "en": title
        },
        "contents": {
            "en": message
        }
    }

    response = requests.post(
        url,
        json=payload,
        headers=headers,
        timeout=10
    )

    return response.json()


def create_notification(
    *,
    user,
    title,
    message,
    notification_event="general",
    notification_type="push",
    metadata=None,
    send_push=True
):

    notification = Notification.objects.create(
        user=user,
        title=title,
        message=message,
        notification_event=notification_event,
        notification_type=notification_type,
        metadata=metadata or {}
    )

    if (
        send_push and
        user.onesignal_player_id
    ):
        send_push_notification(
            player_id=user.onesignal_player_id,
            title=title,
            message=message
        )

    return notification