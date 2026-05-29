import re
from playwright.sync_api import Page

LEAD_URL_PATTERN = re.compile(
    r"https://renaultarca\.my\.site\.com/NestSFA/s/lead/[A-Za-z0-9]+/[^\s\"'>]+"
)


class OutlookMailReader:
    OUTLOOK_URL = "https://outlook.office.com/mail/inbox"

    def __init__(self, page: Page):
        self._page = page

    def _naviguer_dossier_maeva(self) -> None:
        self._page.goto(self.OUTLOOK_URL)
        self._page.wait_for_load_state("networkidle")
        dossier = self._page.locator(
            "div[role='treeitem']:has-text('Maeva'), "
            "span:has-text('Maeva'), "
            "a:has-text('Maeva')"
        ).first
        dossier.wait_for(state="visible", timeout=15_000)
        dossier.click()
        self._page.wait_for_load_state("networkidle")

    def get_unread_lead_emails(self) -> list[dict]:
        self._naviguer_dossier_maeva()
        self._page.screenshot(path="debug_outlook.png")

        try:
            self._page.wait_for_selector(
                "div[role='list'], div[role='listitem'], [data-convid]",
                timeout=30_000
            )
        except Exception:
            print("[DEBUG] Aucun élément de liste trouvé — screenshot sauvegardé dans debug_outlook.png")
            return []

        emails_data = []
        unread = self._page.locator("[data-convid]").all()
        print(f"[DEBUG] {len(unread)} email(s) dans le dossier Maeva")

        for item in unread:
            aria = item.get_attribute("aria-label") or ""
            print(f"[DEBUG] Email aria-label: {aria[:100]}")
            if "Non lu" not in aria and "Unread" not in aria:
                continue

            item.click()
            self._page.wait_for_load_state("networkidle")

            body = self._page.locator("div[role='main']").inner_text()
            lead_urls = LEAD_URL_PATTERN.findall(body)
            print(f"[DEBUG] Lead URLs trouvées: {lead_urls}")

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
