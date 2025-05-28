import os
import requests

def forward_to_zapier(ticket_number: str, ticket_id: str, description: str, email: str) -> str:
    webhook = os.getenv("ZAPIER_WEBHOOK_URL")
    if not webhook:
        raise RuntimeError("ZAPIER_WEBHOOK_URL is not set")

    payload = {
        "ticketNumber": ticket_number,
        "ticketID": ticket_id,
        "ticketDescription": description,
        "email": email,
    }

    response = requests.post(webhook, json=payload)
    response.raise_for_status()
    return "OK"
