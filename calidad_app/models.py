from django.db import models
from django.contrib.auth.models import AbstractUser

# Usuario personalizado
class CustomUser(AbstractUser):
    pass

# Perfil del usuario
class PerfilUsuario(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)

    def __str__(self):
        return self.user.username

# Proyecto
class Proyecto(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    piezas_totales = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.nombre

    def calcular_avance(self):
        """
        Calcula el porcentaje de avance del proyecto basado en las piezas registradas en lotes.
        """
        if self.piezas_totales == 0:
            return 0
        
        # Suma total de piezas en todos los lotes del proyecto
        piezas_registradas = self.lote_set.aggregate(total_piezas=models.Sum('numero_partes'))['total_piezas'] or 0
        
        # Calcula el porcentaje de avance
        avance = (piezas_registradas / self.piezas_totales) * 100
        return round(avance, 2)

# Lote
class Lote(models.Model):
    proyecto = models.ForeignKey(Proyecto, on_delete=models.CASCADE)
    id_lote = models.CharField(max_length=20, unique=True)
    numero_partes = models.PositiveIntegerField()
    analisis_espectrometrico = models.FileField(upload_to='analisis/', default='archivos/archivo_vacio.pdf')
    tolerancia_geometrica = models.FileField(upload_to='tolerancias/', default='archivos/archivo_vacio.pdf')
    prueba_dureza = models.FileField(upload_to='dureza/', default='archivos/archivo_vacio.pdf')
    prueba_tension = models.FileField(upload_to='tension/', default='archivos/archivo_vacio.pdf')
    evidencia_fotografica = models.FileField(upload_to='fotos/', default='archivos/archivo_vacio.pdf')
    plano_original = models.FileField(upload_to='planos/', default='archivos/archivo_vacio.pdf')
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.id_lote
