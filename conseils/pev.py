"""Calendrier vaccinal du PEV Bénin : référence unique du projet.

Ce module est la **seule** source de vérité sur le calendrier vaccinal. Il est
utilisé par :

- la page publique « Calendrier vaccinal » (`conseils.views.calendrier_vaccinal`)
- le calculateur de rendez-vous (`conseils.views.calculer_rdv`)
- le tableau de bord parent (`accounts.views.dashboard`)
- l'espace professionnels de santé (`pro.views`)
- la commande de peuplement `manage.py seed`

Avant, `pev.py` et `seed_vaccins.py` décrivaient deux calendriers **différents**
(notamment pour le vaccin antipaludique), et les libellés enregistrés dans
`VaccinRecu` ne correspondaient pas aux clés du planificateur : une dose saisie
n'était donc jamais reconnue comme reçue. Tout est désormais unifié ici.

Sources (calendrier de routine, Bénin) :

- PEV Bénin / DNPEV-SSP : BCG + VPO-0 à la naissance ; Penta, VPO et PCV-13 à
  6, 10 et 14 semaines ; VAR et VAA à 9 mois.
- Rotavirus : introduit nationalement en décembre 2019 (ROTAVAC, schéma à
  3 doses calé sur Penta 1-2-3).
- VPI (polio inactivé injectable) : 1 dose à 14 semaines, conformément au
  schéma OMS de retrait progressif du VPO.
- Vaccin antipaludique RTS,S/AS01 : introduit dans le PEV en avril 2024 ;
  3 doses à 6, 7 et 9 mois puis un rappel à 18 mois.
- 2ᵉ dose rougeole-rubéole (VAR-2) : introduite en décembre 2024, à 18 mois
  (la 1ʳᵉ dose restant à 9 mois).
- Vitamine A : supplémentation semestrielle de 6 à 59 mois (voir SUPPLEMENTATIONS,
  ce n'est pas un vaccin et elle n'entre pas dans le planning vaccinal).
"""

from datetime import date, timedelta

# Intervalle minimal réglementaire entre deux doses d'une même série.
INTERVALLE_MIN_SEMAINES = 4

# Âge maximal de rattrapage du PEV : le programme cible les enfants de 0 à 59 mois.
AGE_LIMITE_RATTRAPAGE_MOIS = 59


