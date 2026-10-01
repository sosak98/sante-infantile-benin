# Déploiement de Santé Infantile Bénin

Procédure réelle et vérifiable pour mettre le site en ligne sur Render.
Ce document remplace l'ancien `DEPLOIEMENT.md` de la racine, qui décrivait
l'étape 1 du projet et ne contenait pas de procédure de vérification.

---

## 0. À lire avant toute chose : l'environnement de travail est éphémère

Les sessions d'agent travaillent dans un bac à sable **recréé à neuf à chaque
fois** : le dépôt est re-cloné depuis `origin/main`. Rien de ce qui n'a pas été
**commité *et* poussé** ne survit à la fin d'une session — ni les fichiers
modifiés, ni les fichiers non suivis, ni les remises (`git stash`).

**Conséquence pratique :**

> Une session qui se termine sans `git push` a produit zéro travail conservé.
> Il n'y a pas de « travail en attente dans l'arbre de travail » à récupérer à
> la session suivante : `git status` y sera propre.

Pour vérifier en trois commandes si du travail existe réellement :

```bash
git status --porcelain --untracked-files=all   # modifications et fichiers non suivis
git stash list                                 # remises
git log --oneline origin/main..HEAD            # commits locaux non poussés
```

Si ces trois commandes ne renvoient rien, l'arbre est identique à `main` :
il n'y a rien à commiter, rien à pousser, et une pull request serait vide.

**Règle de fin de session : commiter et pousser, toujours.**

---

## 1. Ce que contient l'application

| Module | URL | Rôle |
| --- | --- | --- |
| Accueil | `/` | Présentation, accès aux six outils |
| Carte des structures | `/carte/` | 842 formations sanitaires géolocalisées |
| Jours de vaccination | `/carte/vaccination/` | Séances PEV par centre, filtrables par jour |
| Calendrier vaccinal | `/conseils/` | Calendrier PEV Bénin (24 doses) |
| Calculateur de RDV | `/conseils/rdv/` | Planning vaccinal personnalisé |
| Nutrition | `/conseils/nutrition/` | Conseils par âge |
| Dépistage | `/depistage/` | Z-scores OMS, MUAC |
| Premiers secours | `/premiers-secours/` | Signes de danger, gestes qui sauvent |
| Triage IA | `/triage/` | Orientation assistée (nécessite `GROQ_API_KEY`) |
| Espace professionnels | `/pro/` | Comptes agents de santé, publication des jours de vaccination |
| Espace parent | `/dashboard/` | Suivi des enfants et rappels vaccinaux |

Fichiers techniques servis à la racine : `/manifest.json`, `/sw.js`,
`/hors-ligne/`, `/robots.txt`, `/sitemap.xml`, `/llms.txt`, `/llms-full.txt`.

---

## 2. Variables d'environnement Render

| Variable | Valeur | Obligatoire |
| --- | --- | --- |
| `SECRET_KEY` | chaîne aléatoire de 50+ caractères | **oui** |
| `DEBUG` | `False` | **oui** |
| `ALLOWED_HOSTS` | `.onrender.com` (+ votre domaine) | **oui** |
| `CSRF_TRUSTED_ORIGINS` | `https://*.onrender.com` | **oui** |
| `DATABASE_URL` | fournie par la base PostgreSQL Render | **oui** |
| `GROQ_API_KEY` | clé Groq | non (désactive le triage IA) |
| `DJANGO_SUPERUSER_PASSWORD` | mot de passe du compte administrateur | **oui** (la commande `createsuperuser_auto` échoue sans elle) |
| `DJANGO_SUPERUSER_USERNAME` | identifiant administrateur (`admin_sib` par défaut) | non |
| `DJANGO_SUPERUSER_EMAIL` | courriel administrateur | non |
| `SECURE_SSL_REDIRECT` | `True` pour forcer HTTPS côté serveur | non |
| `CSP_FRAME_ANCESTORS` | `'self'` par défaut | non |

Le compte administrateur est créé/synchronisé au démarrage par
`python manage.py createsuperuser_auto` : le mot de passe ne vit **que** dans
l'environnement (jamais dans le code), il est validé par `validate_password`
et la commande est idempotente. Voir `docs/AUDIT_SECURITE.md` §1.7.

`render.yaml` déclare déjà tout cela (`SECRET_KEY` en `generateValue`).

Générer une clé :

```bash
python -c "import secrets; print(secrets.token_urlsafe(50))"
```

---

## 3. Déployer

Le déploiement est déclenché par un push sur `main`. Le `Procfile` et
`render.yaml` exécutent au démarrage :

```
python manage.py migrate
python manage.py seed
python manage.py seed_etablissements
python manage.py collectstatic --noinput
gunicorn santeinfantile.wsgi --bind 0.0.0.0:$PORT
```

