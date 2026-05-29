import re
from playwright.sync_api import Page

LEAD_URL_PATTERN = re.compile(
    r"https://renaultarca\.my\.site\.com/NestSFA/s/lead/[A-Za-z0-9]+/[^\s\"'>]+"
)


class OutlookMailReader:
    OUTLOOK_URL = "https://outlook.office.com/mail/inbox"

    def __init__(self, page: Page):
        self._page = page

    def get_unread_lead_emails(self) -> list[dict]:
        """Retourne la liste des emails non lus contenant un lien de lead Maeva."""
        self._page.goto(self.OUTLOOK_URL)
        self._page.wait_for_load_state("networkidle")
        self._page.wait_for_selector("div[role='list']", timeout=20_000)

        emails_data = []
        unread = self._page.locator("div[role='listitem'][data-convid]").all()

        for item in unread:
            aria = item.get_attribute("aria-label") or ""
            if "Non lu" not in aria and "Unread" not in aria:
                continue

            item.click()
            self._page.wait_for_load_state("networkidle")

            body = self._page.locator("div[role='main']").inner_text()
            lead_urls = LEAD_URL_PATTERN.findall(body)

            if lead_urls:
                conv_id = item.get_attribute("data-convid")
                emails_data.append({
                    "conv_id": conv_id,
                    "lead_urls": list(set(lead_urls)),
                    "element": item,
                })

        return emails_data

    def mark_as_read(self, item_element) -> None:
        try:
            item_element.click(button="right")
            self._page.locator("span:has-text('Marquer comme lu'), span:has-text('Mark as read')").first.click()
        except Exception:
            pass
