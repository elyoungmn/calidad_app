# calidad_app/forms.py
from django import forms
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from mimetypes import guess_type
import os

from .models import Proyecto, Lote, CustomUser


# ----------------------------
# Formularios de Usuario (CustomUser)
# ----------------------------

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={"class": "form-control"}),
        help_text=_("Opcional, para recuperar contraseña o notificaciones."),
    )

    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ("username", "email")
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control"}),
        }


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = CustomUser
        fields = ("username", "email", "first_name", "last_name", "is_active", "is_staff")
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
        }


# ----------------------------
# Formularios de negocio
# ----------------------------

class ProyectoForm(forms.ModelForm):
    class Meta:
        model = Proyecto
        fields = ["nombre", "cliente", "piezas_totales", "activo"]
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "form-control"}),
            "cliente": forms.TextInput(attrs={"class": "form-control"}),
            "piezas_totales": forms.NumberInput(attrs={"class": "form-control", "min": 0}),
            "activo": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


# Reglas estrictas por tipo de documento (extensión + MIME por nombre)
ALLOWED = {
    "analisis_espectrometrico": (
        [".pdf", ".xlsx", ".xls", ".csv", ".png"],
        [
            "application/pdf",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "application/vnd.ms-excel",
            "text/csv",
        ],
    ),
    "tolerancia_geometrica": (
        [".pdf", ".dxf", ".dwg", ".png"],
        [
            "application/pdf",
            "image/vnd.dxf",
            "application/acad",  # DWG en algunos entornos
        ],
    ),
    "prueba_dureza": (
        [".pdf", ".xlsx", ".xls", ".csv", ".jpg", ".jpeg", ".png"],
        [
            "application/pdf",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "application/vnd.ms-excel",
            "text/csv",
            "image/jpeg",
            "image/png",
        ],
    ),
    "prueba_tension": (
        [".pdf", ".xlsx", ".xls", ".csv", ".jpg", ".jpeg", ".png"],
        [
            "application/pdf",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "application/vnd.ms-excel",
            "text/csv",
            "image/jpeg",
            "image/png",
        ],
    ),
    "evidencia_fotografica": (
        [".jpg", ".jpeg", ".png", ".pdf", ".png"],
        [
            "image/jpeg",
            "image/png",
            "application/pdf",
        ],
    ),
    "plano_original": (
        [".pdf", ".dxf", ".dwg", ".png"],
        [
            "application/pdf",
            "image/vnd.dxf",
            "application/acad",
        ],
    ),
}


def _validate_ext_mime(field_name: str, file_field):
    """
    Valida extensión y MIME (estimado por nombre). Si el navegador reporta
    content_type en el upload, también puede usarse en la vista para reforzar.
    ¡OJO! No sombrear '_' (gettext) con variables locales.
    """
    if not file_field:
        return
    name = (file_field.name or "").lower()
    ext = os.path.splitext(name)[1]
    exts, mimes = ALLOWED[field_name]

    if ext not in exts:
        raise forms.ValidationError(
            _("%(campo)s: extensión no permitida (%(ext)s). Permitidas: %(permitidas)s"),
            params={
                "campo": field_name.replace("_", " ").title(),
                "ext": ext or "—",
                "permitidas": ", ".join(exts),
            },
        )

    mime_from_name, _encoding = guess_type(name)  # ¡No usar '_' aquí!
    if mime_from_name and mime_from_name not in mimes:
        raise forms.ValidationError(
            _("%(campo)s: tipo MIME no permitido (%(mime)s). Permitidos: %(permitidos)s"),
            params={
                "campo": field_name.replace("_", " ").title(),
                "mime": mime_from_name,
                "permitidos": ", ".join(mimes),
            },
        )


class LoteForm(forms.ModelForm):
    """
    Form para registrar un Lote DENTRO de un proyecto ya seleccionado.
    El proyecto se inyecta por __init__(proyecto=...) y se asigna en la vista.
    """
    def __init__(self, *args, proyecto: Proyecto | None = None, **kwargs):
        self.proyecto = proyecto
        super().__init__(*args, **kwargs)

    class Meta:
        model = Lote
        # OJO: NO incluimos 'proyecto' aquí
        fields = [
            "id_lote",
            "fecha",
            "numero_partes",
            "analisis_espectrometrico",
            "tolerancia_geometrica",
            "prueba_dureza",
            "prueba_tension",
            "evidencia_fotografica",
            "plano_original",
        ]
        widgets = {
            "id_lote": forms.TextInput(attrs={"class": "form-control", "placeholder": "00001"}),
            "fecha": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "numero_partes": forms.NumberInput(attrs={"class": "form-control", "min": 0}),
            "analisis_espectrometrico": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "tolerancia_geometrica": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "prueba_dureza": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "prueba_tension": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "evidencia_fotografica": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "plano_original": forms.ClearableFileInput(attrs={"class": "form-control"}),
        }

    def clean(self):
        cleaned = super().clean()

        # Validación por tipo/archivo (solo si el usuario adjuntó algo)
        for field in [
            "analisis_espectrometrico",
            "tolerancia_geometrica",
            "prueba_dureza",
            "prueba_tension",
            "evidencia_fotografica",
            "plano_original",
        ]:
            f = cleaned.get(field)
            if f:
                _validate_ext_mime(field, f)

        # Reglas de negocio: numero_partes no debe exceder piezas_totales del proyecto
        proyecto = self.proyecto  # viene de la vista
        numero_partes = cleaned.get("numero_partes") or 0
        if proyecto and proyecto.piezas_totales and numero_partes > proyecto.piezas_totales:
            self.add_error(
                "numero_partes",
                _("El número de partes del lote (%(np)s) excede las piezas totales del proyecto (%(pt)s)."),
            )

        return cleaned
