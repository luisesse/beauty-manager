from django import forms
from django.core.exceptions import ValidationError
from .models import Cita, Servicio, Cliente, Profesional
from datetime import date, datetime


class CitaForm(forms.ModelForm):
    class Meta:
        model = Cita
        fields = ['cliente', 'profesional', 'servicio', 'fecha', 'hora']
        # Agregamos 'form-control-sm' para hacerlos compactos
        widgets = {
            'fecha': forms.DateInput(format='%Y-%m-%d',attrs={'type': 'date', 'class': 'form-control form-control-sm'}),
            'hora': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control form-control-sm'}),
            'cliente': forms.Select(attrs={'class': 'form-select form-select-sm'}),
            'profesional': forms.Select(attrs={'class': 'form-select form-select-sm'}),
            'servicio': forms.Select(attrs={'class': 'form-select form-select-sm'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        fecha = cleaned_data.get('fecha')
        hora = cleaned_data.get('hora')
        profesional = cleaned_data.get('profesional')

        # Si falta algún dato básico, salimos (ya lo manejan los validadores por defecto)
        if not (fecha and hora and profesional):
            return

        # --- VALIDACIÓN 1: NO VIAJAR AL PASADO ---
        hoy = date.today()

        # A. Si la fecha es anterior a hoy (ayer, antes de ayer...)
        if fecha < hoy:
            raise ValidationError("No se pueden agendar citas en fechas pasadas.")

        # B. Si la fecha es HOY, pero la hora ya pasó
        if fecha == hoy:
            hora_actual = datetime.now().time()
            if hora < hora_actual:
                raise ValidationError("La hora seleccionada ya ha pasado.")

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

            # Opcional: Si quieres que el error salga pegado al campo 'hora':
            # self.add_error('hora', 'Horario no disponible para este estilista')

class CobrarCitaForm(forms.ModelForm):
    class Meta:
        model = Cita
        fields = ['monto_cobrado'] # Solo nos interesa la plata
        widgets = {
            'monto_cobrado': forms.NumberInput(attrs={
                'class': 'form-control form-control-lg text-center fw-bold text-success',
                'placeholder': 'Ingrese monto'
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
        fields = ['nombre', 'apellido', 'especialidad', 'telefono', 'imagen'] # <--- Agrega imagen
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'apellido': forms.TextInput(attrs={'class': 'form-control'}),
            'especialidad': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            # El widget de imagen ya es automático, pero puedes ponerle clase si quieres
            'imagen': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }