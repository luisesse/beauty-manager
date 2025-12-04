from django.db import models


class Profesional(models.Model):
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    especialidad = models.CharField(max_length=100, blank=True, null=True)
    telefono = models.CharField(max_length=20)
    imagen = models.ImageField(upload_to='profesionales/', blank=True, null=True)

    def __str__(self):
        return f"{self.nombre} {self.apellido})"

    def save(self, *args, **kwargs):
        # Antes de guardar, convertimos a Título o Mayúsculas
        self.nombre = self.nombre.title()
        self.apellido = self.apellido.title()
        self.especialidad = self.especialidad.title()

        # self.nombre = self.nombre.upper()

        super().save(*args, **kwargs)

        class Meta:
            ordering = ['nombre', 'apellido']


class Cliente(models.Model):
    # Agregamos unique=True para evitar duplicados de personas
    ci_ruc = models.CharField(max_length=20, unique=True, verbose_name="C.I. o RUC")
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    telefono = models.CharField(max_length=20)
    email = models.EmailField(blank=True, null=True)

    def __str__(self):
        return f"{self.nombre} {self.apellido} ({self.ci_ruc})"

    def save(self, *args, **kwargs):
        self.nombre = self.nombre.title()
        self.apellido = self.apellido.title()

        super().save(*args, **kwargs)

    class Meta:
        ordering = ['nombre', 'apellido']


class Servicio(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    # Precio sin decimales (PyG)
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
    # Relaciones (Foreign Keys)
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name='citas')
    profesional = models.ForeignKey(Profesional, on_delete=models.PROTECT, related_name='citas')
    servicio = models.ForeignKey(Servicio, on_delete=models.PROTECT)

    # Datos propios de la cita
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

    def __str__(self):
        return f"Cita: {self.cliente} - {self.fecha} {self.hora}"

    def save(self, *args, **kwargs):
        # Si no hay monto cobrado y la cita se marca como REALIZADO o CONFIRMADO...
        if not self.monto_cobrado and self.servicio:
            # Usamos el precio del catálogo como sugerencia inicial
            self.monto_cobrado = self.servicio.precio_estimado

        super().save(*args, **kwargs)


class HorarioAtencion(models.Model):
    DIAS_SEMANA = [
        (0, 'Lunes'),
        (1, 'Martes'),
        (2, 'Miércoles'),
        (3, 'Jueves'),
        (4, 'Viernes'),
        (5, 'Sábado'),
        (6, 'Domingo'),
    ]

    dia_semana = models.IntegerField(choices=DIAS_SEMANA, unique=True)
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    abierto = models.BooleanField(default=True)

    def __str__(self):
        estado = "Abierto" if self.abierto else "Cerrado"
        return f"{self.get_dia_semana_display()}: {estado} ({self.hora_inicio} - {self.hora_fin})"

    class Meta:
        ordering = ['dia_semana']
