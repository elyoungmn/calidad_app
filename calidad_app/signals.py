from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.utils import timezone

from .models import PerfilUsuario, Lote, AuditLog
from .middleware import get_current_user

User = get_user_model()


# --- Perfil de usuario al crear cuenta ---
@receiver(post_save, sender=User)
def crear_perfil_usuario(sender, instance, created, **kwargs):
    """
    Crea automáticamente el PerfilUsuario cuando se crea un usuario nuevo.
    Si ya existe, no hace nada.
    """
    if created:
        PerfilUsuario.objects.get_or_create(user=instance)


# --- Auditoría de archivos en Lote ---

@receiver(pre_save, sender=Lote)
def lote_pre_save_snapshot(sender, instance: Lote, **kwargs):
    """
    Antes de guardar un Lote existente, tomamos un snapshot para comparar
    los campos de archivo en post_save.
    """
    if instance.pk:
        try:
            instance._before = sender.objects.get(pk=instance.pk)
        except sender.DoesNotExist:
            instance._before = None
    else:
        instance._before = None


@receiver(post_save, sender=Lote)
def lote_post_save_audit(sender, instance: Lote, created, **kwargs):
    """
    Registra en AuditLog los UPLOAD/REPLACE por cada campo de archivo del Lote.
    Usa CurrentUserMiddleware para capturar el usuario en sesión.
    """
    user = get_current_user()
    before = getattr(instance, '_before', None)

    # Creación: todo archivo presente se considera UPLOAD inicial
    if created:
        for field in Lote.FILE_FIELDS:
            f = getattr(instance, field, None)
            if f and getattr(f, 'name', ''):
                AuditLog.objects.create(
                    lote=instance,
                    campo=field,
                    accion=AuditLog.Accion.UPLOAD,
                    usuario=user if (user and user.is_authenticated) else None,
                    detalle=f"Carga inicial de {field}: {f.name}",
                )
        return

    # Actualización: comparamos nombres de archivo antes vs después
    if before:
        for field in Lote.FILE_FIELDS:
            newf = getattr(instance, field, None)
            oldf = getattr(before, field, None)
            new_name = getattr(newf, 'name', '') or ''
            old_name = getattr(oldf, 'name', '') or ''

            # Cambio relevante: si hay archivo nuevo y difiere del anterior
            if new_name and new_name != old_name:
                accion = AuditLog.Accion.UPLOAD if not old_name else AuditLog.Accion.REPLACE
                AuditLog.objects.create(
                    lote=instance,
                    campo=field,
                    accion=accion,
                    usuario=user if (user and user.is_authenticated) else None,
                    detalle=f"{accion} de {field}: {old_name or '(vacío)'} -> {new_name}",
                )
