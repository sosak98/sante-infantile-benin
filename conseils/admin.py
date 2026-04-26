from django.contrib import admin
from .models import Vaccin

@admin.register(Vaccin)
class VaccinAdmin(admin.ModelAdmin):
    list_display = ['nom', 'age_min_mois', 'age_max_mois', 'obligatoire']
