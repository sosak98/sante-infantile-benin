# Santé Infantile Bénin — Améliorations (carte nationale + sécurité + SEO)

Livraison du 10 septembre 2026. Tout a été testé avec Django : `manage.py check` = 0 erreur,
la carte s'affiche avec 842 structures, les coordonnées pourries sont bloquées, robots.txt
et sitemap.xml répondent 200.

## 1. Ce qui a changé et pourquoi

### A. Carte nationale (ta demande n°1)
- **842 formations sanitaires du Bénin** chargées en une commande (hôpitaux, centres,
  pharmacies, cliniques) depuis le fichier embarqué `sante/data/formations_sanitaires_bj.json`.
  Avant : le seed ne couvrait que Cotonou.
- La carte marche maintenant dès l'installation, **sans appel extérieur** : la base locale
  est servie en priorité, OpenStreetMap n'est appelé qu'en complément si une zone est vide.
- Option `--osm` pour enrichir en direct sur TOUT le territoire (l'ancienne requête
  était limitée à Cotonou). Détection des doublons : relancer la commande ne duplique rien.
- **Route publique `carte/charger-seeds/` supprimée** : n'importe qui pouvait marteler
  l'API externe à travers ton site.

### B. Sécurité (7 failles corrigées)
1. **Injection XSS sur la carte** : les noms venant d'OpenStreetMap étaient injectés bruts
   dans le HTML (`|safe`). Un nom piégé pouvait exécuter du JavaScript chez les visiteurs.
   Remplacé par `json_script` (échappement automatique Django).
2. **Formulaire /chat sans protection CSRF** (`@csrf_exempt`) : n'importe quel site pouvait
   envoyer des requêtes au nom de tes visiteurs et brûler ton quota Groq (payant). Retiré ;
   le token CSRF est déjà envoyé par ton JavaScript, rien ne change pour les vrais visiteurs.
3. **Chat sans limite** ajout d'un plafond : 30 messages / 5 minutes / IP, et messages
   coupés à 1500 caractères. Les erreurs internes (clé, modèle) ne sont plus affichées
   en clair aux visiteurs.
4. **Code OTP prévisible** : généré avec `random` (prédictible) et comparé en clair.
   Passé à `secrets` (imprévisible) + comparaison `hmac`. + anti-spam : 5 codes max /
   10 minutes par numéro (évite la facture SMS Twilio en cas d'attaque).
5. **Pièce jointe proxy carte exposée** : lat/lng étaient interpolés dans la requête
   OpenStreetMap sans validation. Maintenant : valeurs forcées en nombres bornés au Bénin
   + mise en cache 6 h par zone.
6. **En-têtes HTTPS manquants en production** (Render fait le TLS devant ton appli) :
   ajout du bloc sécurité dans `settings.py` (HSTS, cookies sécurisés, redirection HTTPS,
   X-Frame-Options...). Actif automatiquement quand `DEBUG=False`.
7. **`.venv/` commité (115 Mo dans Git !)** : le `.gitignore` contenait `venv/` mais pas
   `.venv/`. Corrigé + commandes de nettoyage ci-dessous.

### C. SEO
- `robots.txt` et `sitemap.xml` servis par Django (zones privées exclues).
- Balises Open Graph complétées (`og:url`, `og:image` = ton logo, `og:locale` fr_BJ),
  Twitter Card, URL canonique sur toutes les pages, `theme-color` passé à ton vert #00695c.

### D. Ménage
Supprimés : `procfile` (doublon de Procfile), `data.json` (vide), `accounts/view.py`
(15 lignes orphelines), l'ancien script de seed racine, `carte_backup.html`, `.venv/`.

## 2. Installation sur ton PC (5 minutes)

```bash
cd ~/chemin/vers/sante-infantile-benin        # ton vrai dossier local
unzip -o ~/Téléchargements/sib-ameliorations.zip

# sortir le .venv de l'historique Git (115 Mo !)
git rm -r --cached .venv
git rm --cached data.json

# enregistrer
git add -A
git commit -m "Carte nationale (842 structures) + correctifs sécurité + SEO"
git push
```

Le `git push` redéploie automatiquement sur Render. Une fois déployé, une seule action :

**Shell Render** (Render > ton service > Shell) :
```bash
python manage.py seed_etablissements
```

## 3. À vérifier une fois sur Render (2 minutes)

1. Render > Environment : la variable `SECRET_KEY doit exister` (sinon le site tourne
   en prod sur la clé de développement). Si absente : génère-en une avec
   `python -c "import secrets; print(secrets.token_urlsafe(50))"` et colle-la dans Render.
2. Ouvre `https://sante-infantile.onrender.com/carte/` : tu dois voir des centaines de
   points sur tout le pays (plus seulement Cotonou).
3. Ouvre `https://sante-infantile.onrender.com/robots.txt` : il répond.
4. Option : soumets `https://sante-infantile.onrender.com/sitemap.xml` dans Google
   Search Console pour accélérer le référencement.

## 4. Commandes utiles après

```bash
python manage.py seed_etablissements          # re-seed (sans doublons)
python manage.py seed_etablissements --osm    # + enrichissement live OSM (lent, ~2 min)
python manage.py check --deploy               # audit sécurité Django (attendu : seulement des warnings explicables)
```

## Fichiers livrés

```
santeinfantile/settings.py    + bloc en-têtes sécurité prod
santeinfantile/urls.py        + robots.txt + sitemap.xml
santeinfantile/seo.py         (nouveau) robots + sitemap
sante/views.py                réécrit : validation + cache + local-first
sante/urls.py                 - route publique charger-seeds
sante/management/commands/seed_etablissements.py   réécrit : national, fichier + --osm
sante/data/formations_sanitaires_bj.json           (nouveau) 961 structures OSM
sante/templates/sante/carte.html  |safe -> json_script (anti-XSS)
accounts/views.py             OTP : secrets + hmac + anti-spam 5/10min
sib_intelligence/views.py     - csrf_exempt, + rate-limit chat, erreurs génériques
templates/base.html           OG complet, Twitter, canonical, robots, theme-color
.gitignore                    + .venv/ media/ .idea/ .vscode/ db.sqlite3
```