# ---------------------------------------------------------------------------
# Le calendrier de référence
# ---------------------------------------------------------------------------
# Chaque entrée décrit UNE dose. Champs :
#   cle       : identifiant stable, utilisé en base (VaccinRecu.nom_vaccin)
#   nom       : libellé court affiché
#   dose      : numéro de dose dans la série (1 si dose unique)
#   serie     : identifiant de la série (pour l'intervalle minimal entre doses)
#   semaines  : âge cible en semaines (exclusif avec `mois`)
#   mois      : âge cible en mois calendaires (exclusif avec `semaines`)
#   affichage : libellé de l'âge tel qu'il figure sur le carnet
#   maladies  : ce contre quoi la dose protège
#   voie      : voie et site d'administration
#   obligatoire : True pour le PEV de routine
CALENDRIER_PEV = [
    # --- Naissance ---------------------------------------------------------
    {
        'cle': 'bcg', 'nom': 'BCG', 'dose': 1, 'serie': 'bcg',
        'semaines': 0, 'affichage': 'Naissance',
        'maladies': 'Tuberculose',
        'voie': 'Intradermique, bras droit',
        'description': "Protège contre les formes graves de la tuberculose "
                       "(méningite tuberculeuse, tuberculose miliaire).",
        'obligatoire': True,
    },
    {
        'cle': 'vpo_0', 'nom': 'VPO 0', 'dose': 1, 'serie': 'vpo_naissance',
        'semaines': 0, 'affichage': 'Naissance',
        'maladies': 'Poliomyélite',
        'voie': 'Orale, 2 gouttes',
        'description': "Dose « zéro » de vaccin polio oral, administrée dans "
                       "les 14 jours suivant la naissance.",
        'obligatoire': True,
    },
    {
        'cle': 'hepb_0', 'nom': 'Hépatite B (dose naissance)', 'dose': 1,
        'serie': 'hepb_naissance',
        'semaines': 0, 'affichage': 'Naissance',
        'maladies': 'Hépatite B',
        'voie': 'Intramusculaire, cuisse',
        'description': "Dose de naissance contre l'hépatite B, idéalement dans "
                       "les 24 heures. Les doses suivantes sont incluses dans "
                       "le Pentavalent.",
        'obligatoire': True, 'maternite': True,
    },

    # --- 6 semaines --------------------------------------------------------
    {
        'cle': 'penta_1', 'nom': 'Pentavalent 1', 'dose': 1, 'serie': 'penta',
        'semaines': 6, 'affichage': '6 semaines',
        'maladies': 'Diphtérie, tétanos, coqueluche, hépatite B, Haemophilus influenzae b',
        'voie': 'Intramusculaire, face externe de la cuisse',
        'description': "1ʳᵉ dose du vaccin pentavalent (DTC + HepB + Hib).",
        'obligatoire': True,
    },
    {
        'cle': 'vpo_1', 'nom': 'VPO 1', 'dose': 1, 'serie': 'vpo',
        'semaines': 6, 'affichage': '6 semaines',
        'maladies': 'Poliomyélite',
        'voie': 'Orale, 2 gouttes',
        'description': "1ʳᵉ dose de la série polio orale.",
        'obligatoire': True,
    },
    {
        'cle': 'pcv_1', 'nom': 'PCV-13 1', 'dose': 1, 'serie': 'pcv',
        'semaines': 6, 'affichage': '6 semaines',
        'maladies': 'Infections à pneumocoque (pneumonie, méningite, otite)',
        'voie': 'Intramusculaire, cuisse',
        'description': "1ʳᵉ dose du vaccin antipneumococcique conjugué 13-valent.",
        'obligatoire': True,
    },
    {
        'cle': 'rota_1', 'nom': 'Rotavirus 1', 'dose': 1, 'serie': 'rota',
        'semaines': 6, 'affichage': '6 semaines',
        'maladies': 'Diarrhées sévères à rotavirus',
        'voie': 'Orale',
        'description': "1ʳᵉ dose du vaccin antirotavirus, introduit au Bénin "
                       "en décembre 2019.",
        'obligatoire': True,
    },

    # --- 10 semaines -------------------------------------------------------
    {
        'cle': 'penta_2', 'nom': 'Pentavalent 2', 'dose': 2, 'serie': 'penta',
        'semaines': 10, 'affichage': '10 semaines',
        'maladies': 'Diphtérie, tétanos, coqueluche, hépatite B, Haemophilus influenzae b',
        'voie': 'Intramusculaire, face externe de la cuisse',
        'description': "2ᵉ dose du vaccin pentavalent, 4 semaines après la 1ʳᵉ.",
        'obligatoire': True,
    },
    {
        'cle': 'vpo_2', 'nom': 'VPO 2', 'dose': 2, 'serie': 'vpo',
        'semaines': 10, 'affichage': '10 semaines',
        'maladies': 'Poliomyélite',
        'voie': 'Orale, 2 gouttes',
        'description': "2ᵉ dose de la série polio orale.",
        'obligatoire': True,
    },
    {
        'cle': 'pcv_2', 'nom': 'PCV-13 2', 'dose': 2, 'serie': 'pcv',
        'semaines': 10, 'affichage': '10 semaines',
        'maladies': 'Infections à pneumocoque',
        'voie': 'Intramusculaire, cuisse',
        'description': "2ᵉ dose du vaccin antipneumococcique conjugué.",
        'obligatoire': True,
    },
    {
        'cle': 'rota_2', 'nom': 'Rotavirus 2', 'dose': 2, 'serie': 'rota',
        'semaines': 10, 'affichage': '10 semaines',
        'maladies': 'Diarrhées sévères à rotavirus',
        'voie': 'Orale',
        'description': "2ᵉ dose du vaccin antirotavirus.",
        'obligatoire': True,
    },

    # --- 14 semaines -------------------------------------------------------
    {
        'cle': 'penta_3', 'nom': 'Pentavalent 3', 'dose': 3, 'serie': 'penta',
        'semaines': 14, 'affichage': '14 semaines',
        'maladies': 'Diphtérie, tétanos, coqueluche, hépatite B, Haemophilus influenzae b',
        'voie': 'Intramusculaire, face externe de la cuisse',
        'description': "3ᵉ et dernière dose du vaccin pentavalent.",
        'obligatoire': True,
    },
    {
        'cle': 'vpo_3', 'nom': 'VPO 3', 'dose': 3, 'serie': 'vpo',
        'semaines': 14, 'affichage': '14 semaines',
        'maladies': 'Poliomyélite',
        'voie': 'Orale, 2 gouttes',
        'description': "3ᵉ et dernière dose de la série polio orale.",
        'obligatoire': True,
    },
    {
        'cle': 'pcv_3', 'nom': 'PCV-13 3', 'dose': 3, 'serie': 'pcv',
        'semaines': 14, 'affichage': '14 semaines',
        'maladies': 'Infections à pneumocoque',
        'voie': 'Intramusculaire, cuisse',
        'description': "3ᵉ et dernière dose du vaccin antipneumococcique.",
        'obligatoire': True,
    },
    {
        'cle': 'rota_3', 'nom': 'Rotavirus 3', 'dose': 3, 'serie': 'rota',
        'semaines': 14, 'affichage': '14 semaines',
        'maladies': 'Diarrhées sévères à rotavirus',
        'voie': 'Orale',
        'description': "3ᵉ et dernière dose du vaccin antirotavirus (ROTAVAC).",
        'obligatoire': True,
    },
    {
        'cle': 'vpi', 'nom': 'VPI (polio injectable)', 'dose': 1, 'serie': 'vpi',
        'semaines': 14, 'affichage': '14 semaines',
        'maladies': 'Poliomyélite',
        'voie': 'Intramusculaire, cuisse',
        'description': "Dose de vaccin polio inactivé injectable, administrée "
                       "en même temps que le VPO 3.",
        'obligatoire': True,
    },

    # --- Vaccin antipaludique (introduit en avril 2024) --------------------
    {
        'cle': 'rtss_1', 'nom': 'Antipaludique 1 (RTS,S)', 'dose': 1, 'serie': 'rtss',
        'mois': 6, 'affichage': '6 mois',
        'maladies': 'Paludisme (formes graves à Plasmodium falciparum)',
        'voie': 'Intramusculaire, cuisse',
        'description': "1ʳᵉ dose du vaccin antipaludique RTS,S/AS01, introduit "
                       "dans le PEV béninois en avril 2024.",
        'obligatoire': True,
    },
    {
        'cle': 'rtss_2', 'nom': 'Antipaludique 2 (RTS,S)', 'dose': 2, 'serie': 'rtss',
        'mois': 7, 'affichage': '7 mois',
        'maladies': 'Paludisme',
        'voie': 'Intramusculaire, cuisse',
        'description': "2ᵉ dose du vaccin antipaludique, un mois après la 1ʳᵉ.",
        'obligatoire': True,
    },

    # --- 9 mois ------------------------------------------------------------
    {
        'cle': 'var_1', 'nom': 'VAR 1 (rougeole-rubéole)', 'dose': 1, 'serie': 'var',
        'mois': 9, 'affichage': '9 mois',
        'maladies': 'Rougeole, rubéole',
        'voie': 'Sous-cutanée, bras',
        'description': "1ʳᵉ dose du vaccin rougeole-rubéole.",
        'obligatoire': True,
    },
    {
        'cle': 'vaa', 'nom': 'VAA (fièvre jaune)', 'dose': 1, 'serie': 'vaa',
        'mois': 9, 'affichage': '9 mois',
        'maladies': 'Fièvre jaune',
        'voie': 'Sous-cutanée, bras',
        'description': "Vaccin antiamaril, obligatoire au Bénin depuis 2002.",
        'obligatoire': True,
    },
    {
        'cle': 'mena', 'nom': 'MenA (méningite A)', 'dose': 1, 'serie': 'mena',
        'mois': 9, 'affichage': '9 mois',
        'maladies': 'Méningite à méningocoque A',
        'voie': 'Intramusculaire, bras',
        'description': "Vaccin conjugué contre le méningocoque A (MenAfriVac).",
        'obligatoire': True,
    },
    {
        'cle': 'rtss_3', 'nom': 'Antipaludique 3 (RTS,S)', 'dose': 3, 'serie': 'rtss',
        'mois': 9, 'affichage': '9 mois',
        'maladies': 'Paludisme',
        'voie': 'Intramusculaire, cuisse',
        'description': "3ᵉ dose du vaccin antipaludique, administrée avec le VAR.",
        'obligatoire': True,
    },

    # --- 18 mois -----------------------------------------------------------
    {
        'cle': 'var_2', 'nom': 'VAR 2 (rappel rougeole-rubéole)', 'dose': 2, 'serie': 'var',
        'mois': 18, 'affichage': '18 mois',
        'maladies': 'Rougeole, rubéole',
        'voie': 'Sous-cutanée, bras',
        'description': "2ᵉ dose rougeole-rubéole, introduite dans le calendrier "
                       "béninois en décembre 2024.",
        'obligatoire': True,
    },
    {
        'cle': 'rtss_4', 'nom': 'Antipaludique 4 (RTS,S)', 'dose': 4, 'serie': 'rtss',
        'mois': 18, 'affichage': '18 mois',
        'maladies': 'Paludisme',
        'voie': 'Intramusculaire, cuisse',
        'description': "4ᵉ dose (rappel) du vaccin antipaludique.",
        'obligatoire': True,
    },
]


