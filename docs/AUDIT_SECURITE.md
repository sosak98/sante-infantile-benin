# Audit de sécurité — Santé Infantile Bénin

Audit du code de l'application (Django 6.0, déploiement Render).
Chaque point a été vérifié dans le code, corrigé le cas échéant, et couvert
par un test automatisé quand c'était possible.

---

## 1. Corrections apportées

### 1.1 Injection HTML (XSS) dans les infobulles de la carte — corrigé

**Où :** `sante/templates/sante/carte.html`, fonctions `popupContent()` et la
liste « 10 plus proches ».

**Problème :** les noms d'établissements étaient concaténés dans des chaînes
HTML puis injectés via `bindPopup()` / `innerHTML` :

```js
'<h6 ...>' + nom + '</h6>'
'<b>' + e.nom + '</b>'
```

Le passage par `json_script` protège la **sérialisation** des données, mais pas
leur **réinjection** dans du HTML côté navigateur. Or ces noms proviennent
d'OpenStreetMap (contributions ouvertes) et, depuis cette version, de saisies
d'agents de santé. Un nom contenant `<img src=x onerror=...>` s'exécutait chez
chaque visiteur affichant la carte.

**Correction :** ajout d'une fonction `echapper()` appliquée à toute valeur
issue des données (nom, adresse, téléphone, jours, horaire) avant insertion.
Les coordonnées sont forcées en nombres via `Number()`.

**Test :** `sante.tests.CarteAvecVaccinationTests.test_carte_echappe_les_noms`.

---

### 1.2 Panne totale du site si la librairie `groq` est indisponible — corrigé

**Où :** `sib_intelligence/views.py`.

**Problème :** `from groq import Groq` était exécuté au chargement du module.
Ce module est importé par `sib_intelligence/urls.py`, lui-même inclus dans
`santeinfantile/urls.py`. Une librairie absente, cassée ou incompatible faisait
donc échouer le chargement de **toute** la configuration d'URL : le site entier
renvoyait 500, y compris le calendrier vaccinal et les premiers secours, alors
que l'IA n'est qu'un module secondaire.

Ce scénario n'est pas théorique : `requirements.txt` épingle toutes les
dépendances sauf `groq` et `python-dotenv`, laissés sans version. Une version
majeure incompatible publiée sur PyPI suffit à casser le prochain déploiement.

**Correction :** l'import et l'instanciation du client sont déplacés dans une
fonction `_client_groq()` appelée à la demande, protégée par `try/except`.
L'absence de librairie ou de clé désactive uniquement le chat.

**Test :** `santeinfantile.tests.EnTetesSecuriteTests.test_module_ia_optionnel_ne_casse_pas_le_site`.

---

### 1.3 Erreur 500 sur date de naissance invalide — corrigé

**Où :** `conseils/views.py`, vue `calculer_rdv`.

**Problème :** `date.fromisoformat(request.POST.get('date_naissance'))` sans
garde. Toute valeur non conforme (champ vide, saisie manuelle, requête forgée)
levait `ValueError` et produisait une erreur 500. En production, une erreur 500
répétée pollue les journaux et peut servir de vecteur de déni de service peu
coûteux.

**Correction :** parsing protégé, message d'erreur affiché dans le formulaire,
refus des dates futures. Le même contrôle est appliqué aux dates de doses
reçues (une dose ne peut pas précéder la naissance ni être dans le futur) et au
planificateur de l'espace professionnels.

**Tests :** `conseils.tests.PagesVaccinationTests.test_rdv_refuse_une_date_invalide_sans_erreur_500`
et `test_rdv_refuse_une_naissance_future`.

---

### 1.4 Content-Security-Policy et Permissions-Policy absentes — ajoutées

**Où :** nouveau module `santeinfantile/middleware.py`.

**Problème :** Django pose `X-Content-Type-Options`, `Referrer-Policy`,
`X-Frame-Options` et HSTS, mais n'écrit ni CSP ni Permissions-Policy. Sans CSP,
rien ne limite l'origine des scripts chargés ni la destination des formulaires.

**Correction :** en-têtes ajoutés sur toutes les réponses.

```
default-src 'self'
script-src  'self' 'unsafe-inline' https://cdn.jsdelivr.net https://unpkg.com
style-src   'self' 'unsafe-inline' https://cdn.jsdelivr.net https://unpkg.com https://fonts.googleapis.com
font-src    'self' data: https://fonts.gstatic.com
img-src     'self' data: blob: <tuiles OSM et CARTO>
connect-src 'self' https://overpass-api.de
object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'self'
manifest-src 'self'; worker-src 'self'
```

