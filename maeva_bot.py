import os
from datetime import date
from playwright.sync_api import Page, sync_playwright


class MaevaBot:
    def __init__(self):
        self.app_url = os.environ["APP_URL"]
        self.username = os.environ["APP_USERNAME"]
        self.password = os.environ["APP_PASSWORD"]
        self._playwright = None
        self._browser = None
        self._page: Page | None = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self) -> None:
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(headless=True)
        self._page = self._browser.new_page()
        self._login()

    def stop(self) -> None:
        if self._browser:
            self._browser.close()
        if self._playwright:
            self._playwright.stop()

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *_):
        self.stop()

    # ------------------------------------------------------------------
    # Auth
    # ------------------------------------------------------------------

    def _login(self) -> None:
        self._page.goto(self.app_url)
        self._page.wait_for_load_state("networkidle")
        # Adapte les sélecteurs selon l'app réelle
        if self._page.locator("input[name='username'], input[type='email']").count():
            self._page.fill("input[name='username'], input[type='email']", self.username)
            self._page.fill("input[name='password'], input[type='password']", self.password)
            self._page.click("button[type='submit'], input[type='submit']")
            self._page.wait_for_load_state("networkidle")

    # ------------------------------------------------------------------
    # Séquence principale : Prendre → Compte rendu → Qualification
    #                       → En cours → Date du jour → Enregistrer
    # ------------------------------------------------------------------

    def traiter_email(self, email: dict) -> bool:
        """Exécute la séquence complète pour un email donné. Retourne True si succès."""
        subject = email.get("subject", "(sans objet)")
        body = email.get("body", {}).get("content", "")
        sender = email.get("from", {}).get("emailAddress", {}).get("address", "")

        try:
            self._naviguer_vers_formulaire()
            self._cliquer_prendre()
            self._remplir_compte_rendu(subject, sender, body)
            self._remplir_qualification(subject)
            self._selectionner_en_cours()
            self._saisir_date_du_jour()
            self._cliquer_enregistrer()
            return True
        except Exception as exc:
            print(f"[MAEVA] Erreur lors du traitement de '{subject}': {exc}")
            return False

    def _naviguer_vers_formulaire(self) -> None:
        self._page.goto(self.app_url)
        self._page.wait_for_load_state("networkidle")

    def _cliquer_prendre(self) -> None:
        """Étape 1 — Cliquer sur le bouton 'Prendre'."""
        btn = self._page.locator("button:has-text('Prendre'), a:has-text('Prendre')").first
        btn.wait_for(state="visible", timeout=10_000)
        btn.click()
        self._page.wait_for_load_state("networkidle")

    def _remplir_compte_rendu(self, subject: str, sender: str, body: str) -> None:
        """Étape 2 — Remplir le champ Compte rendu."""
        contenu = f"Objet: {subject}\nDe: {sender}\n\n{body}"
        field = self._page.locator(
            "textarea[name*='compte'], textarea[placeholder*='compte rendu'], "
            "textarea[id*='compte'], [aria-label*='Compte rendu']"
        ).first
        field.wait_for(state="visible", timeout=10_000)
        field.fill(contenu)

    def _remplir_qualification(self, subject: str) -> None:
        """Étape 3 — Remplir le champ Qualification."""
        field = self._page.locator(
            "input[name*='qualif'], textarea[name*='qualif'], "
            "[aria-label*='Qualification'], [placeholder*='qualif']"
        ).first
        field.wait_for(state="visible", timeout=10_000)
        field.fill(subject)

    def _selectionner_en_cours(self) -> None:
        """Étape 4 — Sélectionner 'En cours' dans la liste déroulante de statut."""
        select = self._page.locator(
            "select[name*='statut'], select[name*='status'], "
            "select[id*='statut'], select[id*='status']"
        ).first
        select.wait_for(state="visible", timeout=10_000)
        select.select_option(label="En cours")

    def _saisir_date_du_jour(self) -> None:
        """Étape 5 — Saisir la date du jour."""
        today = date.today().strftime("%d/%m/%Y")
        field = self._page.locator(
            "input[type='date'], input[name*='date'], "
            "[aria-label*='date'], [placeholder*='date']"
        ).first
        field.wait_for(state="visible", timeout=10_000)
        # Tente d'abord le format natif HTML date (YYYY-MM-DD), puis le format FR
        try:
            field.fill(date.today().strftime("%Y-%m-%d"))
        except Exception:
            field.fill(today)

    def _cliquer_enregistrer(self) -> None:
        """Étape 6 — Cliquer sur 'Enregistrer'."""
        btn = self._page.locator(
            "button:has-text('Enregistrer'), input[value='Enregistrer'], "
            "button:has-text('Sauvegarder'), button[type='submit']"
        ).first
        btn.wait_for(state="visible", timeout=10_000)
        btn.click()
        self._page.wait_for_load_state("networkidle")