# Chimioprévention et supplémentation associées aux séances PEV : ce ne sont
# pas des vaccins et elles ne figurent ni dans le calendrier ni dans le
# planning du calculateur.
CHIMIOPREVENTION_PALUDISME = [
    {
        'cle': 'tpi_1', 'nom': 'TPI 1 (sulfadoxine-pyriméthamine)', 'dose': 1,
        'serie': 'tpi_1', 'semaines': 10, 'affichage': '10 semaines',
        'maladies': 'Paludisme', 'voie': 'Orale',
        'categorie': 'chimioprevention',
        'description': 'Première prise de sulfadoxine-pyriméthamine.',
    },
    {
        'cle': 'tpi_2', 'nom': 'TPI 2 (sulfadoxine-pyriméthamine)', 'dose': 2,
        'serie': 'tpi_2', 'semaines': 14, 'affichage': '14 semaines',
        'maladies': 'Paludisme', 'voie': 'Orale',
        'categorie': 'chimioprevention',
        'description': 'Deuxième prise de sulfadoxine-pyriméthamine.',
    },
    {
        'cle': 'tpi_3', 'nom': 'TPI 3 (sulfadoxine-pyriméthamine)', 'dose': 3,
        'serie': 'tpi_3', 'mois': 9, 'affichage': '9 mois',
        'maladies': 'Paludisme', 'voie': 'Orale',
        'categorie': 'chimioprevention',
        'description': 'Troisième prise de sulfadoxine-pyriméthamine.',
    },
]

