from django.contrib import admin, messages
from django.utils import timezone

from .models import ProfessionnelSante


@admin.register(ProfessionnelSante)
class ProfessionnelSanteAdmin(admin.ModelAdmin):
    list_display = ('user', 'fonction', 'structure_affichee', 'statut', 'date_demande')
    list_filter = ('statut', 'fonction')
    search_fields = ('user__username', 'user__email', 'user__first_name',
                     'user__last_name', 'numero_ordre', 'structure_libre')
    autocomplete_fields = ('etablissement',)
    actions = ('valider_comptes', 'refuser_comptes')

    @admin.action(description='Valider les comptes sélectionnés')
    def valider_comptes(self, request, queryset):
        nb = queryset.update(statut='valide', date_validation=timezone.now())
        self.message_user(request, f"{nb} compte(s) validé(s).", messages.SUCCESS)

    @admin.action(description='Refuser les comptes sélectionnés')
    def refuser_comptes(self, request, queryset):
        nb = queryset.update(statut='refuse', date_validation=timezone.now())
        self.message_user(request, f"{nb} compte(s) refusé(s).", messages.WARNING)
