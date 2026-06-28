# Limitations et considérations de scraping

## Protections anti-bot

Certains sites e-commerce français utilisent des protections avancées :

| Site | Protection | Impact |
|------|-----------|--------|
| **Amazon** | WAF + rate-limit strict | ⚠️ Bloque les requêtes répétitives |
| **Darty** | Cloudflare + bot detection | ❌ 403 Forbidden même avec headers réalistes |
| **Leroy Merlin** | WAF (probablement Cloudflare) | ❌ 403 Forbidden |
| **ManoMano** | Bot detection | ❌ 403 Forbidden |
| **Boulanger** | Timeout + rate-limit | ⏱️ Réponses lentes |
| **Castorama** | WAF | ⚠️ Peut bloquer |

## Stratégies implémentées

✅ **Déjà en place** :
- Headers réalistes (User-Agent, Sec-Fetch-*, DNT, Referer)
- Sessions persistantes par domaine (cookies)
- Retries avec backoff exponentiel (3 tentatives)
- Délai aléatoire entre requêtes (1.5-3.5s)
- Timeout étendu (30s pour les sites lents)
- Gestion gracieuse des 403/429/503

⚠️ **Limites** :
- Impossible de contourner Cloudflare WAF + bot detection sans mesures extrêmes
- Pas d'exécution JavaScript (certains prix chargés dynamiquement)
- Pas de gestion des captchas

## Solutions avancées (non implémentées)

Pour une fiabilité maximale sur tous les sites :

### 1. **Navigateur headless Playwright** ✅ IMPLÉMENTÉ
- [Playwright](https://playwright.dev/) — moderne, rapide, cross-platform
- Exécute un vrai navigateur Chromium (contourne Cloudflare + JavaScript)
- Mode `--use-browser` disponible en CLI
- Plus lent (2-3x) mais très fiable
- À activer dans `.github/workflows/scan-and-publish.yml` si besoin

### 2. **APIs officielles** (recommandé si dispo)
- **Amazon** : [Product Advertising API](https://developer.amazon.com/docs/product-advertising/getting-started.html)
- **Autres** : vérifier la documentation de chaque site

### 3. **Service de scraping proxy** (coûteux mais fiable)
- [ScraperAPI](https://www.scraperapi.com/) — gère Cloudflare + JavaScript
- [Bright Data](https://brightdata.com/) — réseau proxy résidentiel
- [Oxylabs](https://oxylabs.io/) — scraping avec rotation de proxies


### 4. **Rotation de proxies** (anti-ban)
- [ProxyMesh](https://www.proxymesh.com/)
- [SmartProxy](https://smartproxy.com/)

## Recommandations

**Pour le développement personnel** ✅ :
- Utiliser la solution actuelle (headers + retries)
- Cibler les petits sites et marketplaces moins protégées
- Respecter `robots.txt` et ajouter des délais
- Monitorer les bloques et adapter les URLs cibles

**Pour un usage production** ⚠️ :
- Envisager une API officielle ou proxy scraping
- Accepter les délais de réponse plus longs
- Implementer une file d'attente avec notifications de blocage
- Tester en local avant de mettre en place sur GitHub Actions

**Légal** 📋 :
- Vérifier les CGU de chaque site
- Respecter le `robots.txt`
- Ne pas créer de charge serveur excessive
- Consulter un juriste si usage commercial

