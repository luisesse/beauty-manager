from django.db import models
from datetime import date
from django.contrib.auth.models import User


# Crear Empresas.
class Empresa(models.Model):
    nombre = models.CharField(max_length=100, verbose_name="Nombre de la Peluquería")
    direccion = models.CharField(max_length=200, blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    activo = models.BooleanField(default=True)  # Para desactivar clientes que no pagan
    creado_el = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Empresa (Peluquería)"
        verbose_name_plural = "Empresas"


class Profesional(models.Model):
    # Vinculamos al profesional con UNA empresa específica
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name="profesionales")

    usuario = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    especialidad = models.CharField(max_length=100, blank=True, null=True)
    telefono = models.CharField(max_length=20)
    imagen = models.ImageField(upload_to='profesionales/', blank=True, null=True)
    porcentaje_comision = models.IntegerField(
        default=50,
        verbose_name="Porcentaje de Comisión (%)"
    )

    def __str__(self):
        return f"{self.nombre} {self.apellido} ({self.empresa.nombre})"

    def save(self, *args, **kwargs):
        self.nombre = self.nombre.title()
        self.apellido = self.apellido.title()
        if self.especialidad:
            self.especialidad = self.especialidad.title()
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['nombre', 'apellido']


class Cliente(models.Model):
    # El cliente pertenece a una empresa
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name="clientes")


    ci_ruc = models.CharField(max_length=20, verbose_name="C.I. o RUC")

    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    telefono = models.CharField(max_length=20)
    email = models.EmailField(blank=True, null=True)

    def __str__(self):
        return f"{self.nombre} {self.apellido}"

    def save(self, *args, **kwargs):
        self.nombre = self.nombre.title()
        self.apellido = self.apellido.title()
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['nombre', 'apellido']
        #  La combinación Empresa + CI debe ser única.
        # Mismo CI existe en diferentes empresas.
        unique_together = [['empresa', 'ci_ruc']]


class Servicio(models.Model):

    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name="servicios")

    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    precio_estimado = models.DecimalField(max_digits=10, decimal_places=0)
    duracion_minutos = models.PositiveIntegerField(default=30)

    def __str__(self):
        return f"{self.nombre} - {self.precio_estimado} Gs"

    def save(self, *args, **kwargs):
        self.nombre = self.nombre.title()
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['nombre']


class Cita(models.Model):
    METODOS_PAGO = [
        ('EFECTIVO', 'Efectivo'),
        ('TRANSFERENCIA', 'Transferencia / QR'),
        ('TARJETA', 'Tarjeta de Débito/Crédito'),
        ('CHEQUE', 'Cheque'),
        ('OTRO', 'Otro'),
    ]

    # La cita también debe saber de quién es, para filtrar reportes rápido
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name="citas")

    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name='citas')
    profesional = models.ForeignKey(Profesional, on_delete=models.PROTECT, related_name='citas')
    servicio = models.ForeignKey(Servicio, on_delete=models.PROTECT)

    fecha = models.DateField()
    hora = models.TimeField()
    monto_cobrado = models.DecimalField(max_digits=10, decimal_places=0, null=True, blank=True)
    estado = models.CharField(
        max_length=20,
        choices=[
            ('PENDIENTE', 'Pendiente'),
            ('CONFIRMADO', 'Confirmado'),
            ('REALIZADO', 'Realizado'),
            ('CANCELADO', 'Cancelado')
        ],
        default='PENDIENTE'
    )
    metodo_pago = models.CharField(max_length=20, choices=METODOS_PAGO, default='EFECTIVO')

    def __str__(self):
        return f"Cita: {self.cliente} - {self.fecha} {self.hora}"

    def save(self, *args, **kwargs):
        if not self.monto_cobrado and self.servicio:
            self.monto_cobrado = self.servicio.precio_estimado
        super().save(*args, **kwargs)


class HorarioAtencion(models.Model):

    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name="horarios")

    DIAS_SEMANA = [
        (0, 'Lunes'), (1, 'Martes'), (2, 'Miércoles'), (3, 'Jueves'),
        (4, 'Viernes'), (5, 'Sábado'), (6, 'Domingo'),
    ]

    dia_semana = models.IntegerField(choices=DIAS_SEMANA)
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    abierto = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.get_dia_semana_display()}"

    class Meta:
        ordering = ['dia_semana']
        # Cada empresa tiene su lunes, martes, etc.
        unique_together = [['empresa', 'dia_semana']]


class CategoriaGasto(models.Model):

    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name="categorias_gasto")

    nombre = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre

    class Meta:
        ordering = ['nombre']

        unique_together = [['empresa', 'nombre']]


class Gasto(models.Model):

    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name="gastos")

    descripcion = models.CharField(max_length=200)
    monto = models.DecimalField(max_digits=10, decimal_places=0)
    fecha = models.DateField(default=date.today)
    categoria = models.ForeignKey(CategoriaGasto, on_delete=models.PROTECT)

    def __str__(self):
        return f"{self.descripcion} - {self.monto} Gs."

    class Meta:
        ordering = ['-fecha', '-id']