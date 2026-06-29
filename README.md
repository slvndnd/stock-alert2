# Stock Alert Dashboard

Projet Python qui scanne une liste configurable de produits sur plusieurs sites e-commerce, puis publie une page HTML consultable (GitHub Pages) avec les statuts, prix, liens et disponibilites.

## Fonctionnalites

- Scan multi-sites (Amazon, Darty, Boulanger, Leroy Merlin, Castorama, ManoMano, ou autres)
- Configuration YAML des produits, aliases de noms et URLs cibles
- Extraction automatique du titre, prix et disponibilite (schema.org + fallback texte)
- Dashboard HTML responsive avec icones de statut
- Workflow GitHub Actions planifie toutes les 2 heures
- **Alerte email automatique** lorsqu'un produit passe en stock

## Structure

- `src/stock_alert/` : logique applicative (chargement config, scan, parsing, rendu)
- `config/sites.yaml` : catalogue des sites (label + icone)
- `config/watchlist.yaml` : liste des produits, aliases et URLs a scanner
- `templates/index.html.j2` : template du dashboard
- `.github/workflows/scan-and-publish.yml` : CI planifiee + publication GitHub Pages
- `tests/` : tests unitaires

## Prerequis

- Python 3.10+

## Installation locale

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Lancer un scan local

```bash
PYTHONPATH=src python -m stock_alert.cli \
  --sites config/sites.yaml \
  --watchlist config/watchlist.yaml \
  --json-out docs/latest.json \
  --html-out docs/index.html
```

La page generee est `docs/index.html`.

### Mode Playwright (fallback hybride)

Tu peux activer un mode hybride : tentative HTTP classique d'abord, puis retry Playwright uniquement pour les pages bloquées.

```bash
# D'abord installer Playwright (optionnel)
pip install playwright
python -m playwright install chromium

# Ensuite lancer le scan avec fallback Playwright
PYTHONPATH=src python -m stock_alert.cli \
  --sites config/sites.yaml \
  --watchlist config/watchlist.yaml \
  --json-out docs/latest.json \
  --html-out docs/index.html \
  --use-browser
```

⚠️ **Note** : ce mode est plus lent mais evite de degrader les sites qui fonctionnent deja en HTTP.

Dans GitHub Actions, le scan planifie (toutes les 2h) reste en HTTP par defaut.
Pour activer Playwright ponctuellement, lance `Run workflow` puis coche l'input `use_browser`.

### Mode ScraperAPI (fallback proxy anti-blocage)

Pour les sites qui restent bloques en 403 (Darty, Leroy Merlin, ManoMano), active un fallback ScraperAPI.

```bash
export SCRAPERAPI_KEY=ta_cle_scraperapi
export SCRAPERAPI_COUNTRY_CODE=fr   # optionnel, defaut: fr
export SCRAPERAPI_RENDER=false      # optionnel, true si besoin JS

PYTHONPATH=src python -m stock_alert.cli \
  --sites config/sites.yaml \
  --watchlist config/watchlist.yaml \
  --json-out docs/latest.json \
  --html-out docs/index.html \
  --use-scraperapi
```

Tu peux combiner les deux fallbacks:

```bash
PYTHONPATH=src python -m stock_alert.cli \
  --sites config/sites.yaml \
  --watchlist config/watchlist.yaml \
  --json-out docs/latest.json \
  --html-out docs/index.html \
  --use-scraperapi \
  --use-browser
```

## Lancer les tests

```bash
PYTHONPATH=src python -m pytest
```

## Configuration

### Produits (`config/watchlist.yaml`)

- `display_name` : nom affiche dans le dashboard
- `names` : aliases pour matcher le produit
- `targets` : liste des sites/URLs a scanner

Exemple minimal:

```yaml
products:
  - id: steamdeck
    display_name: Steam Deck OLED
    names: ["Steam Deck OLED", "Valve Steam Deck"]
    targets:
      - site: amazon
        url: https://www.amazon.fr/...
      - site: darty
        url: https://www.darty.com/...
```

### Sites (`config/sites.yaml`)

Associe un identifiant de site, un label, une icone et une strategie de fetch par site (`fetch_mode`):

- `requests` : HTTP classique (rapide, stable)
- `scraperapi` : proxy anti-blocage via ScraperAPI
- `browser` : Playwright (fallback navigateur)
- `auto` : requests puis fallback selon les flags CLI

```yaml
sites:
  - id: amazon
    label: Amazon
    icon: "🟧"
    fetch_mode: requests
```

