# Bot MAEVA

Automatise le traitement des emails entrants via Microsoft Graph API + Playwright.

## Séquence exécutée pour chaque email non lu

1. **Prendre** — clic sur le bouton « Prendre » dans l'app web
2. **Compte rendu** — remplit le champ avec l'objet, l'expéditeur et le corps du mail
3. **Qualification** — remplit le champ avec l'objet du mail
4. **En cours** — sélectionne « En cours » dans la liste déroulante de statut
5. **Date du jour** — saisit la date du jour automatiquement
6. **Enregistrer** — soumet le formulaire

## Stack

- Python 3.11+
- [Playwright](https://playwright.dev/python/) — automatisation navigateur
- [Microsoft Graph API](https://learn.microsoft.com/graph) via MSAL — lecture des emails

## Installation

```bash
pip install -r requirements.txt
playwright install chromium
```

## Configuration

```bash
cp .env.example .env
# Éditer .env avec vos valeurs
```

### Variables requises

| Variable | Description |
|---|---|
| `AZURE_CLIENT_ID` | ID de l'application Azure AD |
| `AZURE_CLIENT_SECRET` | Secret de l'application Azure AD |
| `AZURE_TENANT_ID` | ID du tenant Azure AD |
| `MAIL_USER` | Adresse email surveillée |
| `APP_URL` | URL de l'application web cible |
| `APP_USERNAME` | Login de l'app web |
| `APP_PASSWORD` | Mot de passe de l'app web |
| `POLLING_INTERVAL` | Intervalle de polling en secondes (défaut : 60) |

### Permissions Azure AD requises (application)

- `Mail.Read`
- `Mail.ReadWrite` (pour marquer les emails comme lus)

## Lancement

```bash
python main.py
```

## Adaptation des sélecteurs

Les sélecteurs CSS dans `maeva_bot.py` sont des sélecteurs génériques.
Inspecte l'app web cible et ajuste-les dans chaque méthode `_etape_*` si nécessaire.
