from django.contrib import admin

from .models import Etablissement


@admin.register(Etablissement)
class EtablissementAdmin(admin.ModelAdmin):
    list_display = ('nom', 'type_etab', 'commune', 'fait_vaccination',
                    'jours_affichage', 'source_vaccination')
    list_filter = ('type_etab', 'fait_vaccination', 'source_vaccination')
    search_fields = ('nom', 'adresse', 'commune')
    list_per_page = 50
    fieldsets = (
        ('Identification', {
            'fields': ('nom', 'type_etab', 'adresse', 'commune', 'telephone'),
        }),
        ('Localisation', {
            'fields': ('latitude', 'longitude'),
        }),
        ('Vaccination (PEV)', {
            'fields': ('fait_vaccination', 'jours_vaccination',
                       'horaire_vaccination', 'precision_vaccination',
                       'source_vaccination', 'maj_vaccination'),
            'description': "Jours séparés par des virgules, ex. « lundi,mercredi ».",
        }),
    )

    @admin.display(description='Jours de vaccination')
    def jours_affichage(self, obj):
        return obj.jours_affichage