```
Permissions-Policy: geolocation=(self), camera=(), microphone=(), payment=(),
                    usb=(), magnetometer=(), gyroscope=(), accelerometer=(),
                    interest-cohort=()
```

**Limite assumée :** `'unsafe-inline'` est nécessaire sur `script-src` et
`style-src`. Le site compte de nombreux scripts et attributs `style` en ligne
(carte Leaflet, menu, bandeaux) ; les interdire casserait les pages. La CSP
conserve malgré tout sa valeur : `default-src` verrouillé, plugins interdits,
`base-uri` et `form-action` restreints (un formulaire injecté ne peut pas
exfiltrer vers un domaine tiers), et pas d'inclusion en iframe étrangère.
Passer à une CSP à nonce demanderait de réécrire les gabarits : c'est le
chantier suivant, pas un correctif de cette livraison.

**Tests :** `santeinfantile.tests.EnTetesSecuriteTests` (6 tests).

---

### 1.5 Durcissement des cookies et des envois — ajouté

Dans `santeinfantile/settings.py` :

| Réglage | Valeur | Raison |
| --- | --- | --- |
| `SESSION_COOKIE_HTTPONLY` | `True` | Cookie de session illisible en JavaScript |
| `SESSION_COOKIE_SAMESITE` | `Lax` | Pas d'envoi lors d'une navigation tierce |
| `CSRF_COOKIE_SAMESITE` | `Lax` | Idem pour le jeton CSRF |
| `CSRF_COOKIE_HTTPONLY` | `False` | Volontaire : le JS du triage lit le jeton |
| `SECURE_HSTS_PRELOAD` | `True` en prod | Éligibilité à la liste de préchargement HSTS |
| `SECURE_CROSS_ORIGIN_OPENER_POLICY` | `same-origin` | Isolation du contexte de navigation |
| `DATA_UPLOAD_MAX_MEMORY_SIZE` | 5 Mio | Plafonne les corps de requête |
| `DATA_UPLOAD_MAX_NUMBER_FIELDS` | 500 | Limite les attaques par collision de hachage |

---

### 1.6 Contrôle d'accès du nouvel espace professionnels — conçu fermé

L'espace professionnels permet de modifier des informations **publiques** d'un
centre de santé (jours de vaccination, téléphone). Sans contrôle, n'importe qui
pourrait publier de faux horaires et envoyer des parents devant une porte
close — un risque sanitaire réel, pas seulement informatique.

Garde-fous mis en place :

1. Toute demande de compte est créée au statut `en_attente`. Ce statut ne donne
   accès qu'à une page d'information.
2. Le décorateur `pro_valide_requis` protège chaque vue métier et vérifie à la
   fois l'authentification, l'existence du profil et le statut `valide`.
3. Un agent ne peut modifier **que** l'établissement rattaché à son profil :
   le formulaire ne contient aucun champ de sélection d'établissement, et la
   vue charge l'instance depuis `pro.etablissement`. Un identifiant forgé dans
   la requête POST est sans effet.
4. La validation se fait dans l'administration Django (actions
   « Valider » / « Refuser »).

**Tests :** `pro.tests.AccesEspaceProTests` (9 tests) et
`pro.tests.DeclarationJoursTests.test_un_agent_ne_modifie_que_son_centre`.

---

### 1.7 Mot de passe administrateur en clair dans le code — corrigé

**Où :** `accounts/management/commands/createsuperuser_auto.py`.

**Problème :** la commande créait le compte `admin_sib` avec un mot de passe
écrit en dur dans le fichier source — donc visible dans le dépôt et dans tout
l'historique Git. Quiconque lit le code obtenait l'accès complet à
l'administration. Par ailleurs, les paquets `accounts/management/` et
`accounts/management/commands/` contenaient un fichier `_init_.py` (un seul
tiret bas de chaque côté) : la commande n'était trouvée que par chance, via
les paquets implicites de Python 3.

**Correction :**

- la commande lit désormais `DJANGO_SUPERUSER_USERNAME`,
  `DJANGO_SUPERUSER_EMAIL` et `DJANGO_SUPERUSER_PASSWORD` dans
  l'environnement ; elle **échoue explicitement** si la variable de mot de
  passe est absente, et le mot de passe fourni passe par `validate_password` ;
- la commande est idempotente (création au premier lancement, simple
  synchronisation ensuite) et est déclarée dans `render.yaml` et le
  `Procfile` ;
