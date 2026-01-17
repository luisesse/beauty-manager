from django.contrib import admin
from .models import Empresa, Profesional, Cliente, Servicio, Cita, HorarioAtencion, CategoriaGasto, Gasto



@admin.register(Profesional)
class ProfesionalAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'apellido', 'empresa', 'especialidad', 'porcentaje_comision')
    list_filter = ('empresa', 'especialidad')
    search_fields = ('nombre', 'apellido', 'empresa__nombre')



@admin.register(Cita)
class CitaAdmin(admin.ModelAdmin):
    # Qué columnas ver en la lista
    list_display = ('fecha', 'hora', 'cliente_nombre', 'servicio', 'profesional', 'estado_color', 'monto_cobrado',
                    'empresa')

    # Filtros laterales
    list_filter = ('empresa', 'estado', 'fecha', 'profesional')

    # Buscador
    search_fields = ('cliente__nombre', 'cliente__apellido')

    # Orden
    ordering = ('-fecha', 'hora')

    # Navegación rápida por fechas arriba
    date_hierarchy = 'fecha'

    # Función para mostrar nombre completo del cliente
    def cliente_nombre(self, obj):
        return f"{obj.cliente.nombre} {obj.cliente.apellido}"

    cliente_nombre.short_description = "Cliente"

    # Función para colorear el estado
    def estado_color(self, obj):
        if obj.estado == 'REALIZADO':
            return '🟢 Realizado'
        elif obj.estado == 'CANCELADO':
            return '🔴 Cancelado'
        elif obj.estado == 'CONFIRMADO':
            return '🔵 Confirmado'
        return '🟡 Pendiente'

    estado_color.short_description = "Estado"


admin.site.register(Empresa)
admin.site.register(Cliente)
admin.site.register(Servicio)
admin.site.register(HorarioAtencion)
admin.site.register(CategoriaGasto)
admin.site.register(Gasto)