from django.db import models
from django.contrib.auth.models import User
# Create your models here.

class TipoEvento(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True)

    def __str__(self):
        return self.nombre

class Evento(models.Model):
    ESTADO_CHOICES = [
        ('borrador', 'Borrador'),
        ('revision', 'En Revisión'),
        ('oficial', 'Oficial')
    ]
    
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField()
    fecha_inicio = models.DateTimeField()
    fecha_fin = models.DateTimeField()
    tipo_evento = models.ForeignKey(TipoEvento, on_delete=models.CASCADE)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='borrador')
    creador = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.titulo} - {self.fecha_inicio}"