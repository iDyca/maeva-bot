import os
from datetime import date
from playwright.sync_api import Page


class MaevaBot:
    """Automatise la séquence sur un lead du CRM Maeva (Salesforce Experience Cloud)."""

    def __init__(self, page: Page):
        self._page = page
        self.crm_url = os.environ["CRM_URL"]

    def login(self) -> None:
        username = os.environ["CRM_USERNAME"]
        password = os.environ["CRM_PASSWORD"]

        self._page.goto(f"{self.crm_url}/s/login")
        self._page.wait_for_load_state("networkidle")

        self._page.fill("input[name='username'], input[type='email']", username)
        self._page.fill("input[name='password'], input[type='password']", password)
        self._page.click("button[type='submit'], input[type='submit']")
        self._page.wait_for_load_state("networkidle")

    def traiter_lead(self, lead_url: str) -> bool:
        """Exécute la séquence complète sur un lead. Retourne True si succès."""
        try:
            self._ouvrir_lead(lead_url)
            self._cliquer_prendre()
            self._ouvrir_compte_rendu()
            self._selectionner_qualification()
            self._saisir_date_du_jour()
            self._cliquer_enregistrer()
            return True
        except Exception as exc:
            print(f"[MAEVA] Erreur sur {lead_url}: {exc}")
            return False

    def _ouvrir_lead(self, lead_url: str) -> None:
        self._page.goto(lead_url)
        self._page.wait_for_load_state("networkidle")
        # Attendre que les boutons d'action soient visibles
        self._page.wait_for_selector("button:has-text('Prendre')", timeout=15_000)

    def _cliquer_prendre(self) -> None:
        """Étape 1 — Cliquer sur le bouton 'Prendre'."""
        btn = self._page.locator("button:has-text('Prendre')").first
        btn.click()
        self._page.wait_for_load_state("networkidle")
        # Parfois une confirmation apparaît
        confirm = self._page.locator("button:has-text('OK'), button:has-text('Confirmer')").first
        if confirm.is_visible():
            confirm.click()
            self._page.wait_for_load_state("networkidle")

    def _ouvrir_compte_rendu(self) -> None:
        """Étape 2 — Cliquer sur 'Compte Rendu' pour ouvrir la modale."""
        btn = self._page.locator("button:has-text('Compte Rendu'), button:has-text('Compte rendu')").first
        btn.wait_for(state="visible", timeout=10_000)
        btn.click()
        # Attendre l'ouverture de la modale
        self._page.wait_for_selector("text=QUALIFICATION", timeout=10_000)

    def _selectionner_qualification(self) -> None:
        """Étape 3 — Sélectionner 'En cours à recontacter' dans le dropdown Qualification."""
        # Les dropdowns Salesforce LWC sont des combobox custom
        combo = self._page.locator(
            "div.modal-container lightning-combobox:has(label:has-text('QUALIFICATION')) button, "
            "div[role='dialog'] lightning-combobox:has(label:has-text('Qualification')) button"
        ).first

        if not combo.is_visible():
            # Fallback : chercher le premier combobox de la modale
            combo = self._page.locator("div[role='dialog'] button[aria-haspopup='listbox']").first

        combo.click()
        self._page.wait_for_selector("lightning-base-combobox-item, span[role='option']", timeout=5_000)

        option = self._page.locator(
            "lightning-base-combobox-item:has-text('En cours à recontacter'), "
            "span[role='option']:has-text('En cours à recontacter')"
        ).first
        option.click()

    def _saisir_date_du_jour(self) -> None:
        """Étape 4 — Saisir la date du jour dans DATE DE RELANCE."""
        today = date.today().strftime("%d/%m/%Y")

        # Le champ date dans les modales Salesforce LWC
        date_input = self._page.locator(
            "div[role='dialog'] input[placeholder*='jj/mm/aaaa'], "
            "div[role='dialog'] input[placeholder*='dd/mm/yyyy'], "
            "div[role='dialog'] lightning-datepicker input"
        ).first

        date_input.wait_for(state="visible", timeout=8_000)
        date_input.click()
        date_input.fill(today)
        # Fermer le calendrier en appuyant sur Escape ou Tab
        date_input.press("Escape")

    def _cliquer_enregistrer(self) -> None:
        """Étape 5 — Cliquer sur 'Enregistrer' dans la modale."""
        btn = self._page.locator(
            "div[role='dialog'] button:has-text('Enregistrer')"
        ).first
        btn.wait_for(state="visible", timeout=8_000)
        btn.click()
        self._page.wait_for_load_state("networkidle")
        # Attendre la fermeture de la modale
        self._page.wait_for_selector("div[role='dialog']", state="hidden", timeout=10_000)
