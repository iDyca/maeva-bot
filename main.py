import os
import time
import logging
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

from mail_reader import OutlookMailReader
from maeva_bot import MaevaBot

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("maeva")

POLLING_INTERVAL = int(os.getenv("POLLING_INTERVAL", "60"))


def main() -> None:
    log.info("Démarrage du bot MAEVA")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # headless=True en production
        context = browser.new_context()

        # Deux onglets : un pour Outlook, un pour le CRM
        outlook_page = context.new_page()
        crm_page = context.new_page()

        reader = OutlookMailReader(
            email=os.environ["OUTLOOK_EMAIL"],
            password=os.environ["OUTLOOK_PASSWORD"],
            page=outlook_page,
        )
        bot = MaevaBot(page=crm_page)

        log.info("Connexion à Outlook...")
        reader.login()

        log.info("Connexion au CRM Maeva...")
        bot.login()

        log.info("Bot prêt — polling toutes les %ds", POLLING_INTERVAL)

        while True:
            try:
                emails = reader.get_unread_lead_emails()
                if emails:
                    log.info(f"{len(emails)} email(s) avec leads trouvé(s)")
                    for email in emails:
                        for lead_url in email["lead_urls"]:
                            log.info(f"Traitement lead : {lead_url}")
                            success = bot.traiter_lead(lead_url)
                            if success:
                                log.info(f"✓ Lead traité : {lead_url}")
                            else:
                                log.warning(f"✗ Échec : {lead_url}")
                        if any(bot.traiter_lead(u) for u in email["lead_urls"]):
                            reader.mark_as_read(email["element"])
                else:
                    log.debug("Aucun email avec lead")
            except Exception as exc:
                log.error(f"Erreur inattendue : {exc}", exc_info=True)

            time.sleep(POLLING_INTERVAL)


if __name__ == "__main__":
    main()
