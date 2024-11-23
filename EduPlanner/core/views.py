from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib.auth import logout
from django.shortcuts import redirect
import requests
from rest_framework import viewsets, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .models import TipoEvento, Evento
from .serializers import TipoEventoSerializer, EventoSerializer



def home_view(request):
    # URL de la API externa para obtener los feriados
    api_url = "https://calendarific.com/api/v2/holidays"
    api_key = "h231T43X0Fj6UL5fexM1XsqlrMMvCvxW"  # Cambia esto por tu clave de acceso a la API
    params = {
        "api_key": api_key,
        "country": "CL",  # Cambia esto si necesitas otro país
        "year": 2024      # Año para el cual se solicitarán los datos
    }

    # Variable para almacenar los datos de la API
    holidays = []

    try:
        # Llamada a la API
        response = requests.get(api_url, params=params)

        # Verificar si la respuesta fue exitosa
        if response.status_code == 200:
            holidays = response.json().get('response', {}).get('holidays', [])
        else:
            print(f"Error en la API: {response.status_code}, {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Error al conectar con la API: {e}")
    except Exception as e:
        print(f"Error inesperado: {e}")

    # Renderizar el template con los datos de los feriados
    return render(request, 'core/home.html', {'holidays': holidays})

class EventoViewSet(viewsets.ModelViewSet):
    queryset = Evento.objects.all()
    serializer_class = EventoSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAdminUser]
        else:
            permission_classes = [permissions.AllowAny]
        return [permission() for permission in permission_classes]

    @action(detail=False, methods=['get'])
    def calendario_consolidado(self, request):
        # Obtener eventos oficiales
        eventos = Evento.objects.filter(estado='oficial')
        eventos_serializer = EventoSerializer(eventos, many=True)
        
        # Llamar a API de feriados (ejemplo con Calendarific)
        try:
            holidays_response = requests.get('https://calendarific.com/api/v2/holidays', params={
                'api_key': 'h231T43X0Fj6UL5fexM1XsqlrMMvCvxW',
                'country': 'CL',
                'year': '2024'
            })
            holidays = holidays_response.json().get('response', {}).get('holidays', [])
        except Exception as e:
            holidays = []

        # Combinar eventos y feriados
        calendario = {
            'eventos': eventos_serializer.data,
            'feriados': holidays
        }
        
        return Response(calendario)


class TipoEventoListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tipos_evento = TipoEvento.objects.all()
        serializer = TipoEventoSerializer(tipos_evento, many=True)
        return Response(serializer.data)

class EventoListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        eventos = Evento.objects.filter(creador=request.user)
        serializer = EventoSerializer(eventos, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = EventoSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(creador=request.user)  # Asocia el usuario autenticado al evento
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)