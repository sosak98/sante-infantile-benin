"""Création (ou mise à jour) non interactive du compte administrateur.

Le mot de passe ne vit QUE dans l'environnement — jamais dans le code ni dans
l'historique Git. Variables lues :

- ``DJANGO_SUPERUSER_USERNAME``  (défaut : ``admin_sib``)
- ``DJANGO_SUPERUSER_EMAIL``     (défaut : vide)
- ``DJANGO_SUPERUSER_PASSWORD``  (sans elle, la commande ne fait rien)

Si ``DJANGO_SUPERUSER_PASSWORD`` est absente, la commande se contente d'un
avertissement et rend la main sans erreur : les comptes existants restent
intacts et le démarrage du déploiement n'est pas bloqué. C'est le mode de
fonctionnement choisi quand l'administrateur gère son compte à la main.

La commande est idempotente : premier lancement → création du compte ;
lancements suivants → simple synchronisation du mot de passe et des drapeaux
d'administration. Elle peut donc figurer dans la commande de démarrage du
déploiement sans effet de bord.
"""
import os

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = (
        "Crée ou met à jour le superutilisateur à partir des variables "
        "d'environnement DJANGO_SUPERUSER_USERNAME, DJANGO_SUPERUSER_EMAIL "
        "et DJANGO_SUPERUSER_PASSWORD (sans elle, la commande ne fait rien)."
    )

    def handle(self, *args, **options):
        username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin_sib').strip()
        email = os.environ.get('DJANGO_SUPERUSER_EMAIL', '').strip()
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', '')

        if not password:
            # Choix assumé : l'absence de la variable signifie que le compte
            # administrateur est géré à la main. On ne touche à rien et on ne
            # bloque surtout pas le démarrage du déploiement.
            self.stdout.write(self.style.WARNING(
                "DJANGO_SUPERUSER_PASSWORD absente : aucun compte créé ni "
                "modifié, les comptes existants restent intacts."
            ))
            return

        User = get_user_model()
        try:
            validate_password(password, user=User(username=username, email=email))
        except ValidationError as erreur:
            raise CommandError(
                'Mot de passe refusé par les validateurs Django : '
                + ' '.join(erreur.messages)
            )

        utilisateur, cree = User.objects.get_or_create(
            username=username,
            defaults={'email': email, 'is_staff': True, 'is_superuser': True},
        )
        utilisateur.email = email or utilisateur.email
        utilisateur.is_staff = True
        utilisateur.is_superuser = True
        utilisateur.set_password(password)
        utilisateur.save()

        if cree:
            self.stdout.write(self.style.SUCCESS(
                'Superutilisateur « %s » créé.' % username))
        else:
            self.stdout.write(self.style.SUCCESS(
                'Superutilisateur « %s » mis à jour (mot de passe synchronisé).'
                % username))
