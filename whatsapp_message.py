import os
import requests
from dotenv import load_dotenv


# Load .env file
load_dotenv()


# Get WhatsApp credentials from .env
ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")


# Check credentials
if not ACCESS_TOKEN:
    raise ValueError(
        "WHATSAPP_ACCESS_TOKEN is missing in .env"
    )

if not PHONE_NUMBER_ID:
    raise ValueError(
        "WHATSAPP_PHONE_NUMBER_ID is missing in .env"
    )


# WhatsApp Cloud API URL
URL = (
    f"https://graph.facebook.com/v23.0/"
    f"{PHONE_NUMBER_ID}/messages"
)


def send_whatsapp_message(
    mobile,
    challan_id,
    vehicle_number,
    violation,
    fine
):

    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    data = {
        "messaging_product": "whatsapp",
        "to": mobile,
        "type": "template",
        "template": {
            "name": "traffic_challan",
            "language": {
                "code": "en_US"
            },
            "components": [
                {
                    "type": "body",
                    "parameters": [
                        {
                            "type": "text",
                            "text": str(challan_id)
                        },
                        {
                            "type": "text",
                            "text": vehicle_number
                        },
                        {
                            "type": "text",
                            "text": violation
                        },
                        {
                            "type": "text",
                            "text": f"₹{fine}"
                        }
                    ]
                }
            ]
        }
    }

    print()
    print("=" * 60)
    print("SENDING WHATSAPP MESSAGE")
    print("=" * 60)

    print("To:", mobile)
    print("Challan ID:", challan_id)
    print("Vehicle:", vehicle_number)
    print("Violation:", violation)
    print("Fine:", fine)

    response = requests.post(
        URL,
        headers=headers,
        json=data
    )

    print()
    print("WhatsApp Status:", response.status_code)
    print("WhatsApp Response:", response.text)

    if response.ok:
        print()
        print("WhatsApp message request successful.")
        return True

    print()
    print("WhatsApp message failed.")
    return False


# --------------------------------------------------
# TEST
# --------------------------------------------------

if __name__ == "__main__":

    print()
    print("=" * 60)
    print("WHATSAPP API TEST")
    print("=" * 60)

    send_whatsapp_message(
        mobile="917993949559",
        challan_id=1,
        vehicle_number="TS10ED8176",
        violation="No Helmet",
        fine=200
    )