import os
import django
from django.conf import settings
from django.http import HttpResponse
from django.urls import path
from django.core.management import execute_from_command_line

# Define settings for Django
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
settings.configure(
    DEBUG=True,
    SECRET_KEY='your-secret-key',
    ROOT_URLCONF=__name__,
    MIDDLEWARE=[
        'django.middleware.common.CommonMiddleware',
    ],
    ALLOWED_HOSTS=['*'],
)

# A simple view function
def hello_world(request):
    return HttpResponse("Hello, World from main.py!")

# Define URL patterns
urlpatterns = [
    path('', hello_world),  # root URL maps to the hello_world view
]

if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'main')
    django.setup()
    execute_from_command_line(['manage.py', 'runserver', '127.0.0.1:8000'])