- les fichiers `_init_.py` sont renommés en `__init__.py` ;
- l'ancien mot de passe étant compromis par l'historique Git, il doit être
  **changé en production** : définir `DJANGO_SUPERUSER_PASSWORD` dans Render
  (déclarée en `sync: false` dans `render.yaml`) avec une nouvelle valeur
  forte, puis redéployer.

---

## 2. Points vérifiés et jugés corrects

| Point | Constat |
| --- | --- |
| Protection CSRF | Active partout, aucun `@csrf_exempt` dans le code |
| Injection SQL | Aucune requête brute : uniquement l'ORM |
| Requête Overpass | Coordonnées converties en `float` et bornées au Bénin |
| Limitation du chat IA | 30 messages / 5 min / IP, messages tronqués à 1500 caractères |
| Codes OTP | Générés avec `secrets`, comparés avec `hmac`, anti-rejeu en place |
| Mots de passe | Validateurs Django actifs, minimum 8 caractères côté espace pro |
| Secrets | Lus via `python-decouple`, aucun secret dans le dépôt |
| `.gitignore` | `.env`, `db.sqlite3`, `media/`, `.venv/` exclus |
| Zones privées | Exclues de `sitemap.xml` et interdites dans `robots.txt` |
| HSTS | 1 an, `includeSubDomains`, `preload` |

---

## 3. Avertissements `check --deploy` : pourquoi ils restent

```
python manage.py check --deploy
```

**W008 — `SECURE_SSL_REDIRECT` n'est pas à `True`.**
Render assure la terminaison TLS en amont. `SECURE_PROXY_SSL_HEADER` est
configuré, et HSTS (1 an, avec préchargement) force déjà les navigateurs en
HTTPS. Activer la redirection applicative alors que l'en-tête `X-Forwarded-Proto`
ne serait pas transmis correctement provoquerait une boucle de redirection et
rendrait le site inaccessible. Le réglage est laissé configurable par variable
d'environnement (`SECURE_SSL_REDIRECT=True`) pour être activé après
vérification des en-têtes du proxy.

**W009 — `SECRET_KEY` trop courte.**
N'apparaît que lorsqu'on lance la commande avec une clé de test en local. En
production, `render.yaml` déclare `SECRET_KEY` en `generateValue: true` :
Render produit une clé longue et aléatoire.

**W019 — `X_FRAME_OPTIONS` vaut `SAMEORIGIN` et non `DENY`.**
Valeur conservée pour permettre au site de s'afficher dans une iframe de sa
propre origine (aperçus internes). La CSP pose en complément
`frame-ancestors 'self'`, qui est la directive moderne et prioritaire dans les
navigateurs actuels. Le réglage est modifiable par variable d'environnement
(`X_FRAME_OPTIONS=DENY`).

---

## 4. Recommandations pour la suite

Classées par rapport valeur / effort. Aucune n'est bloquante.

1. **Épingler `groq` et `python-dotenv`** dans `requirements.txt`. Ce sont les
   deux seules dépendances sans version : un déploiement peut casser sans
   qu'aucun commit n'ait changé. *(Hors périmètre ici : consigne explicite de
   ne pas modifier `requirements.txt`.)*
2. **Servir les médias depuis un stockage objet.** `/media/<path>` passe par
   `django.views.static.serve`, prévu pour le développement. Django protège de
   la traversée de chemin, mais ce service n'est ni performant ni conçu pour la
   production.
3. **Limiter le rythme des demandes de compte professionnel**, sur le modèle du
   plafond déjà appliqué au chat, pour éviter la création massive de comptes.
4. **Passer la CSP aux nonces** en sortant les scripts en ligne des gabarits,
   ce qui permettra de supprimer `'unsafe-inline'`.
5. **Journaliser les modifications de fiches de centre** (qui a changé quoi,
   quand), utile en cas de publication erronée.

---

## 5. Couverture de tests

126 tests, tous verts.

| Module | Tests | Portée |
| --- | --- | --- |
| `conseils` | 38 | Calendrier PEV, normalisation des doses, planification, pages |
| `santeinfantile` | 35 | Routes, en-têtes de sécurité, service worker v9, 404, SEO |
| `pro` | 24 | Contrôle d'accès, inscription, déclaration des jours |
| `sante` | 21 | Jours de vaccination, page publique, carte, échappement |
| `accounts` | 8 | Tableau de bord parent, rappels vaccinaux |

```bash
python manage.py test
```
