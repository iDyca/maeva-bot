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

# Chemin du profil Chrome de l'utilisateur (déjà connecté au CRM et Outlook)
CHROME_PROFILE = os.getenv(
    "CHROME_PROFILE",
    str(Path.home() / "AppData/Local/Google/Chrome/User Data")
)


def main() -> None:
    log.info("Démarrage du bot MAEVA")
    log.info("Ferme Google Chrome complètement avant de continuer...")
    input("Appuie sur Entrée quand Chrome est fermé...")

    with sync_playwright() as p:
        # Utilise le profil Chrome existant (sessions déjà actives)
        browser = p.chromium.launch_persistent_context(
            user_data_dir=CHROME_PROFILE,
            headless=False,
            args=["--profile-directory=Default"],
        )

        outlook_page = browser.new_page()
        crm_page = browser.new_page()

        reader = OutlookMailReader(
            email=os.environ["OUTLOOK_EMAIL"],
            password=os.environ["OUTLOOK_PASSWORD"],
            page=outlook_page,
        )
        bot = MaevaBot(page=crm_page)

        log.info("Vérification session Outlook...")
        reader.login()

        log.info("Chargement du CRM...")
        crm_page.goto(os.environ["CRM_URL"])
        crm_page.wait_for_load_state("networkidle")

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
