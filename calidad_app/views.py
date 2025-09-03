from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test, permission_required
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth import get_user_model
from django.http import HttpResponse, HttpResponseNotAllowed
from django.contrib import messages
from django.db.models import Sum

from django.contrib.auth.models import Group, Permission

from .models import Proyecto, Lote, PerfilUsuario, AuditLog
from .forms import (
    ProyectoForm,
    LoteForm,
    LoteAdminForm,
    CustomUserCreationForm,
    CustomAuthenticationForm,
)

import zipfile
import os
from io import BytesIO


# =====================
# Helpers
# =====================
def is_admin(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)


def _ensure_groups_and_perms():
    """
    Crea/actualiza grupos:
      - Lectores: view_proyecto, view_lote
      - Editores: view_* + add/change de Lote y Proyecto
    """
    app_label = 'calidad_app'
    def p(code):  # obtiene permiso por codename
        return Permission.objects.get(content_type__app_label=app_label, codename=code)

    # Lectores
    lectores, _ = Group.objects.get_or_create(name='Lectores')
    for code in ['view_proyecto', 'view_lote']:
        try:
            lectores.permissions.add(p(code))
        except Permission.DoesNotExist:
            pass

    # Editores
    editores, _ = Group.objects.get_or_create(name='Editores')
    for code in ['view_proyecto', 'view_lote', 'add_lote', 'change_lote', 'add_proyecto', 'change_proyecto']:
        try:
            editores.permissions.add(p(code))
        except Permission.DoesNotExist:
            pass

    return lectores, editores


# =====================
# Auth
# =====================
class CustomLoginView(LoginView):
    template_name = 'login.html'
    authentication_form = CustomAuthenticationForm


class CustomLogoutView(LogoutView):
    next_page = 'login'


# =====================
# Registro de usuario (con aprobación)
# =====================
def registro_usuario(request):
    """
    Crea usuario INACTIVO (pendiente de aprobación por admin).
    No inicia sesión automáticamente.
    """
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False  # quedará pendiente
            user.save()
            PerfilUsuario.objects.get_or_create(user=user)
            messages.success(request, "Tu registro fue enviado. Un administrador debe aprobar tu acceso.")
            return redirect('login')
        else:
            messages.error(request, "Revisa los errores del formulario.")
    else:
        form = CustomUserCreationForm()
    return render(request, 'registro.html', {'form': form})


@login_required
@user_passes_test(is_admin)
def usuarios_pendientes(request):
    User = get_user_model()
    pendientes = User.objects.filter(is_active=False).order_by('date_joined', 'username')
    return render(request, 'usuarios_pendientes.html', {'pendientes': pendientes})


@login_required
@user_passes_test(is_admin)
def aprobar_usuario_lector(request, user_id):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    _ensure_groups_and_perms()
    User = get_user_model()
    usuario = get_object_or_404(User, id=user_id, is_active=False)
    lectores = Group.objects.get(name='Lectores')

    usuario.is_active = True
    usuario.is_staff = False
    usuario.save(update_fields=['is_active', 'is_staff'])
    usuario.groups.clear()
    usuario.groups.add(lectores)

    messages.success(request, f"Usuario '{usuario.username}' aprobado como LECTOR (solo lectura/descarga).")
    return redirect('usuarios_pendientes')


@login_required
@user_passes_test(is_admin)
def aprobar_usuario_editor(request, user_id):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    _ensure_groups_and_perms()
    User = get_user_model()
    usuario = get_object_or_404(User, id=user_id, is_active=False)
    editores = Group.objects.get(name='Editores')

    usuario.is_active = True
    usuario.is_staff = False  # editor no es staff; permisos por grupo
    usuario.save(update_fields=['is_active', 'is_staff'])
    usuario.groups.clear()
    usuario.groups.add(editores)

    messages.success(request, f"Usuario '{usuario.username}' aprobado como EDITOR.")
    return redirect('usuarios_pendientes')


@login_required
@user_passes_test(is_admin)
def eliminar_usuario_pendiente(request, user_id):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    User = get_user_model()
    usuario = get_object_or_404(User, id=user_id, is_active=False)
    username = usuario.username
    usuario.delete()
    messages.warning(request, f"Solicitud de usuario '{username}' eliminada.")
    return redirect('usuarios_pendientes')


# Activos (lista y eliminación)
@login_required
@user_passes_test(is_admin)
def usuarios_activos(request):
    User = get_user_model()
    activos = User.objects.filter(is_active=True).order_by('username')
    return render(request, 'usuarios_activos.html', {'activos': activos})


