from django.shortcuts import render, redirect
from django.shortcuts import render
from django.http import JsonResponse
import requests
from rest_framework import viewsets, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .models import TipoEvento, Evento, Api
from .serializers import TipoEventoSerializer, EventoSerializer, ApiSerializer


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
    
def Lista_Api(request):
    fechas = Api.objects.all()
    #return render(request, 'core/Lista_Api.html', {'fechas': fechas})
    return render(request, 'core/Lista_Api.html', {'fechas': fechas})

class FusionarApisView(APIView):
    def get(self, request):
        # **1. Obtener datos de la API externa (Calendarific)**
        api_url = "https://calendarific.com/api/v2/holidays"
        api_key = "h231T43X0Fj6UL5fexM1XsqlrMMvCvxW"
        params = {
            "api_key": api_key,
            "country": "CL",
            "year": 2024
        }

        # Lista para almacenar los datos externos
        external_data = []
        try:
            response = requests.get(api_url, params=params)
            if response.status_code == 200:
                external_data = response.json().get('response', {}).get('holidays', [])
            else:
                print(f"Error API externa: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"Error al conectar con la API externa: {e}")

        # **2. Obtener datos de tu API interna (base de datos local)**
        eventos = Api.objects.all()
        eventos_serializer = ApiSerializer(eventos, many=True)

        # **3. Fusionar datos**
        data_fusionada = {
            "eventos": eventos_serializer.data,
            "feriados_externos": external_data
        }

        # **4. Retornar respuesta combinada**
        return Response(data_fusionada)
    
def calendario_view(request):
    api_url = "http://127.0.0.1:8000/api/fusion-api/?format=json"  # Cambia la URL según tu configuración
    calendario = []

    try:
        response = requests.get(api_url)
        if response.status_code == 200:
            data = response.json()
            eventos = data.get('eventos', [])
            feriados_externos = data.get('feriados_externos', [])
            
            # Combinar y estandarizar los datos
            for evento in eventos:
                calendario.append({
                    'title': evento.get('title'),
                    'description': evento.get('description'),
                    'FechaInicio': evento.get('FechaInicio'),
                    'FechaTermino': evento.get('FechaTermino'),
                    'source': 'Interno'
                })

            for feriado in feriados_externos:
                calendario.append({
                    'title': feriado.get('name'),
                    'description': feriado.get('description'),
                    'FechaInicio': feriado.get('date', {}).get('iso'),
                    'FechaTermino': None,  # Los feriados no tienen fecha de término
                    'source': 'Externo'
                })
        else:
            print(f"Error al consumir la API: {response.status_code}")
    except Exception as e:
        print(f"Error al obtener el calendario: {e}")

    return render(request, 'core/Lista_Api.html', {'calendario': calendario})