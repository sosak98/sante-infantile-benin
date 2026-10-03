from django.db import migrations, models
import django.db.models.deletion
class Migration(migrations.Migration):
    initial=True
    dependencies=[('enfants','0001_initial')]
    operations=[migrations.CreateModel(name='RappelEnvoye', fields=[('id',models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name='ID')),('nom_vaccin',models.CharField(max_length=200)),('date_rdv',models.DateField()),('quand',models.CharField(choices=[('j3','J-3'),('jour_j','Jour J')],max_length=8)),('destinataire',models.EmailField(max_length=254)),('message',models.CharField(max_length=160)),('envoye_le',models.DateTimeField(auto_now_add=True)),('enfant',models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,related_name='rappels_envoyes',to='enfants.enfant'))], options={'constraints':[models.UniqueConstraint(fields=('enfant','date_rdv','quand'),name='rappel_enfant_date_quand_unique')]} )]
