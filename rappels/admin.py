from django.contrib import admin
from .models import RappelEnvoye
@admin.register(RappelEnvoye)
class RappelEnvoyeAdmin(admin.ModelAdmin):
    list_display = ('enfant','date_rdv','quand','destinataire','envoye_le')
    readonly_fields = [f.name for f in RappelEnvoye._meta.fields]
    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return False
