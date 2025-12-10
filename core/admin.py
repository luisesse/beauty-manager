from django.contrib import admin
from .models import Empresa, Profesional, Cliente, Servicio, Cita, HorarioAtencion, CategoriaGasto, Gasto

# Mostrar en el Panel de control
admin.site.register(Empresa)
admin.site.register(Profesional)
admin.site.register(Cliente)
admin.site.register(Servicio)
admin.site.register(Cita)
admin.site.register(HorarioAtencion)
admin.site.register(CategoriaGasto)
admin.site.register(Gasto)