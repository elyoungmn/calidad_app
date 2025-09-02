from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth import login
from django.http import HttpResponse
from .models import Proyecto, Lote, PerfilUsuario
from .forms import ProyectoForm, LoteForm, CustomUserCreationForm
import zipfile
import os
from io import BytesIO



class CustomLoginView(LoginView):
    template_name = 'login.html'

class CustomLogoutView(LogoutView):
    next_page = 'login'

def registro_usuario(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            PerfilUsuario.objects.create(user=user)
            login(request, user)
            return redirect('ver_proyectos')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registro.html', {'form': form})
@login_required
def seleccionar_proyecto_para_lote(request):
    proyectos = Proyecto.objects.all()  # O puedes filtrar según el usuario
    return render(request, 'seleccionar_proyecto.html', {'proyectos': proyectos})

@login_required
def ver_proyectos(request):
    proyectos = Proyecto.objects.all()
    for proyecto in proyectos:
        proyecto.avance = proyecto.calcular_avance()
        # Calcular piezas completadas y restantes
        piezas_totales = proyecto.piezas_totales
        porcentaje_avance = proyecto.avance / 100
        piezas_completadas = int(piezas_totales * porcentaje_avance)
        piezas_restantes = piezas_totales - piezas_completadas
        
        # Agregar los valores al proyecto
        proyecto.piezas_completadas = piezas_completadas
        proyecto.piezas_restantes = piezas_restantes
    return render(request, 'ver_proyectos.html', {'proyectos': proyectos})

@login_required
def crear_proyecto(request):
    if request.method == 'POST':
        form = ProyectoForm(request.POST)
        if form.is_valid():
            proyecto = form.save()  # Guarda y genera el ID aquí
            return redirect('registrar_lote', proyecto_id=proyecto.id)
    else:
        form = ProyectoForm()

    return render(request, 'crear_proyecto.html', {'form': form})


@login_required
def lotes_por_proyecto(request, proyecto_id):
    proyecto = get_object_or_404(Proyecto, id=proyecto_id)
    lotes = Lote.objects.filter(proyecto=proyecto)
    return render(request, 'lotes_por_proyecto.html', {'proyecto': proyecto, 'lotes': lotes})

@login_required
def registrar_lote(request, proyecto_id):
    proyecto = get_object_or_404(Proyecto, id=proyecto_id)
    if request.method == 'POST':
        form = LoteForm(request.POST, request.FILES)
        if form.is_valid():
            lote = form.save(commit=False)
            lote.proyecto = proyecto
            lote.save()
            return redirect('detalle_lote', lote_id=lote.id)
    else:
        form = LoteForm()
    return render(request, 'registrar_lote.html', {'form': form, 'proyecto': proyecto})

@login_required
def ver_lotes(request):
    lotes = Lote.objects.select_related('proyecto').all()
    return render(request, 'ver_lotes.html', {'lotes': lotes})

@login_required
def detalle_lote(request, lote_id):
    lote = get_object_or_404(Lote, id=lote_id)
    return render(request, 'detalle_lote.html', {'lote': lote})

@login_required
def descargar_zip(request, lote_id):
    lote = get_object_or_404(Lote, id=lote_id)

    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
        for archivo in [
            lote.analisis_espectrometrico,
            lote.tolerancia_geometrica,
            lote.prueba_dureza,
            lote.prueba_tension,
            lote.evidencia_fotografica,
            lote.plano_original,
        ]:
            if archivo:
                zip_file.write(archivo.path, os.path.basename(archivo.name))

    zip_buffer.seek(0)
    response = HttpResponse(zip_buffer, content_type='application/zip')
    response['Content-Disposition'] = f'attachment; filename={str(lote.id_lote).zfill(5)}.zip'
    return response
