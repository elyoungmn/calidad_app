from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path('accounts/login/', views.CustomLoginView.as_view(), name='login'),
    path('accounts/logout/', views.CustomLogoutView.as_view(), name='logout'),

    # Home / Proyectos
    path('', views.ver_proyectos, name='ver_proyectos'),
    path('proyectos/nuevo/', views.crear_proyecto, name='crear_proyecto'),
    path('proyectos/<int:proyecto_id>/lotes/', views.lotes_por_proyecto, name='lotes_por_proyecto'),

    # Lotes
    path('registrar_lote/<int:proyecto_id>/', views.registrar_lote, name='registrar_lote'),
    path('lotes/<int:lote_id>/', views.detalle_lote, name='detalle_lote'),
    path('lotes/<int:lote_id>/zip/', views.descargar_zip, name='descargar_zip'),
    path('lotes/<int:lote_id>/editar/', views.editar_lote, name='editar_lote'),

    # Registro de usuario (solicitud)
    path('registro/', views.registro_usuario, name='registro_usuario'),

    # Admin: aprobación/eliminación de pendientes
    path('usuarios/pendientes/', views.usuarios_pendientes, name='usuarios_pendientes'),
    path('usuarios/pendientes/<int:user_id>/aprobar/lector/', views.aprobar_usuario_lector, name='aprobar_usuario_lector'),
    path('usuarios/pendientes/<int:user_id>/aprobar/editor/', views.aprobar_usuario_editor, name='aprobar_usuario_editor'),
    path('usuarios/pendientes/<int:user_id>/eliminar/', views.eliminar_usuario_pendiente, name='eliminar_usuario_pendiente'),

    # Admin: activos (eliminar empleados que dejan la empresa)
    path('usuarios/activos/', views.usuarios_activos, name='usuarios_activos'),
    path('usuarios/activos/<int:user_id>/eliminar/', views.eliminar_usuario_activo, name='eliminar_usuario_activo'),
]