@login_required
@user_passes_test(is_admin)
def eliminar_usuario_activo(request, user_id):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    User = get_user_model()
    usuario = get_object_or_404(User, id=user_id, is_active=True)

    # No permitir borrar superusuarios ni a uno mismo
    if usuario.is_superuser:
        messages.error(request, "No puedes eliminar un superusuario.")
        return redirect('usuarios_activos')
    if usuario.id == request.user.id:
        messages.error(request, "No puedes eliminar tu propia cuenta.")
        return redirect('usuarios_activos')

    username = usuario.username
    usuario.delete()
    messages.warning(request, f"Usuario activo '{username}' eliminado.")
    return redirect('usuarios_activos')


# =====================
# Proyectos / Lotes
# =====================
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
@permission_required('calidad_app.add_proyecto', raise_exception=True)
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
@permission_required('calidad_app.add_lote', raise_exception=True)
def registrar_lote(request, proyecto_id):
    """
    Registrar un lote dentro de un proyecto ya seleccionado.
    Se requiere permiso add_lote (editores o staff).
    """
    proyecto = get_object_or_404(Proyecto, id=proyecto_id)

    if request.method == 'POST':
        form = LoteForm(request.POST, request.FILES, proyecto=proyecto)
        if form.is_valid():
            lote = form.save(commit=False)
            lote.proyecto = proyecto
            lote.subido_por = request.user  # firma
            lote.save()

            # Auditoría inicial de archivos cargados
            for field in Lote.FILE_FIELDS:
                f = getattr(lote, field, None)
                if f and getattr(f, "name", ""):
                    AuditLog.objects.create(
                        lote=lote,
                        campo=field,
                        accion=AuditLog.Accion.UPLOAD,
                        usuario=request.user,
                        detalle="Carga inicial"
                    )

            messages.success(request, "Lote registrado correctamente.")
            return redirect('detalle_lote', lote_id=lote.id)
        else:
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
@user_passes_test(is_admin)
def editar_lote(request, lote_id):
    """
    Edición de lote SOLO para admin/staff.
    Permite reemplazar/eliminar archivos, corregir datos y cambiar 'subido_por'.
    """
    lote = get_object_or_404(Lote, id=lote_id)

    # Snapshot previo para auditar archivos
    old_files = {f: (getattr(lote, f).name if getattr(lote, f) else '') for f in Lote.FILE_FIELDS}
    old_subido_por_id = lote.subido_por_id

    if request.method == 'POST':
        form = LoteAdminForm(request.POST, request.FILES, instance=lote, proyecto=lote.proyecto)
        if form.is_valid():
            lote = form.save()

            # Auditar reemplazos / eliminaciones de archivos
            for field in Lote.FILE_FIELDS:
                newf = getattr(lote, field, None)
                newname = newf.name if newf else ''
                oldname = old_files.get(field, '')
                cleared = request.POST.get(f'{field}-clear') == 'on'  # ClearableFileInput

                if cleared and oldname:
                    AuditLog.objects.create(
                        lote=lote, campo=field, accion=AuditLog.Accion.REPLACE,
                        usuario=request.user, detalle="Archivo eliminado"
                    )
                elif newname and newname != oldname:
                    accion = AuditLog.Accion.UPLOAD if not oldname else AuditLog.Accion.REPLACE
                    AuditLog.objects.create(
                        lote=lote, campo=field, accion=accion,
                        usuario=request.user, detalle="Edición de lote"
                    )

            # Aviso si cambió el responsable
            if old_subido_por_id != lote.subido_por_id:
                messages.info(request, "Se actualizó el responsable del lote.")

            messages.success(request, "Lote actualizado correctamente.")
            return redirect('detalle_lote', lote_id=lote.id)
        else:
            messages.error(request, "Corrige los errores del formulario.")
    else:
        form = LoteAdminForm(instance=lote, proyecto=lote.proyecto)

    return render(request, 'editar_lote.html', {'form': form, 'proyecto': lote.proyecto, 'lote': lote})


@login_required
def detalle_lote(request, lote_id):
    lote = get_object_or_404(Lote, id=lote_id)
    return render(request, 'detalle_lote.html', {'lote': lote})


@login_required
def descargar_zip(request, lote_id):
    """
    Crea un ZIP en memoria con los archivos presentes del lote.
    """
    lote = get_object_or_404(Lote, id=lote_id)

    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for archivo in [
            lote.analisis_espectrometrico,
            lote.tolerancia_geometrica,
            lote.pruebas_mecanicas,   # documento único (dureza + tensión)
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
