import os
import time
import logging
from dotenv import load_dotenv

from mail_reader import MailReader
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
    reader = MailReader()

    with MaevaBot() as bot:
        while True:
            try:
                emails = reader.get_unread_emails()
                if emails:
                    log.info(f"{len(emails)} email(s) non lu(s) trouvé(s)")
                    for email in emails:
                        subject = email.get("subject", "(sans objet)")
                        log.info(f"Traitement : {subject}")
                        success = bot.traiter_email(email)
                        if success:
                            reader.mark_as_read(email["id"])
                            log.info(f"✓ Traité et marqué lu : {subject}")
                        else:
                            log.warning(f"✗ Échec du traitement : {subject}")
                else:
                    log.debug("Aucun email non lu")
            except Exception as exc:
                log.error(f"Erreur inattendue : {exc}", exc_info=True)

            time.sleep(POLLING_INTERVAL)


if __name__ == "__main__":
    main()
