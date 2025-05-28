import os
from manifold_core.secrets.bitwarden.backend import Backend
import requests

class SlackAPI:
    def __init__(self, name: str):
        self.name = name
        self.secrets = Backend()

    def get_token(self) -> str:
        return self.secrets.get_secret(f"slack:{self.name}:token")

    def save_token(self, token: str):
        self.secrets.set_secret(f"slack:{self.name}:token", token)

    def delete_token(self):
        raise NotImplementedError("Token deletion is not implemented yet.")

    def get_channel_id_by_name(self, channel_name: str) -> str | None:
        token = self.get_token()
        url = "https://slack.com/api/conversations.list"
        headers = {
            "Authorization": f"Bearer {token}"
        }

        cursor = None
        while True:
            params = {"exclude_archived": "true", "limit": 1000}
            if cursor:
                params["cursor"] = cursor

            response = requests.get(url, headers=headers, params=params)
            data = response.json()

            if not data.get("ok"):
                raise Exception(f"Slack API error: {data.get('error')}")

            for channel in data.get("channels", []):
                if channel["name"] == channel_name:
                    return channel["id"]

            cursor = data.get("response_metadata", {}).get("next_cursor")
            if not cursor:
                break

        return None