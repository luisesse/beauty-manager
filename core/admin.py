from django.contrib import admin
from .models import Profesional, Cliente, Servicio, Cita, HorarioAtencion

# Mostrar en el Panel de control
admin.site.register(Profesional)
admin.site.register(Cliente)
admin.site.register(Servicio)
admin.site.register(Cita)
admin.site.register(HorarioAtencion)