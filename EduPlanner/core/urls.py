from django.urls import path
from core import views
from django.urls import path
from .views import TipoEventoListView
from .views import EventosAcademicosAPI

urlpatterns = [
    path('', views.home_view, name= 'home'),
    path('api/tipos-evento/', TipoEventoListView.as_view(), name='tipos-evento'),
    path('api/eventos/', EventosAcademicosAPI.as_view(), name='api-eventos'),
]
