import re
from playwright.sync_api import Page

LEAD_URL_PATTERN = re.compile(
    r"https://renaultarca\.my\.site\.com/NestSFA/s/lead/[A-Za-z0-9]+/[^\s\"'>]+"
)


class OutlookMailReader:
    OUTLOOK_URL = "https://outlook.office.com/mail/inbox"

    def __init__(self, page: Page):
        self._page = page
        self._traites: set[str] = set()  # IDs déjà traités

    def get_unread_lead_emails(self) -> list[dict]:
        self._page.goto(self.OUTLOOK_URL)
        self._page.wait_for_load_state("networkidle")

        try:
            self._page.wait_for_selector("[data-convid]", timeout=30_000)
        except Exception:
            print("[DEBUG] Boîte de réception non chargée")
            return []

        emails_data = []
        items = self._page.locator("[data-convid]").all()
        print(f"[DEBUG] {len(items)} email(s) visibles")

        for item in items:
            conv_id = item.get_attribute("data-convid") or ""
            if conv_id in self._traites:
                continue

            item.click()
            self._page.wait_for_load_state("networkidle")

            body = self._page.locator("div[role='main']").inner_text()
            lead_urls = LEAD_URL_PATTERN.findall(body)

            if lead_urls:
                print(f"[DEBUG] Lead trouvé : {lead_urls}")
                emails_data.append({
                    "conv_id": conv_id,
                    "lead_urls": list(set(lead_urls)),
                    "element": item,
                })

        return emails_data

    def mark_as_read(self, conv_id: str, item_element) -> None:
        self._traites.add(conv_id)
        try:
            item_element.click(button="right")
            self._page.locator(
                "span:has-text('Marquer comme lu'), span:has-text('Mark as read')"
            ).first.click()
        except Exception:
            pass
