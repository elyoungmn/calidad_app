
import threading
from django.utils.deprecation import MiddlewareMixin

_user_storage = threading.local()

def get_current_user():
    return getattr(_user_storage, 'user', None)

class CurrentUserMiddleware(MiddlewareMixin):
    def process_request(self, request):
        _user_storage.user = getattr(request, 'user', None)
