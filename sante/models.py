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

    def vaccine_le(self, quand=None):
        if not self.fait_vaccination or not self.jours_renseignes: return None
        return code_du_jour(quand) in self.jours_liste

    def vaccine_aujourd_hui(self): return self.vaccine_le()
