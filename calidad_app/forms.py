from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, UsernameField
from django.core.validators import FileExtensionValidator

from .models import Proyecto, Lote


class DateInput(forms.DateInput):
    input_type = "date"


# ----------------------------
# Proyecto
# ----------------------------
class ProyectoForm(forms.ModelForm):
    class Meta:
        model = Proyecto
        fields = ["nombre", "cliente", "piezas_totales", "activo"]
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "form-control", "placeholder": "Nombre del proyecto"}),
            "cliente": forms.TextInput(attrs={"class": "form-control", "placeholder": "Cliente"}),
            "piezas_totales": forms.NumberInput(attrs={"class": "form-control", "min": "0"}),
            "activo": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


# ----------------------------
# Lote (para alta normal)
# ----------------------------
_FILE_VALIDATOR = FileExtensionValidator(
    allowed_extensions=["pdf", "jpg", "jpeg", "png", "docx", "xlsx"]
)

class LoteForm(forms.ModelForm):
    """
    'proyecto' y 'subido_por' no se muestran; se fijan en la vista.
    """
    analisis_espectrometrico = forms.FileField(required=False, validators=[_FILE_VALIDATOR])
    tolerancia_geometrica   = forms.FileField(required=False, validators=[_FILE_VALIDATOR])
    pruebas_mecanicas       = forms.FileField(required=False, validators=[_FILE_VALIDATOR])
    evidencia_fotografica   = forms.FileField(required=False, validators=[_FILE_VALIDATOR])
    plano_original          = forms.FileField(required=False, validators=[_FILE_VALIDATOR])

    def __init__(self, *args, proyecto=None, **kwargs):
        self.proyecto = proyecto
        super().__init__(*args, **kwargs)

        self.fields["id_lote"].widget = forms.TextInput(
            attrs={"class": "form-control", "placeholder": "00001"}
        )
        self.fields["fecha"].widget = DateInput(attrs={"class": "form-control"})
        self.fields["numero_partes"].widget = forms.NumberInput(
            attrs={"class": "form-control", "min": "0"}
        )

        file_widgets = {"class": "form-control"}
        for f in [
            "analisis_espectrometrico",
            "tolerancia_geometrica",
            "pruebas_mecanicas",
            "evidencia_fotografica",
            "plano_original",
        ]:
            self.fields[f].widget = forms.ClearableFileInput(attrs=file_widgets)
            self.fields[f].widget.attrs.update({
                "accept": ".pdf,.docx,.xlsx,.jpg,.jpeg,.png"
            })

        # Etiquetas amigables
        self.fields["id_lote"].label = "ID de Lote"
        self.fields["fecha"].label = "Fecha"
        self.fields["numero_partes"].label = "Número de partes"
        self.fields["analisis_espectrometrico"].label = "Análisis espectrométrico"
        self.fields["tolerancia_geometrica"].label = "Tolerancia geométrica"
        self.fields["pruebas_mecanicas"].label = "Pruebas mecánicas (dureza + tensión)"
        self.fields["evidencia_fotografica"].label = "Evidencia fotográfica"
        self.fields["plano_original"].label = "Plano original"

        # Ayuda
        self.fields["pruebas_mecanicas"].help_text = "Sube un único documento (preferible PDF) que incluya ambas pruebas."

    class Meta:
        model = Lote
        fields = [
            "id_lote",
            "fecha",
            "numero_partes",
            "analisis_espectrometrico",
            "tolerancia_geometrica",
            "pruebas_mecanicas",
            "evidencia_fotografica",
            "plano_original",
        ]


# ----------------------------
# Lote (edición por admin: permite cambiar subido_por)
# ----------------------------
class LoteAdminForm(LoteForm):
    subido_por = forms.ModelChoiceField(
        queryset=get_user_model().objects.filter(is_active=True).order_by("username"),
        required=False,
        widget=forms.Select(attrs={"class": "form-select"}),
        label="Responsable (subido por)"
    )

    class Meta(LoteForm.Meta):
        fields = LoteForm.Meta.fields + ["subido_por"]


# ----------------------------
# Usuarios
# ----------------------------
class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = get_user_model()
        fields = ("username", "first_name", "last_name", "email")


class CustomAuthenticationForm(AuthenticationForm):
    username = UsernameField(
        widget=forms.TextInput(
            attrs={
                "autofocus": True,
                "class": "form-control",
                "placeholder": "Nombre de usuario",
            }
        )
    )
    password = forms.CharField(
        label="Contraseña",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Contraseña",
            }
        ),
    )
