from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth import login
from django.http import HttpResponse
from django.contrib import messages
from django.db.models import Sum

from .models import Proyecto, Lote, PerfilUsuario  # <- modelos SOLO desde models.py
from .forms import ProyectoForm, LoteForm, CustomUserCreationForm

import zipfile
import os
from io import BytesIO


class CustomLoginView(LoginView):
    # Busca templates/login.html
    template_name = 'login.html'


class CustomLogoutView(LogoutView):
    # Vuelve al login tras cerrar sesión
    next_page = 'login'


def registro_usuario(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Si ya tienes señal post_save para crear PerfilUsuario, puedes omitir:
            PerfilUsuario.objects.get_or_create(user=user)
            login(request, user)
            return redirect('ver_proyectos')
        else:
            messages.error(request, "Revisa los errores del formulario.")
    else:
        form = CustomUserCreationForm()
    return render(request, 'registro.html', {'form': form})


@login_required
def ver_proyectos(request):
    proyectos = Proyecto.objects.all()
    for proyecto in proyectos:
        producidas = proyecto.lotes.aggregate(s=Sum('numero_partes'))['s'] or 0
        total = proyecto.piezas_totales or 0
        avance = round((producidas / total) * 100.0, 2) if total > 0 else 0.0
        faltantes = max(total - producidas, 0) if total > 0 else 0

        proyecto.avance = avance
        proyecto.piezas_completadas = producidas
        proyecto.piezas_restantes = faltantes
        proyecto.total = total

    return render(request, 'ver_proyectos.html', {'proyectos': proyectos})


@login_required
def crear_proyecto(request):
    if request.method == 'POST':
        form = ProyectoForm(request.POST)
        if form.is_valid():
            proyecto = form.save()
            return redirect('registrar_lote', proyecto_id=proyecto.id)
        else:
            messages.error(request, "Revisa los errores del formulario.")
    else:
        form = ProyectoForm()
    return render(request, 'crear_proyecto.html', {'form': form})


@login_required
def lotes_por_proyecto(request, proyecto_id):
    proyecto = get_object_or_404(Proyecto, id=proyecto_id)
    lotes = Lote.objects.filter(proyecto=proyecto).order_by('-fecha', 'id_lote')
    return render(request, 'lotes_por_proyecto.html', {'proyecto': proyecto, 'lotes': lotes})


@login_required
def registrar_lote(request, proyecto_id):
    """
    Registrar un lote dentro de un proyecto ya seleccionado.
    LoteForm NO incluye 'proyecto'; se fija aquí.
    """
    proyecto = get_object_or_404(Proyecto, id=proyecto_id)

    if request.method == 'POST':
        form = LoteForm(request.POST, request.FILES, proyecto=proyecto)
        if form.is_valid():
            lote = form.save(commit=False)
            lote.proyecto = proyecto
            lote.save()
            messages.success(request, "Lote registrado correctamente.")
            return redirect('detalle_lote', lote_id=lote.id)
        else:
            # Vuelca errores al sistema de mensajes (además de errores por campo en el template)
            errores = []
            for campo, errs in form.errors.items():
                for e in errs:
                    errores.append(f"{campo}: {e}")
            if errores:
                messages.error(request, "No se pudo guardar el lote. " + " | ".join(errores))
    else:
        form = LoteForm(proyecto=proyecto)

    return render(request, 'registrar_lote.html', {'form': form, 'proyecto': proyecto})


@login_required
def detalle_lote(request, lote_id):
    lote = get_object_or_404(Lote, id=lote_id)
    return render(request, 'detalle_lote.html', {'lote': lote})


@login_required
def descargar_zip(request, lote_id):
    """
    Crea un ZIP en memoria con los archivos presentes del lote.
    Intenta usar .path (filesystem); si no existe, lee desde el storage.
    """
    lote = get_object_or_404(Lote, id=lote_id)

    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for archivo in [
            lote.analisis_espectrometrico,
            lote.tolerancia_geometrica,
            lote.prueba_dureza,
            lote.prueba_tension,
            lote.evidencia_fotografica,
            lote.plano_original,
        ]:
            if not archivo or not getattr(archivo, 'name', ''):
                continue

            arcname = os.path.basename(archivo.name)

            if hasattr(archivo, 'path'):
                try:
                    zip_file.write(archivo.path, arcname)
                    continue
                except Exception:
                    pass

            try:
                archivo.open('rb')
                try:
                    zip_file.writestr(arcname, archivo.read())
                finally:
                    archivo.close()
            except Exception:
                pass

    zip_buffer.seek(0)
    response = HttpResponse(zip_buffer.getvalue(), content_type='application/zip')
    response['Content-Disposition'] = f'attachment; filename={str(lote.id_lote).zfill(5)}.zip'
    return response
