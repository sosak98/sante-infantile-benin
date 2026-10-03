from django.db import models
from enfants.models import Enfant
class RappelEnvoye(models.Model):
    QUAND = (('j3', 'J-3'), ('jour_j', 'Jour J'))
    enfant = models.ForeignKey(Enfant, on_delete=models.CASCADE, related_name='rappels_envoyes')
    nom_vaccin = models.CharField(max_length=200)
    date_rdv = models.DateField()
    quand = models.CharField(max_length=8, choices=QUAND)
    destinataire = models.EmailField()
    message = models.CharField(max_length=160)
    envoye_le = models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['enfant','date_rdv','quand'], name='rappel_enfant_date_quand_unique')]