SUPPLEMENTATIONS = [
    {
        'nom': 'Vitamine A',
        'affichage': 'De 6 à 59 mois, tous les 6 mois',
        'description': "Supplémentation en vitamine A, couplée au déparasitage "
                       "à l'albendazole à partir de 12 mois.",
    },
]


# Correspondances des anciens libellés (ou des saisies libres) vers les clés
# stables du calendrier. Sans cela, une dose enregistrée sous « Pentavalent 1 »
# n'était jamais reconnue face à la clé « Pentavalent_1 ».
ALIAS = {
    'bcg': 'bcg',
    'vpo 0': 'vpo_0', 'vpo0': 'vpo_0', 'vpo_0': 'vpo_0',
    'vpo 0 (polio oral)': 'vpo_0', 'polio 0': 'vpo_0',
    'hepatite b': 'hepb_0', 'hépatite b': 'hepb_0', 'hepb': 'hepb_0',
    'hepatite_b': 'hepb_0',
    'vpi': 'vpi', 'polio injectable': 'vpi',
}
for _entree in CALENDRIER_PEV:
    ALIAS.setdefault(_entree['cle'], _entree['cle'])
    ALIAS.setdefault(_entree['nom'].lower(), _entree['cle'])
    # Anciennes clés de la forme « Pentavalent_1 », « VPO_2 », « RTSS_3 »…
    _serie = _entree['serie'].upper()
    ALIAS.setdefault(f"{_serie}_{_entree['dose']}".lower(), _entree['cle'])
