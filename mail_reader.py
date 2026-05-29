import re
from playwright.sync_api import Page

LEAD_URL_PATTERN = re.compile(
    r"https://renaultarca\.my\.site\.com/NestSFA/s/lead/[A-Za-z0-9]+/[^\s\"'>]+"
)


class OutlookMailReader:
    OUTLOOK_URL = "https://outlook.office.com/mail/inbox"

    def __init__(self, email: str, password: str, page: Page):
        self.email = email
        self.password = password
        self._page = page
        self._logged_in = False

    def login(self) -> None:
        self._page.goto(self.OUTLOOK_URL)
        self._page.wait_for_load_state("networkidle")

        self._page.fill("input[type='email']", self.email)
        self._page.click("input[type='submit']")
        self._page.wait_for_load_state("networkidle")

        self._page.fill("input[type='password']", self.password)
        self._page.click("input[type='submit']")
        self._page.wait_for_load_state("networkidle")

        # "Rester connecté ?" → Non
        stay_signed = self._page.locator("input[id='idBtn_Back']")
        if stay_signed.is_visible():
            stay_signed.click()
            self._page.wait_for_load_state("networkidle")

        self._logged_in = True

    def get_unread_lead_emails(self) -> list[dict]:
        """Retourne la liste des emails non lus contenant un lien de lead Maeva."""
        if not self._logged_in:
            self.login()

        # Attendre que la boîte de réception soit chargée
        self._page.wait_for_selector("div[role='list']", timeout=15_000)

        emails_data = []
        # Récupérer tous les emails non lus (aria-label contient "Non lu")
        unread = self._page.locator("div[role='listitem'][data-convid]").all()

        for item in unread:
            aria = item.get_attribute("aria-label") or ""
            if "Non lu" not in aria and "Unread" not in aria:
                continue

            item.click()
            self._page.wait_for_load_state("networkidle")

            # Extraire le contenu du mail ouvert
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
        """Clic droit → Marquer comme lu."""
        try:
            item_element.click(button="right")
            self._page.locator("span:has-text('Marquer comme lu'), span:has-text('Mark as read')").first.click()
        except Exception:
            pass
