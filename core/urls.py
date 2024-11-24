from django.urls import path
from core import views
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EventoViewSet
from .views import TipoEventoListView, EventoListCreateView
router = DefaultRouter()
router.register(r'eventos', EventoViewSet)

urlpatterns = [
    path('', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('home/', views.home_view, name= 'home'),
    path('logout/', views.logout_view, name='logout'),
    path('api/tipos-evento/', TipoEventoListView.as_view(), name='tipos-evento'),
    path('api/eventos/', EventoListCreateView.as_view(), name='eventos'),
]
