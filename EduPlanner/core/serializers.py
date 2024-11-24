from rest_framework import serializers
from .models import TipoEvento, Evento

class TipoEventoSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoEvento
        fields = ['id', 'nombre', 'descripcion']

class EventoSerializer(serializers.ModelSerializer):
    tipo_evento = serializers.CharField(source='tipo_evento.nombre', read_only=True)
    
    class Meta:
        model = Evento
        fields = [
            'id', 
            'titulo', 
            'descripcion', 
            'fecha_inicio', 
            'fecha_fin', 
            'tipo_evento',
            'estado',
            'creador'
        ]
        read_only_fields = ['creador', 'estado']

    def validate(self, data):
        # Validar que la fecha de fin no sea anterior a la fecha de inicio
        if data['fecha_fin'] < data['fecha_inicio']:
            raise serializers.ValidationError({
                "fecha_fin": "La fecha de fin no puede ser anterior a la fecha de inicio"
            })
        return data