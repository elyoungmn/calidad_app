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
    """Usuario personalizado basado en AbstractUser."""
    pass


# ======================================
# Helpers
# ======================================
def lot_upload_path(instance: "Lote", filename: str) -> str:
    """
    Ruta de almacenamiento para archivos del lote.
    Ej: lotes/2025/09/00001_reporte.pdf
    """
    base_date = instance.fecha or timezone.localdate()  # fecha es DateField
    safe_name = (filename or "").replace(" ", "_")
    return f"lotes/{base_date:%Y/%m}/{instance.id_lote}_{safe_name}"


# ======================================
# Modelos de negocio
# ======================================
class PerfilUsuario(models.Model):
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
        total = self.piezas_totales or 0
        producidas = self.lotes.aggregate(s=Sum("numero_partes"))["s"] or 0
        return round((producidas / total) * 100.0, 2) if total > 0 else 0.0

    def detalle_avance(self) -> dict:
        total = self.piezas_totales or 0
        producidas = self.lotes.aggregate(s=Sum("numero_partes"))["s"] or 0
        return {
            "piezas_totales": total,
            "producidas": producidas,
            "avance_pct": self.calcular_avance(),
        }


class Lote(models.Model):
    """
    Lote con un archivo único para pruebas mecánicas (dureza+tensión).
    """
    proyecto = models.ForeignKey(Proyecto, on_delete=models.PROTECT, related_name="lotes")
    id_lote = models.CharField(max_length=20, unique=True, help_text="Ejemplo: 00001")
    fecha = models.DateField(default=timezone.localdate)
    numero_partes = models.PositiveIntegerField(default=0, validators=[MinValueValidator(0)])

    # Firma: quién sube el lote
    subido_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="lotes_subidos"
    )

    # Documentos
    analisis_espectrometrico = models.FileField(upload_to=lot_upload_path, blank=True, null=True)
    tolerancia_geometrica   = models.FileField(upload_to=lot_upload_path, blank=True, null=True)
    pruebas_mecanicas       = models.FileField(upload_to=lot_upload_path, blank=True, null=True, help_text="Documento único con dureza y tensión")
    evidencia_fotografica   = models.FileField(upload_to=lot_upload_path, blank=True, null=True)
    plano_original          = models.FileField(upload_to=lot_upload_path, blank=True, null=True)

    creado = models.DateTimeField(auto_now_add=True)
    modificado = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-fecha", "id_lote"]
        verbose_name = "Lote"
        verbose_name_plural = "Lotes"

    # Campos para auditoría/validación (solo los vigentes)
    FILE_FIELDS = [
        "analisis_espectrometrico",
        "tolerancia_geometrica",
        "pruebas_mecanicas",
        "evidencia_fotografica",
        "plano_original",
    ]
    REQUIRED_FILE_FIELDS = FILE_FIELDS  # ajusta si no todos son obligatorios

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
    class Accion(models.TextChoices):
        UPLOAD = "UPLOAD", _("UPLOAD")
        REPLACE = "REPLACE", _("REPLACE")

    lote = models.ForeignKey(Lote, on_delete=models.CASCADE, related_name="auditorias")
    campo = models.CharField(max_length=50, help_text="Nombre del campo de archivo (p.ej., 'pruebas_mecanicas')")
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
