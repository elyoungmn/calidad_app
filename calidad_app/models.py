# calidad_app/models.py
from django.db import models
from django.db.models import Sum
from django.conf import settings
from django.utils import timezone
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import AbstractUser

# ======================================
# Usuario personalizado
# ======================================
class CustomUser(AbstractUser):
    """
    Usuario personalizado basado en AbstractUser.
    Si necesitas campos extra (p.ej., puesto), agrégalos aquí.
    """
    pass


# ======================================
# Helpers
# ======================================
def lot_upload_path(instance: "Lote", filename: str) -> str:
    """
    Ruta de almacenamiento para archivos del lote.
    Ejemplo: lotes/2025/09/00001_reporte.pdf
    """
    base_date = instance.fecha or timezone.localdate()
    safe_name = (filename or "").replace(" ", "_")
    return f"lotes/{base_date:%Y/%m}/{instance.id_lote}_{safe_name}"

# ======================================
# Modelos de negocio
# ======================================
class PerfilUsuario(models.Model):
    """
    Perfil mínimo enlazado al usuario. Expandible (teléfono, rol, etc.)
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="perfil")
    puesto = models.CharField(max_length=120, blank=True, null=True)
    telefono = models.CharField(max_length=30, blank=True, null=True)
    creado = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"Perfil · {self.user.get_username()}"


class Proyecto(models.Model):
    nombre = models.CharField(max_length=200)
    cliente = models.CharField(max_length=200, blank=True, null=True)
    piezas_totales = models.PositiveIntegerField(default=0, validators=[MinValueValidator(0)])
    activo = models.BooleanField(default=True)
    creado = models.DateTimeField(auto_now_add=True)
    modificado = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-creado", "nombre"]
        verbose_name = "Proyecto"
        verbose_name_plural = "Proyectos"

    def __str__(self) -> str:
        return self.nombre

    def calcular_avance(self) -> float:
        """
        Devuelve SOLO el porcentaje de avance (float 0..100).
        Mantiene compatibilidad con vistas/plantillas que hacen operaciones numéricas (p.ej. / 100).
        """
        total = self.piezas_totales or 0
        producidas = self.lotes.aggregate(s=Sum("numero_partes"))["s"] or 0
        return round((producidas / total) * 100.0, 2) if total > 0 else 0.0

    def detalle_avance(self) -> dict:
        """
        Desglose opcional si lo necesitas en otras vistas.
        """
        total = self.piezas_totales or 0
        producidas = self.lotes.aggregate(s=Sum("numero_partes"))["s"] or 0
        return {
            "piezas_totales": total,
            "producidas": producidas,
            "avance_pct": self.calcular_avance(),
        }


class Lote(models.Model):
    """
    Lote con un FileField por tipo de documento (se mantiene tu diseño).
    """
    proyecto = models.ForeignKey(Proyecto, on_delete=models.PROTECT, related_name="lotes")
    id_lote = models.CharField(max_length=20, unique=True, help_text="Ejemplo: 00001")
    fecha = models.DateField(default=timezone.localdate)
    numero_partes = models.PositiveIntegerField(default=0, validators=[MinValueValidator(0)])

    # Documentos requeridos por ISO 9001:2015 (opcionalmente vacíos al inicio)
    analisis_espectrometrico = models.FileField(upload_to=lot_upload_path, blank=True, null=True)
    tolerancia_geometrica = models.FileField(upload_to=lot_upload_path, blank=True, null=True)
    prueba_dureza = models.FileField(upload_to=lot_upload_path, blank=True, null=True)
    prueba_tension = models.FileField(upload_to=lot_upload_path, blank=True, null=True)
    evidencia_fotografica = models.FileField(upload_to=lot_upload_path, blank=True, null=True)
    plano_original = models.FileField(upload_to=lot_upload_path, blank=True, null=True)

    creado = models.DateTimeField(auto_now_add=True)
    modificado = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-fecha", "id_lote"]
        verbose_name = "Lote"
        verbose_name_plural = "Lotes"

    # Campos de archivo que vigila la auditoría (no altera tu estructura)
    FILE_FIELDS = [
        "analisis_espectrometrico",
        "tolerancia_geometrica",
        "prueba_dureza",
        "prueba_tension",
        "evidencia_fotografica",
        "plano_original",
    ]
    REQUIRED_FILE_FIELDS = FILE_FIELDS  # útil para checks de completitud

    def __str__(self) -> str:
        return f"Lote {self.id_lote} · {self.proyecto.nombre}"

    def archivos_presentes(self) -> list[str]:
        presentes = []
        for field in self.REQUIRED_FILE_FIELDS:
            f = getattr(self, field, None)
            if f and getattr(f, "name", ""):
                presentes.append(field)
        return presentes

    def archivos_faltantes(self) -> list[str]:
        presentes = set(self.archivos_presentes())
        return [f for f in self.REQUIRED_FILE_FIELDS if f not in presentes]

    def is_completo(self) -> bool:
        return len(self.archivos_faltantes()) == 0


class AuditLog(models.Model):
    """
    Bitácora para saber quién subió o reemplazó cada archivo de Lote y cuándo.
    No modifica el modelo Lote; registra acciones por campo de archivo.
    """
    class Accion(models.TextChoices):
        UPLOAD = "UPLOAD", _("UPLOAD")     # primera carga del archivo en el campo
        REPLACE = "REPLACE", _("REPLACE")  # cuando se reemplaza por otro archivo

    lote = models.ForeignKey(Lote, on_delete=models.CASCADE, related_name="auditorias")
    campo = models.CharField(max_length=50, help_text="Nombre del campo de archivo en Lote, p.ej. 'prueba_dureza'")
    accion = models.CharField(max_length=10, choices=Accion.choices)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    detalle = models.TextField(blank=True)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-fecha"]
        verbose_name = "Auditoría"
        verbose_name_plural = "Auditorías"

    def __str__(self) -> str:
        return f"{self.lote.id_lote} · {self.campo} · {self.accion} · {self.fecha:%Y-%m-%d %H:%M}"
