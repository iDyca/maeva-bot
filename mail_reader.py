import os
import requests
import msal


class MailReader:
    GRAPH_URL = "https://graph.microsoft.com/v1.0"

    def __init__(self):
        self.client_id = os.environ["AZURE_CLIENT_ID"]
        self.client_secret = os.environ["AZURE_CLIENT_SECRET"]
        self.tenant_id = os.environ["AZURE_TENANT_ID"]
        self.mail_user = os.environ["MAIL_USER"]
        self._token = None

    def _get_token(self) -> str:
        app = msal.ConfidentialClientApplication(
            self.client_id,
            authority=f"https://login.microsoftonline.com/{self.tenant_id}",
            client_credential=self.client_secret,
        )
        result = app.acquire_token_for_client(
            scopes=["https://graph.microsoft.com/.default"]
        )
        if "access_token" not in result:
            raise RuntimeError(f"Échec d'authentification Graph API: {result.get('error_description')}")
        return result["access_token"]

    def _headers(self) -> dict:
        if not self._token:
            self._token = self._get_token()
        return {"Authorization": f"Bearer {self._token}", "Content-Type": "application/json"}

    def get_unread_emails(self) -> list[dict]:
        url = (
            f"{self.GRAPH_URL}/users/{self.mail_user}/mailFolders/inbox/messages"
            "?$filter=isRead eq false&$orderby=receivedDateTime asc&$top=50"
            "&$select=id,subject,from,receivedDateTime,body"
        )
        resp = requests.get(url, headers=self._headers(), timeout=30)
        resp.raise_for_status()
        return resp.json().get("value", [])

    def mark_as_read(self, message_id: str) -> None:
        url = f"{self.GRAPH_URL}/users/{self.mail_user}/messages/{message_id}"
        resp = requests.patch(
            url,
            headers=self._headers(),
            json={"isRead": True},
            timeout=30,
        )
        resp.raise_for_status()
