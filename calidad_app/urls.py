from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views
from .views import seleccionar_proyecto_para_lote

urlpatterns = [
    path('', views.ver_proyectos, name='ver_proyectos'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    path('crear_proyecto/', views.crear_proyecto, name='crear_proyecto'),
    path('proyecto/<int:proyecto_id>/', views.lotes_por_proyecto, name='lotes_por_proyecto'),
    path('registrar_lote/<int:proyecto_id>/', views.registrar_lote, name='registrar_lote'),
    path('lote/<int:lote_id>/', views.detalle_lote, name='detalle_lote'),
    path('lote/<int:lote_id>/descargar/', views.descargar_zip, name='descargar_zip'),
    path('lotes/', views.ver_lotes, name='ver_lotes'),
    path('seleccionar_proyecto/', seleccionar_proyecto_para_lote, name='seleccionar_proyecto'),
    path('registro/', views.registro_usuario, name='registro_usuario'),
]
