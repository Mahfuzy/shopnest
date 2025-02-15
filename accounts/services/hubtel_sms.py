import base64
from django.conf import settings
import requests

def send_sms(phone_number, message):
    url = "https://smsc.hubtel.com/v1/messages/send"
    credentials = f"{settings.HUBTEL_CLIENT_ID}:{settings.HUBTEL_CLIENT_SECRET}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Basic {encoded_credentials}"
    }

    payload = {
        "From": settings.HUBTEL_SENDER_ID,
        "To": phone_number,
        "Content": message
    }
    try:
        response = requests.post(url, json=payload, headers=headers)
        print("Response Status:", response.status_code)
        print("Response Body:", response.text)  # Debug output

        if response.status_code in [200, 201]:
            return True

        raise Exception(f"Failed to send SMS: {response.text}")
    except requests.RequestException as e:
        raise Exception(f"SMS request failed: {str(e)}")