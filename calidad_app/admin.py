from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import PerfilUsuario, Proyecto, Lote, AuditLog, CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    pass


@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ("user", "puesto", "telefono", "creado")
    search_fields = ("user__username", "user__email", "puesto", "telefono")
    readonly_fields = ("creado",)


@admin.register(Proyecto)
class ProyectoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "cliente", "piezas_totales", "activo", "creado")
    search_fields = ("nombre", "cliente")
    list_filter = ("activo",)
    readonly_fields = ("creado", "modificado")
    date_hierarchy = "creado"


class AuditLogInline(admin.TabularInline):
    model = AuditLog
    fields = ("fecha", "campo", "accion", "usuario", "detalle")
    readonly_fields = ("fecha", "campo", "accion", "usuario", "detalle")
    extra = 0
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Lote)
class LoteAdmin(admin.ModelAdmin):
    list_display = ("id_lote", "proyecto", "fecha", "numero_partes", "completo")
    search_fields = ("id_lote", "proyecto__nombre")
    list_filter = ("proyecto", "fecha")
    date_hierarchy = "fecha"
    readonly_fields = ("creado", "modificado")
    inlines = [AuditLogInline]

    @admin.display(boolean=True, description="Completo")
    def completo(self, obj: Lote):
        try:
            return obj.is_completo()
        except Exception:
            return False


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("fecha", "lote", "campo", "accion", "usuario")
    list_filter = ("accion", "campo", "usuario")
    search_fields = ("lote__id_lote", "detalle")
    readonly_fields = ("fecha",)
    date_hierarchy = "fecha"
