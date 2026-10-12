from django.contrib import admin, messages
from .models import LIBELLES_JOURS, Etablissement

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
    list_display = ('nom', 'type_etab', 'commune', 'fait_vaccination', 'jours_confirmes',
                    'jours_affichage', 'jours_9mois_affichage', 'source_vaccination')
    list_filter = ('type_etab', 'fait_vaccination', 'jours_confirmes', 'source_vaccination')
    list_editable = ('jours_confirmes',)
    actions = (confirmer_les_jours, retirer_la_confirmation)
    search_fields = ('nom', 'adresse', 'commune')
    list_per_page = 50
    fieldsets = (('Identification', {'fields': ('nom','type_etab','adresse','commune','telephone')}),
                 ('Localisation', {'fields': ('latitude','longitude')}),
                 ('Vaccination (PEV)', {'fields': ('fait_vaccination','jours_vaccination','jours_vaccination_9mois','jours_confirmes','horaire_vaccination','precision_vaccination','source_vaccination','maj_vaccination')}),
                 ('Programme par vaccin', {'fields': ('programme_vaccination','vaccins_non_proposes'),
                                           'description': "Par jour et par vaccin : le BCG le lundi, le Pentavalent le mardi… Le pseudo-groupe « 9mois » désigne les doses dues à neuf mois."}))

    @admin.display(description='Jours de vaccination')
    def jours_affichage(self, obj): return obj.jours_affichage

    @admin.display(description='Jours de 9 mois')
    def jours_9mois_affichage(self, obj):
        """Les jours où ce centre administre les doses dues à neuf mois.

        Ils se déduisent du programme détaillé quand il existe (le groupe
        « 9mois »), sinon du champ historique `jours_vaccination_9mois`.
        """
        jours = (obj.jours_pour('9mois', age_mois=9) if obj.programme_vaccination
                 else obj.jours_9mois_liste)
        if not jours:
            return '—'
        return ', '.join(LIBELLES_JOURS.get(code, code) for code in jours)