**Les migrations tournent seules** : aucune commande manuelle n'est requise.
La migration `sante.0003_marquer_centres_vaccinateurs` renseigne
`fait_vaccination` sur les structures déjà en base (centres, hôpitaux,
hôpitaux de zone), sans quoi la page « Jours de vaccination » paraîtrait vide
après la mise à jour.

Ne pas modifier `requirements.txt` sans raison : Django 6.0.3 y est épinglé et
exige **Python ≥ 3.12** côté Render.

Séquence complète depuis une branche de travail :

```bash
git add -A
git commit -m "Description du lot"
git push origin <ma-branche>
gh pr create --base main --head <ma-branche> --title "..." --body "..."
gh pr merge --merge --delete-branch=false
# Render redéploie automatiquement (~3 à 6 minutes)
```

---

## 4. Vérification après mise en ligne

Remplacer `URL` par l'adresse du service, par exemple
`https://sante-infantile-benin.onrender.com`.

### 4.1 Toutes les pages répondent 200

```bash
URL=https://sante-infantile-benin.onrender.com
for p in / /a-propos/ /carte/ /carte/vaccination/ /depistage/ /conseils/ \
         /conseils/rdv/ /conseils/nutrition/ /premiers-secours/ /triage/ \
         /pro/ /pro/inscription/ /inscription/ /connexion/ /hors-ligne/ \
         /politique-de-confidentialite/ /politique-des-cookies/ /cgu/ \
         /robots.txt /sitemap.xml /llms.txt /llms-full.txt /manifest.json /sw.js; do
  printf '%s  %s\n' "$(curl -s -o /dev/null -w '%{http_code}' "$URL$p")" "$p"
done
```

Attendu : `200` partout.

### 4.2 Zones privées protégées

```bash
for p in /dashboard/ /profil/ /pro/tableau-de-bord/ /pro/mon-centre/ /pro/outil-pev/; do
  printf '%s  %s\n' "$(curl -s -o /dev/null -w '%{http_code}' "$URL$p")" "$p"
done
```

Attendu : `302` (redirection vers la connexion), jamais `200`.

### 4.3 En-têtes de sécurité

```bash
curl -sI "$URL/" | grep -iE 'content-security-policy|permissions-policy|strict-transport|x-content-type|referrer-policy|x-frame-options'
```

Attendu :

- `Content-Security-Policy` contenant `default-src 'self'`, `object-src 'none'`,
  `base-uri 'self'`, `form-action 'self'`, `frame-ancestors 'self'`
- `Permissions-Policy` contenant `geolocation=(self)`, `camera=()`, `microphone=()`
- `Strict-Transport-Security: max-age=31536000; includeSubDomains; preload`
- `X-Content-Type-Options: nosniff`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `X-Frame-Options: SAMEORIGIN`

### 4.4 Service worker en v10

```bash
curl -s "$URL/sw.js" | grep -E "const VERSION|'/carte/vaccination/'"
curl -sI "$URL/sw.js" | grep -i cache-control
```

Attendu : `const VERSION = 'v10';`, la présence de `/carte/vaccination/` dans la
liste `CORE`, et `Cache-Control: no-cache, no-store, must-revalidate`.

Incrémenter `SW_VERSION` dans `santeinfantile/pwa.py` à **chaque** modification
du service worker : c'est ce qui purge le cache des visiteurs déjà installés.

### 4.5 Page 404 en français

```bash
curl -s -o /dev/null -w '%{http_code}\n' "$URL/page-qui-nexiste-pas/"
curl -s "$URL/page-qui-nexiste-pas/" | grep -o 'Page introuvable'
```

Attendu : code `404` et le titre français « Page introuvable ».

### 4.6 Calendrier PEV à jour

```bash
curl -s "$URL/conseils/" | grep -oE 'Rotavirus 1|VPI \(polio injectable\)|Antipaludique 1'
```

Attendu : les trois libellés. Leur absence signale un déploiement resté sur
l'ancienne version.

---

## 5. Tests avant de pousser

```bash
python manage.py test          # 126 tests
python manage.py check --deploy
```

`check --deploy` remonte trois avertissements attendus et documentés dans
[`AUDIT_SECURITE.md`](AUDIT_SECURITE.md) (W008, W009, W019).

---

## 6. En cas de problème

| Symptôme | Cause probable | Action |
| --- | --- | --- |
| 500 sur toutes les pages | `SECRET_KEY` ou `DATABASE_URL` absente | Vérifier les variables Render |
| Page « Jours de vaccination » vide | migration `sante.0003` non appliquée | Consulter les logs de déploiement |
| Carte sans points | `seed_etablissements` non exécuté | `python manage.py seed_etablissements` dans le Shell Render |
| Anciennes pages affichées | service worker en cache | Vérifier que `SW_VERSION` a bien été incrémentée |
| Triage IA indisponible | `GROQ_API_KEY` absente | Normal : le reste du site fonctionne |
| Statiques manquants | `collectstatic` en échec | Consulter les logs de build |
