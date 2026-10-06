from django.contrib import admin, messages
from django.utils import timezone

from .models import ProfessionnelSante


@admin.register(ProfessionnelSante)
class ProfessionnelSanteAdmin(admin.ModelAdmin):
    CRITERES_VALIDATION = (
        "Valider une demande si les quatre conditions sont réunies :\n"
        "1. la fonction déclarée est une fonction soignante (infirmier, sage-femme, médecin, aide-soignant, relais communautaire) ;\n"
        "2. le numéro d'ordre ou matricule est renseigné et plausible ;\n"
        "3. la structure déclarée existe et correspond à la fonction ;\n"
        "4. l'adresse électronique est joignable.\n"
        "Dans le doute, appeler le centre avant de valider. Refuser plutôt que valider à moitié : "
        "un compte refusé peut être redemandé."
    )

    list_display = ('user', 'fonction', 'structure_affichee', 'statut', 'date_demande')
    list_filter = ('statut', 'fonction')
    search_fields = ('user__username', 'user__email', 'user__first_name',
                     'user__last_name', 'numero_ordre', 'structure_libre')
    autocomplete_fields = ('etablissement',)
    actions = ('valider_comptes', 'refuser_comptes')

    def get_queryset(self, request):
        return super().get_queryset(request).order_by('statut', '-date_demande')

    @admin.action(description='Valider les comptes sélectionnés')
    def valider_comptes(self, request, queryset):
        nb = queryset.update(statut='valide', date_validation=timezone.now())
        self.message_user(request, f"{nb} compte(s) validé(s).", messages.SUCCESS)

    @admin.action(description='Refuser les comptes sélectionnés')
    def refuser_comptes(self, request, queryset):
        nb = queryset.update(statut='refuse', date_validation=timezone.now())
        self.message_user(request, f"{nb} compte(s) refusé(s).", messages.WARNING)
