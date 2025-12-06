from django import forms
from django.core.exceptions import ValidationError
from .models import Cita, Servicio, Cliente, Profesional, HorarioAtencion, Gasto
from datetime import date, datetime


class CitaForm(forms.ModelForm):
    class Meta:
        model = Cita
        fields = ['cliente', 'profesional', 'servicio', 'fecha', 'hora']
        # 'form-control-sm' para hacerlos compactos
        widgets = {
            'fecha': forms.DateInput(format='%Y-%m-%d',attrs={'type': 'date', 'class': 'form-control form-control-sm'}),
            'hora': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control form-control-sm'}),
            'cliente': forms.Select(attrs={'class': 'form-select select2'}),
            'profesional': forms.Select(attrs={'class': 'form-select select2'}),
            'servicio': forms.Select(attrs={'class': 'form-select select2'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        fecha = cleaned_data.get('fecha')
        hora = cleaned_data.get('hora')
        profesional = cleaned_data.get('profesional')

        # Si falta algún dato básico, salimos.
        if not (fecha and hora and profesional):
            return

        # --- VALIDACIÓN 1: NO VIAJAR AL PASADO ---
        hoy = date.today()

        # A. Si la fecha es anterior a hoy (ayer, antes de ayer, etc...)
        if fecha < hoy:
            raise ValidationError("No se pueden agendar citas en fechas pasadas.")

        # B. Si la fecha es HOY, pero la hora ya pasó (ohasama la hora)
        if fecha == hoy:
            hora_actual = datetime.now().time()
            if hora < hora_actual:
                raise ValidationError("La hora seleccionada ya ha pasado.")

        # 2. VALIDAR DÍAS Y HORARIOS DE ATENCIÓN
        dia_semana = fecha.weekday()  # 0=Lunes, 6=Domingo

        try:
            # Buscamos la regla para ese día específico en la BD
            horario = HorarioAtencion.objects.get(dia_semana=dia_semana)
        except HorarioAtencion.DoesNotExist:
            # Si por error no configuraron el día en el admin, asumimos cerrado por seguridad
            raise ValidationError("No hay horario configurado para este día.")

        # Regla A: Dias de atención.
        if not horario.abierto:
            raise ValidationError(f"El salón permanece cerrado los {horario.get_dia_semana_display()}´s.")

        # Regla B: Horarios (Comparamos objetos TimeField directamente)
        # Nota: hora es un objeto time (ej: 17:30), horario.hora_inicio también.
        if not (horario.hora_inicio <= hora < horario.hora_fin):
            raise ValidationError(
                f"El horario de atención los {horario.get_dia_semana_display()}´s es de "
                f"{horario.hora_inicio.strftime('%H:%M')} a {horario.hora_fin.strftime('%H:%M')}."
            )

        # --- VALIDACIÓN 2: DISPONIBILIDAD  ---
        citas_coincidentes = Cita.objects.filter(
            profesional=profesional,
            fecha=fecha,
            hora=hora
        ).exclude(estado='CANCELADO')

        if self.instance.pk:
            citas_coincidentes = citas_coincidentes.exclude(pk=self.instance.pk)

        if citas_coincidentes.exists():
            raise ValidationError(
                f"El profesional {profesional} ya tiene una cita agendada a las {hora}."
            )

            # Opcional: error pegado al campo 'hora':
            # self.add_error('hora', 'Horario no disponible para este estilista')

class CobrarCitaForm(forms.ModelForm):
    class Meta:
        model = Cita
        fields = ['monto_cobrado', 'metodo_pago']
        widgets = {
            'monto_cobrado': forms.NumberInput(attrs={
                'class': 'form-control form-control-lg text-center fw-bold text-success',
                'placeholder': 'Ingrese monto'
            }),
            'metodo_pago': forms.Select(attrs={
                'class': 'form-select form-select-lg text-center'
            }),
        }

class ServicioForm(forms.ModelForm):
    class Meta:
        model = Servicio
        fields = ['nombre', 'descripcion', 'precio_estimado', 'duracion_minutos']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'precio_estimado': forms.NumberInput(attrs={'class': 'form-control'}),
            'duracion_minutos': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['nombre', 'apellido', 'telefono', 'ci_ruc', 'email']
        widgets = {
            'ci_ruc': forms.TextInput(attrs={'class': 'form-control'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'apellido': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

class ProfesionalForm(forms.ModelForm):
    class Meta:
        model = Profesional
        fields = ['nombre', 'apellido', 'especialidad', 'telefono', 'imagen', 'usuario', 'porcentaje_comision']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'apellido': forms.TextInput(attrs={'class': 'form-control'}),
            'especialidad': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'usuario': forms.Select(attrs={'class': 'form-select select2'}),
            'porcentaje_comision': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '100',
                'placeholder': 'Ej: 50'
            }),
            'imagen': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

# Formularios de Gastos

class GastoForm(forms.ModelForm):
    class Meta:
        model = Gasto
        fields = ['descripcion', 'monto', 'fecha', 'categoria']
        widgets = {
            'descripcion': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Pago de Luz Ande'}),
            'monto': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Ingrese monto'}),
            'fecha': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'class': 'form-control'}),
            'categoria': forms.Select(attrs={'class': 'form-select select2'}),
        }