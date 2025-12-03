from django.contrib import admin
from .models import Profesional, Cliente, Servicio, Cita

# Esto hace que aparezcan en el panel de control
admin.site.register(Profesional)
admin.site.register(Cliente)
admin.site.register(Servicio)
admin.site.register(Cita)
