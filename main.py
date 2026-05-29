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
CRM_SESSION = SESSION_DIR / "crm_session.json"
OUTLOOK_SESSION = SESSION_DIR / "outlook_session.json"
LOGIN_URL = "https://sso.renault.com/app/renault_irn54144_1/exk7slmj6lRFh2ZHg417/sso/saml"


def setup_sessions(p) -> None:
    """Première connexion manuelle — sauvegarde les sessions Outlook et CRM."""
    log.info("=== PREMIÈRE CONNEXION — SETUP ===")
    browser = p.chromium.launch(headless=False)

    # Session Outlook
    log.info("Étape 1/2 — Connexion Outlook")
    outlook_ctx = browser.new_context()
    outlook_page = outlook_ctx.new_page()
    outlook_page.goto("https://outlook.office.com/mail/inbox")
    outlook_page.wait_for_load_state("networkidle")
    input("Connecte-toi à Outlook dans Chrome, puis appuie sur Entrée ici...")
    outlook_ctx.storage_state(path=str(OUTLOOK_SESSION))
    log.info("Session Outlook sauvegardée.")

    # Session CRM
    log.info("Étape 2/2 — Connexion CRM")
    crm_ctx = browser.new_context()
    crm_page = crm_ctx.new_page()
    crm_page.goto(LOGIN_URL)
    crm_page.wait_for_load_state("networkidle")
    input("Connecte-toi au CRM avec ton token USB, puis appuie sur Entrée ici...")
    crm_ctx.storage_state(path=str(CRM_SESSION))
    log.info("Session CRM sauvegardée.")

    browser.close()
    log.info("Setup terminé. Relance le bot avec : py main.py")


def main() -> None:
    log.info("Démarrage du bot MAEVA")
    SESSION_DIR.mkdir(exist_ok=True)

    with sync_playwright() as p:
        # Premier lancement : setup des sessions
        if not CRM_SESSION.exists() or not OUTLOOK_SESSION.exists():
            setup_sessions(p)
            return

        # Lancement normal — invisible, sessions sauvegardées
        browser = p.chromium.launch(headless=True)

        outlook_ctx = browser.new_context(storage_state=str(OUTLOOK_SESSION))
        outlook_page = outlook_ctx.new_page()

        crm_ctx = browser.new_context(storage_state=str(CRM_SESSION))
        crm_page = crm_ctx.new_page()

        reader = OutlookMailReader(
            email=os.environ["OUTLOOK_EMAIL"],
            password=os.environ["OUTLOOK_PASSWORD"],
            page=outlook_page,
        )
        bot = MaevaBot(page=crm_page)

        log.info("Vérification session Outlook...")
        outlook_page.goto("https://outlook.office.com/mail/inbox")
        outlook_page.wait_for_load_state("networkidle")

        log.info("Vérification session CRM...")
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
