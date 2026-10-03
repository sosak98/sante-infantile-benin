import unicodedata
from datetime import date, timedelta
from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.db import transaction
from conseils.pev import planifier
from enfants.models import Enfant
from . import __name__
from rappels.models import RappelEnvoye

def sans_accents(texte):
    return ''.join(c for c in unicodedata.normalize('NFD', texte) if unicodedata.category(c) != 'Mn')

class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true')
        parser.add_argument('--max', type=int, default=50)
        parser.add_argument('--date', dest='jour', type=date.fromisoformat)
    def handle(self, *args, **opts):
        jour = opts['jour'] or date.today()
        if opts['max'] <= 0: return
        candidats = []
        for enfant in Enfant.objects.select_related('parent__user'):
            email = enfant.parent.user.email
            if not email: continue
            recus = {r.nom_vaccin: r.date_reelle for r in enfant.vaccins_recus.all()}
            lignes = planifier(enfant.date_naissance, recus, jour)
            groupes = {}
            for ligne in lignes:
                if ligne['statut'] in ('Reçu', 'À la maternité'): continue
                d = ligne['date_prevue']
                if d not in (jour, jour + timedelta(days=3)): continue
                groupes.setdefault(d, []).append(ligne)
            for d, doses in groupes.items(): candidats.append((enfant, d, doses, 'jour_j' if d == jour else 'j3'))
        envoyes = 0
        for enfant, d, doses, quand in sorted(candidats, key=lambda x: x[1]):
            if envoyes >= opts['max']: break
            n = len(doses); noms = ', '.join(x['nom'] for x in doses[:2])
            sujet = 'Rappel de rendez-vous de vaccination'
            quantite = 'sa dose' if n == 1 else f'ses {n} doses'
            msg = sans_accents(f"Rappel : {enfant.prenom} a {quantite} prevue(s) le {d:%d/%m/%Y}. {noms}.")[:160]
            if opts['dry_run']: self.stdout.write(msg); envoyes += 1; continue
            with transaction.atomic():
                trace, cree = RappelEnvoye.objects.get_or_create(
                    enfant=enfant, date_rdv=d, quand=quand,
                    defaults={'nom_vaccin': noms, 'destinataire': enfant.parent.user.email, 'message': msg})
                if not cree: continue
                try: send_mail(sujet, msg, None, [trace.destinataire], fail_silently=False)
                except Exception:
                    trace.delete(); raise
            envoyes += 1
        self.stdout.write(self.style.SUCCESS(f'{envoyes} rappel(s) traite(s).'))
