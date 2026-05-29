# Bot MAEVA

Automatise le traitement des leads reçus par email dans le CRM Maeva (Salesforce).

## Ce que fait le bot

1. Se connecte à **Outlook Web** et scrute les emails non lus
2. Détecte les emails contenant un lien de lead Maeva (`renaultarca.my.site.com/NestSFA/s/lead/...`)
3. Pour chaque lead, exécute automatiquement la séquence :
   - **Prendre** — prend le lead
   - **Compte Rendu** — ouvre la modale
   - **Qualification** — sélectionne "En cours à recontacter"
   - **Date de relance** — saisit la date du jour
   - **Enregistrer** — valide

## Installation

```bash
pip install -r requirements.txt
playwright install chromium
```

## Configuration

```bash
cp .env.example .env
```

Remplir `.env` avec :

| Variable | Description |
|---|---|
| `OUTLOOK_EMAIL` | Ton adresse email Outlook |
| `OUTLOOK_PASSWORD` | Ton mot de passe Outlook |
| `CRM_URL` | `https://renaultarca.my.site.com/NestSFA` |
| `CRM_USERNAME` | Ton login CRM Maeva |
| `CRM_PASSWORD` | Ton mot de passe CRM Maeva |
| `POLLING_INTERVAL` | Intervalle en secondes (défaut : 60) |

## Lancement

```bash
python main.py
```

Le bot ouvre deux fenêtres navigateur (Outlook + CRM) et tourne en boucle.
Pour le faire tourner en arrière-plan sans fenêtre, passer `headless=True` dans `main.py`.
