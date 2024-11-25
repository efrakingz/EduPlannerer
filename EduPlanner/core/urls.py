from django.urls import path
from core import views
from .views import TipoEventoListView
from .views import EventosAcademicosAPI, mostrar_eventos

urlpatterns = [
    path('', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    #path('home/', views.home_view, name= 'home'),
    path('home/', views.mostrar_eventos, name= 'home'),
    path('logout/', views.logout_view, name='logout'),
    path('api/tipos-evento/', TipoEventoListView.as_view(), name='tipos-evento'),
    path('api/eventos/', EventosAcademicosAPI.as_view(), name='api-eventos'),
]
