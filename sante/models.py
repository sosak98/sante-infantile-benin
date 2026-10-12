from django.db import models
from django.utils import timezone

JOURS_SEMAINE = (
    ('lundi', 'Lundi'), ('mardi', 'Mardi'), ('mercredi', 'Mercredi'),
    ('jeudi', 'Jeudi'), ('vendredi', 'Vendredi'), ('samedi', 'Samedi'),
    ('dimanche', 'Dimanche'),
)
CODES_JOURS = [code for code, _ in JOURS_SEMAINE]
LIBELLES_JOURS = dict(JOURS_SEMAINE)


def code_du_jour(quand=None):
    quand = quand or timezone.localdate()
    return CODES_JOURS[quand.weekday()]


class Etablissement(models.Model):
    TYPES = (('centre', 'Centre de Santé'), ('pharmacie', 'Pharmacie'),
             ('hopital', 'Hôpital'), ('hopital_zone', 'Hôpital de zone'),
             ('clinique', 'Clinique'))
    SOURCES_VACCINATION = (('', 'Non renseigné'), ('centre', 'Déclaré par le centre'),
                            ('osm', 'OpenStreetMap'), ('admin', 'Saisi par l’administration'))
    # Libellés lisibles des groupes de vaccins (clés de `programme_vaccination`
    # et de `vaccins_non_proposes`). « 9mois » est le pseudo-groupe des doses
    # dues à neuf mois : les centres leur réservent souvent une séance.
    GROUPES = {
        'bcg': 'BCG',
        'vpo': 'VPO',
        'vpo_naissance': 'VPO 0 (naissance)',
        'hepb_naissance': 'Hépatite B (naissance)',
        'penta': 'Pentavalent',
        'pcv': 'PCV-13',
        'rota': 'Rotavirus',
        'vpi': 'VPI',
        'rtss': 'Antipaludique RTS,S',
        'var': 'VAR (rougeole-rubéole)',
        'vaa': 'Fièvre jaune (VAA)',
        'mena': 'Méningite A (MenA)',
        'vitamine_a': 'Vitamine A',
        '9mois': '9 mois',
    }
    # Les vaccins des 6, 10 et 14 semaines s'administrent ensemble : un centre
    # qui annonce « jour Pentavalent » fait aussi PCV-13, rotavirus et VPI.
    SERIES_CONCOMITANTES = {'penta', 'pcv', 'rota', 'vpi'}
    nom = models.CharField(max_length=200)
    type_etab = models.CharField(max_length=20, choices=TYPES)
    adresse = models.CharField(max_length=300)
    latitude = models.FloatField()
    longitude = models.FloatField()
    telephone = models.CharField(max_length=20, blank=True)
    commune = models.CharField(max_length=100, blank=True)
    fait_vaccination = models.BooleanField(default=False, verbose_name="Propose la vaccination PEV")
    jours_vaccination = models.CharField(max_length=80, blank=True, verbose_name="Jours de vaccination")
    jours_vaccination_9mois = models.CharField(max_length=80, blank=True, verbose_name="Jours dédiés aux 9 mois")
    # Les centres n'organisent pas leurs séances « avant 9 mois / 9 mois » :
    # ils les organisent par vaccin (le BCG le lundi, le Pentavalent le mardi,
    # la vitamine A le mercredi…). Forme :
    #   {"lundi": {"mode": "seulement", "series": ["bcg", "vpo"]},
    #    "mercredi": {"mode": "tous_sauf", "series": ["bcg", "var"]},
    #    "vendredi": {"mode": "tous"}}
    # Le pseudo-groupe « 9mois » désigne les doses dues à neuf mois.
    programme_vaccination = models.JSONField(
        default=dict, blank=True, verbose_name="Programme par jour et par vaccin",
        help_text='Ex. {"lundi": {"mode": "seulement", "series": ["bcg", "vpo"]}}',
    )
    # Tous les vaccins du PEV ne sont pas déployés partout : le RTS,S n'arrive
    # que dans certaines zones. Groupes séparés par des virgules.
    vaccins_non_proposes = models.CharField(
        max_length=200, blank=True, verbose_name="Vaccins non proposés dans ce centre",
        help_text="Groupes séparés par des virgules, ex. « rtss ».",
    )
    jours_confirmes = models.BooleanField(default=False, verbose_name="Jours confirmés")
    horaire_vaccination = models.CharField(max_length=100, blank=True, verbose_name="Horaires des séances")
    precision_vaccination = models.CharField(max_length=250, blank=True, verbose_name="Précision")
    source_vaccination = models.CharField(max_length=10, blank=True, default='', choices=SOURCES_VACCINATION)
    maj_vaccination = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['nom']
        indexes = [models.Index(fields=['fait_vaccination']), models.Index(fields=['type_etab'])]

    def __str__(self):
        return f"{self.nom} ({self.get_type_etab_display()})"

    @property
    def jours_liste(self):
        bruts = {j.strip().lower() for j in (self.jours_vaccination or '').split(',')}
        return [code for code in CODES_JOURS if code in bruts]

    @property
    def jours_9mois_liste(self):
        bruts = {j.strip().lower() for j in (self.jours_vaccination_9mois or '').split(',')}
        return [code for code in CODES_JOURS if code in bruts]

    @property
    def jours_libelles(self):
        return [LIBELLES_JOURS[code] for code in self.jours_liste]

    @property
    def jours_9mois_libelles(self):
        return [LIBELLES_JOURS[code] for code in self.jours_9mois_liste]

    @property
    def jours_affichage(self):
        libelles = self.jours_libelles
        if not libelles: return "Jours non communiqués"
        if len(libelles) == 1: return libelles[0]
        return ', '.join(libelles[:-1]) + ' et ' + libelles[-1]

    @property
    def jours_renseignes(self): return bool(self.jours_liste)

    @property
    def coordonnees_connues(self):
        """La position du centre est-elle réellement connue ?

        Les centres dont la position n'a pas encore été saisie dans
        l'administration sont enregistrés à 0.0 / 0.0 : un point au large du
        golfe de Guinée. Tant qu'elles le sont, on ne propose ni itinéraire ni
        marqueur : un centre mal placé envoie une famille au mauvais endroit.
        """
        return bool(self.latitude) and bool(self.longitude)

    @property
    def non_proposes_liste(self):
        """Groupes de vaccins que ce centre ne reçoit pas (clés, en minuscules)."""
        bruts = (self.vaccins_non_proposes or '').split(',')
        return [brut.strip().lower() for brut in bruts if brut.strip()]

    @property
    def non_proposes_libelles(self):
        """Les mêmes groupes, en clair : « Antipaludique RTS,S »."""
        return [self.GROUPES.get(cle, cle.capitalize()) for cle in self.non_proposes_liste]

    @property
    def _programme_normalise(self):
        programme = self.programme_vaccination
        if not isinstance(programme, dict):
            return {}
        return {str(code).strip().lower(): regle for code, regle in programme.items() if code}

    def _regle_normalisee(self, regle):
        """Une règle de jour : {« mode »: tous|seulement|tous_sauf, « series »: […]}. """
        if isinstance(regle, (list, tuple, set)):
            regle = {'mode': 'seulement', 'series': list(regle)}
        if not isinstance(regle, dict):
            return None
        mode = str(regle.get('mode') or 'tous').strip().lower()
        if mode not in ('tous', 'seulement', 'tous_sauf'):
            mode = 'seulement'
        series = []
        for brut in (regle.get('series') or []):
            cle = str(brut).strip().lower()
            if cle and cle not in series:
                series.append(cle)
        return mode, series

    @staticmethod
    def _dose_de_9_mois(serie, age_mois):
        if serie == '9mois':
            return True
        try:
            return abs(float(age_mois) - 9) < 0.5
        except (TypeError, ValueError):
            return False

    def _jour_programme(self, regle, serie, age_mois):
        """La série est-elle administrée ce jour-là, d'après la règle du jour ?"""
        regle = self._regle_normalisee(regle)
        if regle is None:
            return False
        mode, series = regle
        if mode == 'tous':
            return True
        concerne = serie in series or (
            serie in self.SERIES_CONCOMITANTES and bool(set(series) & self.SERIES_CONCOMITANTES)
        )
        if self._dose_de_9_mois(serie, age_mois) and '9mois' in series:
            concerne = True
        return concerne if mode == 'seulement' else not concerne

    def jours_pour(self, serie, age_mois=None):
        """Jours (codes) où le centre administre cette série de vaccins.

        Un vaccin que le centre ne reçoit pas n'a aucun jour, quelle que soit
        la règle du programme. Sans programme détaillé, on retombe sur les
        jours d'ouverture saisis dans `jours_vaccination`.
        """
        serie = str(serie or '').strip().lower()
        if not serie:
            return []
        if serie in self.non_proposes_liste:
            return []
        programme = self._programme_normalise
        if not programme:
            return self.jours_liste
        return [code for code in CODES_JOURS
                if self._jour_programme(programme.get(code), serie, age_mois)]

    def _regle_affichage(self, regle):
        """Une règle de jour en clair : « BCG, VPO » ou « toutes les doses sauf 9 mois »."""
        regle = self._regle_normalisee(regle)
        if regle is None:
            return ''
        mode, series = regle
        libelles = [self.GROUPES.get(cle, cle) for cle in series]
        if mode == 'tous':
            return 'toutes les doses'
        if mode == 'tous_sauf':
            return ('toutes les doses sauf ' + ', '.join(libelles)) if libelles else 'toutes les doses'
        return ', '.join(libelles)

    @property
    def programme_affichage(self):
        """Le programme du centre en clair, une ligne par jour :

        « Lundi : BCG, VPO · Mardi : Pentavalent, PCV-13, Rotavirus, VPI ».
        """
        programme = self._programme_normalise
        lignes = []
        for code in CODES_JOURS:
            if code not in programme:
                continue
            libelle = self._regle_affichage(programme[code])
            if libelle:
                lignes.append(f"{LIBELLES_JOURS[code]} : {libelle}")
        return ' · '.join(lignes)

    def vaccine_le(self, quand=None):
        if not self.fait_vaccination or not self.jours_renseignes: return None
        return code_du_jour(quand) in self.jours_liste

    def vaccine_aujourd_hui(self): return self.vaccine_le()
