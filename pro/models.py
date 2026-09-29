"""Espace professionnels de santé : comptes agents du PEV et centres rattachés."""

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

from sante.models import Etablissement


class ProfessionnelSante(models.Model):
    """Compte d'un agent de santé, rattaché à une formation sanitaire.

    Un compte n'a AUCUN pouvoir tant qu'il n'a pas été validé : c'est ce qui
    empêche n'importe qui de publier de fausses informations (jours de
    vaccination, coordonnées) au nom d'un centre de santé.
    """

    FONCTIONS = (
        ('infirmier', "Infirmier(ère) diplômé(e) d'État"),
        ('sage_femme', 'Sage-femme'),
        ('medecin', 'Médecin'),
        ('agent_pev', 'Agent PEV / vaccinateur'),
        ('aide_soignant', 'Aide-soignant(e)'),
        ('autre', 'Autre personnel de santé'),
    )

    STATUTS = (
        ('en_attente', 'En attente de validation'),
        ('valide', 'Validé'),
        ('refuse', 'Refusé'),
    )

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='professionnel',
    )
    fonction = models.CharField(max_length=20, choices=FONCTIONS)
    etablissement = models.ForeignKey(
        Etablissement, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='professionnels',
        help_text="Formation sanitaire dont l'agent est responsable.",
    )
    structure_libre = models.CharField(
        max_length=200, blank=True,
        verbose_name='Structure (si absente de la liste)',
    )
    numero_ordre = models.CharField(
        max_length=50, blank=True,
        verbose_name="Numéro d'ordre ou matricule",
    )
    telephone = models.CharField(max_length=20, blank=True)
    statut = models.CharField(max_length=12, choices=STATUTS, default='en_attente')
    date_demande = models.DateTimeField(auto_now_add=True)
    date_validation = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Professionnel de santé'
        verbose_name_plural = 'Professionnels de santé'
        ordering = ['-date_demande']

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.get_fonction_display()})"

    @property
    def est_valide(self):
        return self.statut == 'valide'

    @property
    def structure_affichee(self):
        if self.etablissement:
            return self.etablissement.nom
        return self.structure_libre or 'Structure non précisée'

    def valider(self):
        self.statut = 'valide'
        self.date_validation = timezone.now()
        self.save(update_fields=['statut', 'date_validation'])
