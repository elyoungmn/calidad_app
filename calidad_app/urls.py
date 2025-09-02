from django.urls import path
from . import views

urlpatterns = [
    # Auth (login/logout)
    path('accounts/login/', views.CustomLoginView.as_view(), name='login'),
    path('accounts/logout/', views.CustomLogoutView.as_view(), name='logout'),

    # Home / Proyectos
    path('', views.ver_proyectos, name='ver_proyectos'),
    path('proyectos/nuevo/', views.crear_proyecto, name='crear_proyecto'),
    path('proyectos/<int:proyecto_id>/lotes/', views.lotes_por_proyecto, name='lotes_por_proyecto'),

    # Registrar lote directamente en un proyecto
    path('registrar_lote/<int:proyecto_id>/', views.registrar_lote, name='registrar_lote'),

    # Detalle de lote y descarga
    path('lotes/<int:lote_id>/', views.detalle_lote, name='detalle_lote'),
    path('lotes/<int:lote_id>/zip/', views.descargar_zip, name='descargar_zip'),

    # Registro de usuario (opcional)
    path('registro/', views.registro_usuario, name='registro_usuario'),
]
