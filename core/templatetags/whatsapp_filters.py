from django import template
import re

register = template.Library()


@register.filter
def whatsapp_url(telefono, codigo_pais="595"):
    """
    Limpia el teléfono y lo convierte en formato internacional para URL.
    Entrada: 0981-123 456 -> Salida: 595981123456
    """
    if not telefono:
        return ""

    numero_limpio = re.sub(r'\D', '', str(telefono))


    if numero_limpio.startswith('0'):
        numero_limpio = numero_limpio[1:]

    return f"{codigo_pais}{numero_limpio}"


@register.filter
def whatsapp_mensaje(cita):
    """
    Crea el texto del mensaje personalizado
    """
    texto = (
        f"Hola {cita.cliente.nombre}! %0A"
        f"Te recordamos tu cita en * Beauty Manager*:%0A"
        f"Fecha: {cita.fecha.strftime('%d/%m')}%0A"
        f"Hora: {cita.hora.strftime('%H:%M')} hs%0A"
        f"Servicio: {cita.servicio.nombre}%0A%0A"
        f"Por favor confirma tu asistencia. ¡Te esperamos! "
    )
    return texto