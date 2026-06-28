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

### 1. **APIs officielles** (recommandé)
- **Amazon** : [Product Advertising API](https://developer.amazon.com/docs/product-advertising/getting-started.html)
- **Autres** : vérifier la documentation de chaque site

### 2. **Service de scraping proxy** (coûteux mais fiable)
- [ScraperAPI](https://www.scraperapi.com/) — gère Cloudflare + JavaScript
- [Bright Data](https://brightdata.com/) — réseau proxy résidentiel
- [Oxylabs](https://oxylabs.io/) — scraping avec rotation de proxies

### 3. **Navigateur headless** (JavaScript + interaction réelle)
- [Selenium](https://www.selenium.dev/) — WebDriver
- [Playwright](https://playwright.dev/) — moderne et rapide

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