for _ancien, _nouveau in [
    ('pentavalent_1', 'penta_1'), ('pentavalent_2', 'penta_2'),
    ('pentavalent_3', 'penta_3'),
    ('pentavalent 1', 'penta_1'), ('pentavalent 2', 'penta_2'),
    ('pentavalent 3', 'penta_3'),
    ('vpo_1', 'vpo_1'), ('vpo_2', 'vpo_2'), ('vpo_3', 'vpo_3'),
    ('vpo 1', 'vpo_1'), ('vpo 2', 'vpo_2'), ('vpo 3', 'vpo_3'),
    ('pcv_1', 'pcv_1'), ('pcv_2', 'pcv_2'), ('pcv_3', 'pcv_3'),
    ('pneumocoque 1 (pcv)', 'pcv_1'), ('pneumocoque 2 (pcv)', 'pcv_2'),
    ('pneumocoque 3 (pcv)', 'pcv_3'),
    ('rtss_1', 'rtss_1'), ('rtss_2', 'rtss_2'),
    ('rtss_3', 'rtss_3'), ('rtss_4', 'rtss_4'),
    ('vaccin antipaludique 1 (rts,s)', 'rtss_1'),
    ('vaccin antipaludique 2 (rts,s)', 'rtss_2'),
    ('vaccin antipaludique 3 (rts,s)', 'rtss_3'),
    ('vaccin antipaludique 4 (rts,s)', 'rtss_4'),
    ('var', 'var_1'), ('var_1', 'var_1'), ('var 1', 'var_1'),
    ('var (rougeole-rubéole)', 'var_1'),
    ('var_2', 'var_2'), ('var 2 (rappel rougeole)', 'var_2'),
    ('vaa', 'vaa'), ('vaa (fièvre jaune)', 'vaa'),
    ('mena', 'mena'), ('mena (méningite a)', 'mena'),
    ('rotavirus 1', 'rota_1'), ('rotavirus 2', 'rota_2'),
    ('rotavirus 3', 'rota_3'),
]:
    ALIAS[_ancien] = _nouveau


def normaliser_cle(nom):
    """Ramène un libellé de vaccin (ancien ou nouveau) à sa clé stable.

    Renvoie `None` si le libellé est inconnu, pour ne jamais rattacher par
    erreur une dose à un autre vaccin.
    """
    if not nom:
        return None
    brut = str(nom).strip().lower()
    return ALIAS.get(brut)


def ajouter_mois(depart, mois):
    """Ajoute `mois` mois calendaires à une date, sans dépendance externe.

    Le 31 janvier + 1 mois donne le 28 (ou 29) février : on ramène au dernier
    jour du mois cible plutôt que de déborder sur le mois suivant.
    """
    total = depart.month - 1 + mois
    annee = depart.year + total // 12
    mois_cible = total % 12 + 1
    # Dernier jour du mois cible
    if mois_cible == 12:
        dernier = 31
    else:
        dernier = (date(annee, mois_cible + 1, 1) - timedelta(days=1)).day
    return date(annee, mois_cible, min(depart.day, dernier))


def date_theorique(date_naissance, entree):
    """Date à laquelle la dose est due, d'après l'âge cible du calendrier."""
    if entree.get('mois') is not None:
        return ajouter_mois(date_naissance, entree['mois'])
    return date_naissance + timedelta(weeks=entree['semaines'])


def age_en_mois(date_naissance, reference=None):
    """Âge révolu en mois calendaires."""
    reference = reference or date.today()
    mois = (reference.year - date_naissance.year) * 12 + (reference.month - date_naissance.month)
    if reference.day < date_naissance.day:
        mois -= 1
    return max(mois, 0)


def calendrier_affichable():
    """Le calendrier de référence, prêt à être affiché (page publique)."""
    lignes = []
    for entree in CALENDRIER_PEV:
        lignes.append({
            'cle': entree['cle'],
            'nom': entree['nom'],
            'age_affichage': entree['affichage'],
            'maladies': entree['maladies'],
            'voie': entree['voie'],
            'description': entree['description'],
            'obligatoire': entree['obligatoire'],
            'categorie': entree.get('categorie', 'vaccination'),
            'age_min_mois': entree.get('mois') or (entree.get('semaines') or 0) // 4,
        })
    return lignes