Recommandation pratique:
- `amazon`, `boulanger`, `castorama` -> `requests`
- `darty`, `leroy_merlin`, `manomano` -> `scraperapi`

Cela evite les regressions du type HTTP 400 sur Boulanger en mode navigateur.

## Gestion des sites anti-bot (Darty, Leroy Merlin, ManoMano)

Ces sites utilisent des protections WAF (Cloudflare) qui bloquent tout scraping, même avec Playwright ou proxy.

**Solution pragmatique** :

1. **Accepter "Accès bloqué"** dans le dashboard (c'est honnête)
2. **Utiliser idealo.fr** comme comparateur centralisé (gratuit, avec alertes email natives)
3. **Remplacer les URLs** dans `config/watchlist.yaml` par des liens idealo.fr (optionnel)

### Remplacer par idealo.fr (optionnel)

```bash
python3 find_idealo_url.py "Climatiseur Midea PortaSplit"
```

Puis copie l'URL générée dans `config/watchlist.yaml` pour les sites bloqués:

```yaml
products:
  - id: midea-portasplit
    display_name: Midea PortaSplit
    names: [...]
    targets:
      - site: darty
        url: https://www.idealo.fr/search.html?q=Midea+PortaSplit+climatiseur
      # ... ou removerl'entrée si tu n'en as pas besoin
```

### Alternative : enlever les sites bloqués

Simplement supprime les entrées `darty`, `leroy_merlin`, `manomano` de ta watchlist si tu ne veux pas les voir "Accès bloqué".

## GitHub Actions + GitHub Pages

1. Pousser le projet sur GitHub.
2. Dans `Settings > Pages`, choisir `GitHub Actions` comme source.
3. Le workflow `.github/workflows/scan-and-publish.yml` s'executera:
   - manuellement (`workflow_dispatch`)
   - automatiquement toutes les 2 heures (`cron: 0 */2 * * *`)

En `workflow_dispatch`, tu peux cocher:
- `use_scraperapi` pour activer le fallback ScraperAPI
- `use_browser` pour activer le fallback Playwright

Pour changer la frequence, modifier directement la ligne `cron` du workflow.

## Alertes email

Les alertes sont envoyees par email quand un produit passe en stock.
Par defaut, une seule alerte est envoyee par transition (pas de spam toutes les 2h si le produit est deja connu en stock).

### Configurer les secrets GitHub

Dans `Settings > Secrets and variables > Actions`, ajouter:

| Secret | Description | Exemple |
|---|---|---|
| `SMTP_HOST` | Serveur SMTP | `smtp.gmail.com` |
| `SMTP_PORT` | Port SMTP (optionnel, defaut 587) | `587` |
| `SMTP_USER` | Adresse email expediteur | `moncompte@gmail.com` |
| `SMTP_PASSWORD` | Mot de passe application SMTP | `xxxx xxxx xxxx xxxx` |
| `ALERT_EMAIL_TO` | Destinataire de l'alerte | `moi@gmail.com` |
| `SCRAPERAPI_KEY` | Cle API ScraperAPI | `scraperapi_xxx` |

Variables optionnelles (`Actions > Variables`):

| Variable | Description | Exemple |
|---|---|---|
| `SCRAPERAPI_COUNTRY_CODE` | Pays proxy ScraperAPI (defaut `fr`) | `fr` |
| `SCRAPERAPI_RENDER` | Rendu JS ScraperAPI (`true`/`false`) | `false` |

> **Gmail** : utiliser un [mot de passe d'application](https://myaccount.google.com/apppasswords) (pas le mot de passe principal).
> Activer d'abord la validation en deux etapes sur le compte Google.

### Tester les alertes localement

```bash
export SMTP_HOST=smtp.gmail.com
export SMTP_USER=moncompte@gmail.com
export SMTP_PASSWORD=xxxx
export ALERT_EMAIL_TO=moi@gmail.com

PYTHONPATH=src python -m stock_alert.cli \
  --sites config/sites.yaml \
  --watchlist config/watchlist.yaml \
  --json-out docs/latest.json \
  --html-out docs/index.html \
  --always-alert   # Force l'envoi meme si l'etat n'a pas change
```

## Limites et recommandations

- Certains sites changent souvent leur HTML ou bloquent les bots; verifier regulierement la qualite des extractions.
- Respecter les CGU des sites cibles et leur `robots.txt`.
- Pour un usage intensif, envisager des parsers dedies par site et un proxy anti-blocage.

**Voir aussi** : [SCRAPING_LIMITS.md](docs/SCRAPING_LIMITS.md) pour une analyse détaillée des protections anti-bot par site et les solutions avancées.

