from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

class Command(BaseCommand):
    def handle(self, *args, **options):
        if not User.objects.filter(username='admin_sib').exists():
            User.objects.create_superuser('admin_sib', 'sante.infantile.benin@gmail.com', 'Admin2026!')
            self.stdout.write('Superuser cree !')
        else:
            u = User.objects.get(username='admin_sib')
            u.set_password('Admin2026!')
            u.save()
            self.stdout.write('Mot de passe mis a jour !')
