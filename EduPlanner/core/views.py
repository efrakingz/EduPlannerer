from rest_framework import viewsets, permissions, status
import requests
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from .serializers import TipoEventoSerializer, EventoSerializer
from django.db.models import Q
from django.shortcuts import render, redirect
from rest_framework.decorators import action
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import logout, authenticate, login
from .models import TipoEvento, Evento
from rest_framework.response import Response
from datetime import datetime

def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        try:
            # lo aue hace es buscar el usuario por email y obtiene su username
            username = User.objects.get(email=email).username
        except User.DoesNotExist:
            username = None

        user = authenticate(request, username=username, password=password)

        if user is not None:
            # Verifica si el usuario es superusuario (admin)
            if user.is_superuser:
                messages.error(request, 'Acceso denegado para usuarios admin. Usa el panel administrativo.')
                return redirect('login')  # Redirige al login de usuarios comunes
            else:
                login(request, user)
                return redirect('home')  # Redirige al home de usuarios comunes
        else:
            messages.error(request, 'Email o contraseña incorrectos.')

    return render(request, 'core/login.html')

# Registrar Usuario
def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        # Validadaciones
        if not username or not email or not password or not confirm_password:
            messages.error(request, 'Todos los campos son obligatorios.')
            return render(request, 'core/register.html')

        if password != confirm_password:
            messages.error(request, 'Las contraseñas no coinciden.')
            return render(request, 'core/register.html')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'El nombre de usuario ya está en uso.')
            return render(request, 'core/register.html')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'El email ya está en uso.')
            return render(request, 'core/register.html')

        # Crear el usuario
        try:
            user = User.objects.create_user(username=username, email=email, password=password)
            user.save()
            messages.success(request, '¡Cuenta creada con éxito! Ahora puedes iniciar sesión.')
            return redirect('login')
        except Exception as e:
            messages.error(request, 'Hubo un error al crear la cuenta. Por favor, inténtalo de nuevo.')
            return render(request, 'core/register.html')

    return render(request, 'core/register.html')

def logout_view(request):
    logout(request)
    return redirect('core/login.html')

 # Clase para fusionar la Api Externa y la Api Local
class EventosAcademicosAPI(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        # Obtener eventos académicos
        eventos = Evento.objects.filter(Q(estado='oficial') | Q(creador=request.user))
        eventos_serializer = EventoSerializer(eventos, many=True)
        
        # Obtener feriados desde Calendarific
        api_url = "https://calendarific.com/api/v2/holidays"
        api_key = "h231T43X0Fj6UL5fexM1XsqlrMMvCvxW"
        params = {
            "api_key": api_key,
            "country": "CL",
            "year": datetime.now().year
        }
        
        feriados = []
        try:
            response = requests.get(api_url, params=params)
            if response.status_code == 200:
                feriados_data = response.json().get('response', {}).get('holidays', [])
                
                feriados = [
                    {
                        "titulo": f["name"],
                        "descripcion": "Feriado Nacional" if "national" in f.get("type", [""])[0].lower() else "Feriado Regional",
                        "fecha_inicio": f["date"]["iso"],
                        "fecha_fin": f["date"]["iso"],
                        "tipo_evento": "Feriado Nacional" if "national" in f.get("type", [""])[0].lower() else "Feriado Regional"
                    }
                    for f in feriados_data
                ]
            else:
                print(f"Error en la API Calendarific: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Error al conectar con Calendarific: {e}")
        
        # Fusionar eventos y feriados
        calendario = eventos_serializer.data + feriados
        calendario = sorted(calendario, key=lambda x: x["fecha_inicio"])
        
        return Response(calendario)
    
    def post(self, request):
        if not request.user.is_staff:
            return Response(
                {"error": "No tienes permiso para crear eventos."}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = EventoSerializer(data=request.data)
        if serializer.is_valid():
            evento = serializer.validated_data
            
            api_url = "https://calendarific.com/api/v2/holidays"
            params = {
                "api_key": "h231T43X0Fj6UL5fexM1XsqlrMMvCvxW",
                "country": "CL",
                "year": evento["fecha_inicio"].year
            }
            
            try:
                response = requests.get(api_url, params=params)
                if response.status_code == 200:
                    feriados = response.json().get('response', {}).get('holidays', [])
                    conflictos = [
                        f for f in feriados
                        if f["date"]["iso"] >= str(evento["fecha_inicio"]) and 
                        f["date"]["iso"] <= str(evento["fecha_fin"])
                    ]
                    
                    if conflictos:
                        return Response({
                            "error": "Conflicto con feriados.",
                            "conflictos": [f["name"] for f in conflictos],
                            "mensaje": "¿Desea continuar con la creación del evento a pesar del conflicto?"
                        }, status=status.HTTP_409_CONFLICT)
                    
            except requests.exceptions.RequestException as e:
                print(f"Error al conectar con Calendarific: {e}")
            
            # Guardar evento
            evento = serializer.save(
                creador=request.user,
                estado='pendiente' if request.user.is_staff else 'oficial'
            )
            
            return Response(EventoSerializer(evento).data, status=status.HTTP_201_CREATED)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@login_required
def mostrar_eventos(request):
    api_url = "http://localhost:8000/api/eventos/"
    
    try:
        response = requests.get(api_url, cookies=request.COOKIES)  
        if response.status_code == 200:
            eventos = response.json()
        else:
            eventos = []
            print(f"Error al obtener eventos: {response.status_code}")
    except requests.exceptions.RequestException as e:
        eventos = []
        print(f"Error de conexión: {e}")
    
    # Renderiza los datos en el template
    return render(request, 'core/home.html', {"eventos": eventos})


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
            serializer.save(creador=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    













# No afectan al proyecto, pero no las borro porsiacaso
'''def home_view(request):
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
    return render(request, 'core/home.html', {'holidays': holidays})'''




'''class EventoViewSet(viewsets.ModelViewSet):
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
        
        return Response(calendario)'''