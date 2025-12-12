from django.contrib import admin
from .models import Empresa, Profesional, Cliente, Servicio, Cita, HorarioAtencion, CategoriaGasto, Gasto


class ProfesionalAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'apellido', 'empresa', 'especialidad')
    list_filter = ('empresa', 'especialidad')
    search_fields = ('nombre', 'apellido', 'empresa__nombre')

# Mostrar en el Panel de control
admin.site.register(Empresa)
admin.site.register(Profesional, ProfesionalAdmin)
admin.site.register(Cliente)
admin.site.register(Servicio)
admin.site.register(Cita)
admin.site.register(HorarioAtencion)
admin.site.register(CategoriaGasto)
admin.site.register(Gasto)
