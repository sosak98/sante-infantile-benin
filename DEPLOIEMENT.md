# 🚀 Étape 1 — Mise à niveau & déploiement

## Ce qui a été fait

### 1. Fondations
- **`settings.py` complet & moderne** : secrets lus depuis les variables d'environnement
  (`python-decouple`), base de données via `dj-database-url` (PostgreSQL en prod, SQLite en dev),
  Whitenoise pour les statiques, `AUTH`/`LOGIN_URL` câblés.
- **`accounts/models.py`** : ajout du modèle `Parent` (profil lié à `User`) qui était référencé
  partout mais absent. Migration `0005` générée (ajoute aussi `Profile` et `PhoneOTP`).
- **`accounts/forms.py`** : ajout de `ParentRegisterForm` (inscription par téléphone).
- **`accounts/views.py`** : ajout de `accueil`, `register`, `login_view`, `logout_view`,
  `profil`/`profile_edit`, `ajouter_enfant` + `dashboard` robustifié.
- **Routing corrigé** : `main.urls` (inexistant) remplacé par les vraies apps.
  - `/` → accueil · `/a-propos/` · `/dashboard/` · `/profil/` · `/inscription/` · `/connexion/` · `/deconnexion/`
  - `/carte/` (santé) · `/depistage/` (enfants) · `/conseils/` + `/conseils/rdv/` + `/conseils/nutrition/` · `/triage/`
- **Sécurité** : `/carte/charger-seeds/` réservé au staff (plus de `@csrf_exempt` public) ;
  client IA Groq rendu **optionnel** (plus de crash si la clé est absente).

### 2. Design system (validé)
- **`templates/base.html`** unique (nav + footer + alertes) hérité par toutes les pages.
- **`static/css/sib.css`** : palette teal + ambre, boutons, cartes, formulaires, timeline, tableaux.
- **Refonte complète** des 18 templates (accueil, dashboard, carte, dépistage, calendrier, RDV,
  nutrition, triage, résultat, profil, ajout enfant, login, register, à propos, OTP…).
- **Logo compressé** (2,2 Mo → 18 Ko) + **photo de profil** intégrée.

### 3. PWA (le site devient une appli installable)
- **`manifest.json`** + **`sw.js`** servis à la racine (`santeinfantile/pwa.py`).
- Icônes 192/512 + apple-touch générées depuis le logo.
- Service worker enregistré dans `base.html` : cache-first pour les assets, réseau d'abord
  pour les pages (consultation hors-ligne des pages déjà visitées).

## Déploiement sur Render

1. **Variables d'environnement** (Render → Environment) :
   - `SECRET_KEY` (longue chaîne aléatoire)
   - `DEBUG=False`
   - `ALLOWED_HOSTS=.onrender.com` (ou votre domaine)
   - `GROQ_API_KEY` (votre clé Groq pour l'IA)
   - `DATABASE_URL` (fournie automatiquement par Render si vous créez une base PostgreSQL)
2. **Build/Start** : le `Procfile` exécute désormais `migrate && collectstatic --noinput && gunicorn`.
3. **En local** : copiez `.env.example` → `.env`, renseignez les valeurs, puis
   `pip install -r requirements.txt && python manage.py migrate && python manage.py runserver`.

## À venir (étapes suivantes)
- Étape 2 : vraies courbes OMS (LMS / percentiles) + graphique d'évolution de croissance.
- Étape 3 : rappels WhatsApp, domaine `.bj`, témoignages, contenu/blog.