def planifier(date_naissance, vaccins_recus, aujourd_hui=None):
    aujourd_hui = aujourd_hui or date.today()
    recus = {normaliser_cle(k): v for k, v in (vaccins_recus or {}).items()
             if normaliser_cle(k) and v}
    resultats, dates_serie = [], {}
    for entree in CALENDRIER_PEV:
        cle, serie = entree['cle'], entree['serie']
        theorique = date_theorique(date_naissance, entree)
        precedente = dates_serie.get(serie)
        if precedente is not None:
            theorique = max(theorique, precedente + timedelta(weeks=INTERVALLE_MIN_SEMAINES))
        maternité = bool(entree.get('maternite'))
        if cle in recus:
            date_affichee, statut, couleur, retard = recus[cle], 'Reçu', 'success', 0
            dates_serie[serie] = recus[cle]
        elif maternité:
            date_affichee, statut, couleur, retard = theorique, 'À la maternité', 'info', 0
            dates_serie[serie] = theorique
        else:
            date_affichee = theorique; dates_serie[serie] = theorique
            retard = (aujourd_hui - theorique).days
            if retard < 0: statut, couleur, retard = 'À venir', 'info', 0
            elif retard == 0: statut, couleur = "Aujourd'hui", 'warning'
            else: statut, couleur = 'En retard', 'danger'
        resultats.append({**{k: entree.get(k) for k in ('nom','cle','dose','serie','maladies','voie','categorie')},
            'date_prevue': date_affichee, 'date_theorique': theorique, 'statut': statut,
            'couleur': couleur, 'retard_jours': retard, 'age_affichage': entree['affichage'],
            'age_mois': entree.get('mois'), 'maternite': maternité})
    return sorted(resultats, key=lambda ligne: (ligne['date_prevue'], ligne['nom']))

AGES_SEANCE_DEDIEE = (9,)

def releve_de_la_seance_dediee(age, ages):
    return any(abs(float(age) - float(a)) <= 0.5 for a in ages)

def prochaine_seance(depart, codes):
    codes = set(codes or [])
    if not codes: return None
    for i in range(14):
        candidate = depart + timedelta(days=i)
        if candidate.weekday() in codes or candidate.strftime('%A').lower() in codes:
            return candidate
    return None

def adapter_au_centre(planning, jours_ordinaires, jours_9mois, ages_dedies=AGES_SEANCE_DEDIEE):
    ordinaires = set(jours_ordinaires or []); dedies = set(jours_9mois or [])
    def code(d): return d.weekday() if all(isinstance(x, int) for x in ordinaires | dedies) else d.strftime('%A').lower()
    resultat, retenues = [], {}
    for ligne in sorted(planning, key=lambda x: x['date_prevue']):
        ligne = dict(ligne); theorique = ligne['date_prevue']
        if ligne.get('maternite') or ligne['statut'] == 'À la maternité':
            retenue = theorique
        else:
            codes = dedies if releve_de_la_seance_dediee(ligne.get('age_mois') or 0, ages_dedies) else ordinaires
            serie = ligne.get('serie'); depart = theorique
            if serie in retenues: depart = max(depart, retenues[serie] + timedelta(weeks=INTERVALLE_MIN_SEMAINES))
            retenue = prochaine_seance(depart, codes)
        ligne['date_theorique'] = theorique; ligne['date_centre'] = retenue
        ligne['decalage_jours'] = (retenue - theorique).days if retenue else None
        ligne['seance_tardive'] = bool(retenue and retenue > theorique)
        if ligne.get('serie') and retenue: retenues[ligne['serie']] = retenue
        resultat.append(ligne)
    return resultat

def prochain_rdv(date_naissance, vaccins_recus, aujourd_hui=None):
    """La prochaine dose due (en retard d'abord, puis la plus proche)."""
    aujourd_hui = aujourd_hui or date.today()
    planning = planifier(date_naissance, vaccins_recus, aujourd_hui)
    en_attente = [ligne for ligne in planning if ligne['statut'] != 'Reçu']
    if not en_attente:
        return None
    en_retard = [ligne for ligne in en_attente if ligne['statut'] == 'En retard']
    if en_retard:
        return max(en_retard, key=lambda ligne: ligne['retard_jours'])
    return min(en_attente, key=lambda ligne: ligne['date_prevue'])


def resume_couverture(date_naissance, vaccins_recus, aujourd_hui=None):
    """Compteurs pour le tableau de bord : reçus / en retard / à venir."""
    planning = planifier(date_naissance, vaccins_recus, aujourd_hui)
    return {
        'total': len(planning),
        'recus': sum(1 for ligne in planning if ligne['statut'] == 'Reçu'),
        'maternite': sum(1 for ligne in planning if ligne['statut'] == 'À la maternité'),
        'en_retard': sum(1 for ligne in planning if ligne['statut'] == 'En retard'),
        'aujourd_hui': sum(1 for ligne in planning if ligne['statut'] == "Aujourd'hui"),
        'a_venir': sum(1 for ligne in planning if ligne['statut'] == 'À venir'),
    }
