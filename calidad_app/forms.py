from django import forms
from .models import Proyecto, Lote
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser

class ProyectoForm(forms.ModelForm):
    class Meta:
        model = Proyecto
        fields = ['nombre', 'descripcion', 'piezas_totales']

class LoteForm(forms.ModelForm):
    class Meta:
        model = Lote
        fields = [
            'id_lote',
            'numero_partes',
            'analisis_espectrometrico',
            'tolerancia_geometrica',
            'prueba_dureza',
            'prueba_tension',
            'evidencia_fotografica',
            'plano_original',
        ]

    def clean_numero_partes(self):
        """
        Valida que el número de partes no exceda el total de piezas del proyecto.
        """
        numero_partes = self.cleaned_data.get('numero_partes')
        proyecto = self.cleaned_data.get('proyecto')
        
        if proyecto:
            # Suma las piezas registradas en otros lotes
            piezas_registradas = Lote.objects.filter(proyecto=proyecto).exclude(id=self.instance.id).aggregate(
                total_piezas=models.Sum('numero_partes'))['total_piezas'] or 0
            
            # Verifica si el nuevo lote excede el total de piezas
            if (piezas_registradas + numero_partes) > proyecto.piezas_totales:
                raise forms.ValidationError(
                    f'El número de piezas excede el total permitido para el proyecto. ' 
                    f'Solo quedan {proyecto.piezas_totales - piezas_registradas} piezas disponibles.'
                )
        
        return numero_partes

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'password1', 'password2']
