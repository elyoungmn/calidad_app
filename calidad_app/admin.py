from django.contrib import admin
from .models import CustomUser, PerfilUsuario, Proyecto, Lote

admin.site.register(CustomUser)
admin.site.register(PerfilUsuario)
admin.site.register(Proyecto)
admin.site.register(Lote)
