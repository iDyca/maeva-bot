import os
import time
import logging
from pathlib import Path
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
SESSION_DIR = Path("sessions")


def main() -> None:
    log.info("Démarrage du bot MAEVA")
    SESSION_DIR.mkdir(exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)

        # Contexte Outlook
        outlook_context = browser.new_context()
        outlook_page = outlook_context.new_page()

        # Contexte CRM — réutilise la session sauvegardée si elle existe
        crm_session = str(SESSION_DIR / "crm_session.json")
        if Path(crm_session).exists():
            crm_context = browser.new_context(storage_state=crm_session)
        else:
            crm_context = browser.new_context()

        crm_page = crm_context.new_page()

        reader = OutlookMailReader(
            email=os.environ["OUTLOOK_EMAIL"],
            password=os.environ["OUTLOOK_PASSWORD"],
            page=outlook_page,
        )
        bot = MaevaBot(page=crm_page)

        # Connexion Outlook
        log.info("Connexion à Outlook...")
        reader.login()

        # Connexion CRM — manuelle si pas de session sauvegardée
        crm_page.goto(os.environ["CRM_URL"])
        crm_page.wait_for_load_state("networkidle")

        if not Path(crm_session).exists():
            log.info("=== CONNEXION CRM REQUISE ===")
            log.info("Connecte-toi au CRM dans la fenêtre qui vient de s'ouvrir.")
            log.info("Appuie sur Entrée ici une fois connecté...")
            input()
            crm_context.storage_state(path=crm_session)
            log.info("Session CRM sauvegardée.")

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
                                reader.mark_as_read(email["element"])
                            else:
                                log.warning(f"✗ Échec : {lead_url}")
                else:
                    log.debug("Aucun email avec lead")
            except Exception as exc:
                log.error(f"Erreur inattendue : {exc}", exc_info=True)

            time.sleep(POLLING_INTERVAL)


if __name__ == "__main__":
    main()
