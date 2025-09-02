from .models import Proyecto

def proyectos_disponibles(request):
    if request.user.is_authenticated:
        return {
            'proyectos': Proyecto.objects.all()
        }
    return {}
