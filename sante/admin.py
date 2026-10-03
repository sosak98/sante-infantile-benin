from django.contrib import admin, messages
from .models import Etablissement

@admin.action(description='Confirmer les jours sélectionnés')
def confirmer_les_jours(modeladmin, request, queryset):
    valides = queryset.exclude(jours_vaccination='').filter(jours_vaccination__isnull=False)
    refuses = queryset.count() - valides.count()
    valides.update(jours_confirmes=True)
    if refuses: messages.warning(request, f'{refuses} centre(s) sans jours n’ont pas été confirmés.')

@admin.action(description='Retirer la confirmation des jours')
def retirer_la_confirmation(modeladmin, request, queryset):
    queryset.update(jours_confirmes=False)

@admin.register(Etablissement)
class EtablissementAdmin(admin.ModelAdmin):
    list_display = ('nom', 'type_etab', 'commune', 'fait_vaccination', 'jours_confirmes', 'jours_affichage', 'source_vaccination')
    list_filter = ('type_etab', 'fait_vaccination', 'jours_confirmes', 'source_vaccination')
    list_editable = ('jours_confirmes',)
    actions = (confirmer_les_jours, retirer_la_confirmation)
    search_fields = ('nom', 'adresse', 'commune')
    list_per_page = 50
    fieldsets = (('Identification', {'fields': ('nom','type_etab','adresse','commune','telephone')}),
                 ('Localisation', {'fields': ('latitude','longitude')}),
                 ('Vaccination (PEV)', {'fields': ('fait_vaccination','jours_vaccination','jours_vaccination_9mois','jours_confirmes','horaire_vaccination','precision_vaccination','source_vaccination','maj_vaccination')}))

    @admin.display(description='Jours de vaccination')
    def jours_affichage(self, obj): return obj.jours_affichage
