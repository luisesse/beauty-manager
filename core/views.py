from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import ProtectedError, Sum
from datetime import date, datetime
from .models import Servicio, Cita,  Cliente, Profesional
from .forms import CitaForm, ServicioForm, ClienteForm, ProfesionalForm, CobrarCitaForm


@login_required
def listado_servicios(request):
    # 1. Vamos a la base de datos y traemos TODOS los servicios
    servicios = Servicio.objects.all().order_by('nombre')

    # 2. Preparamos una cajita de datos (contexto) para enviar al HTML
    contexto = {
        'mis_servicios': servicios
    }

    # 3. Renderizamos el HTML enviándole los datos
    return render(request, 'core/lista_servicios.html', contexto)

@login_required
def crear_servicio(request):
    if request.method == 'POST':
        form = ServicioForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('lista_servicios')
    else:
        form = ServicioForm()

    contexto = {
        'form': form,
        'titulo': 'Nuevo Servicio'
    }

    return render(request, 'core/form_servicio.html', contexto)

@login_required
def agendar_cita(request):
    if request.method == 'POST':
        # ESCENARIO 2: El usuario llenó el formulario y le dio a "Guardar"
        form = CitaForm(request.POST)
        if form.is_valid():
            form.save() # ¡Guarda en PostgreSQL mágicamente!
            return redirect('listado_citas')
    else:
        # ESCENARIO 1: El usuario solo quiere ver el formulario vacío (GET)
        form = CitaForm()

    contexto = {
        'form': form,
        'titulo': 'Agendar Cita'
    }

    return render(request, 'core/agendar_cita.html',  contexto)


@login_required
def editar_servicio(request, id):
    servicio = get_object_or_404(Servicio, pk=id)

    if request.method == 'POST':
        form = ServicioForm(request.POST, instance=servicio)
        if form.is_valid():
            form.save()
            return redirect('lista_servicios')
    else:
        form = ServicioForm(instance=servicio)

    contexto = {
        'form': form,
        'titulo': 'Editar Servicio'
    }

    return render(request, 'core/form_servicio.html', contexto)

@login_required
def eliminar_servicio(request, id):
    servicio = get_object_or_404(Servicio, pk=id)  # Buscamos al condenado

    if request.method == 'POST':
        # Si el usuario confirmó el formulario, procedemos a la ejecución
        servicio.delete()
        return redirect('lista_servicios')

    # Si no es POST, mostramos la página de "¿Estás seguro?"
    return render(request, 'core/eliminar_servicio.html', {'servicio': servicio})

@login_required
def home(request):
    # 1. Obtener la fecha de hoy
    hoy = date.today()

    # 2. FILTRAR: Trae solo las citas donde fecha es mayor o igual a hoy
    # 3. ORDENAR: Pon primero las más tempranas (hora)
    citas_hoy = Cita.objects.filter(fecha=hoy).order_by('hora')

    contexto = {
        'citas': citas_hoy,
        'fecha_actual': hoy
    }
    return render(request, 'core/home.html', contexto)

@login_required
def listado_clientes(request):
    clientes = Cliente.objects.all().order_by('nombre', 'apellido')
    return render(request, 'core/lista_clientes.html', {'clientes': clientes})

@login_required
def detalle_cliente(request, id):
    # Traemos al cliente o error 404
    cliente = get_object_or_404(Cliente, pk=id)

    # MAGIA: Traemos sus citas históricas ordenadas por fecha (de la más nueva a la vieja)
    historial = cliente.citas.all().order_by('-fecha')

    contexto = {
        'cliente': cliente,
        'historial': historial
    }
    return render(request, 'core/detalle_cliente.html', contexto)

@login_required
def crear_cliente(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            form.save()
            # Al guardar, nos vamos directo al listado de clientes
            return redirect('listado_clientes')
    else:
        form = ClienteForm()

    return render(request, 'core/form_cliente.html', {'form': form, 'titulo': 'Nuevo Cliente'})

def editar_cliente(request, id):
    # 1. Buscar el servicio. Si no existe el id 500, muestra error 404 automáticamente.
    cliente = get_object_or_404(Cliente, pk=id)

    if request.method == 'POST':

        form = ClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            form.save()
            return redirect('listado_clientes')
    else:
        # 3. (GET) Crear el formulario pre-rellenado con los datos de la base de datos
        form = ClienteForm(instance=cliente)

    contexto = {
        'form': form,
        'titulo': 'Editar Cliente'
    }
    return render(request, 'core/form_cliente.html', contexto)

@login_required
def eliminar_cliente(request, id):
    cliente = get_object_or_404(Cliente, pk=id)

    if request.method == 'POST':
        try:
            cliente.delete()
            return redirect('listado_clientes')
        except ProtectedError:
            # Si entra aquí, es porque el cliente tiene citas y la DB lo protegió.
            # No borramos nada y renderizamos la misma página pero con un error.
            error_msg = f"No se puede eliminar a {cliente.nombre} porque tiene citas registradas. Borra sus citas primero."
            return render(request, 'core/eliminar_cliente.html', {'cliente': cliente, 'error': error_msg})

    return render(request, 'core/eliminar_cliente.html', {'cliente': cliente})

@login_required
def listado_profesional(request):
    profesional = Profesional.objects.all().order_by('nombre', 'apellido')
    return render(request, 'core/lista_profesional.html', {'profesional': profesional})

@login_required
def crear_profesional(request):
    if request.method == 'POST':
        form = ProfesionalForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()

            return redirect('listado_profesional')
    else:
        form = ProfesionalForm()

    return render(request, 'core/form_profesional.html', {'form': form, 'titulo': 'Nuevo Profesional'})

def editar_profesional(request, id):
    # 1. Buscar el servicio. Si no existe el id 500, muestra error 404 automáticamente.
    profesional = get_object_or_404(Profesional, pk=id)

    if request.method == 'POST':

        form = ProfesionalForm(request.POST, request.FILES, instance=profesional)
        if form.is_valid():
            form.save()
            return redirect('listado_profesional')
    else:
        # 3. (GET) Crear el formulario pre-rellenado con los datos de la base de datos
        form = ProfesionalForm(instance=profesional)

    contexto = {
        'form': form,
        'titulo': 'Editar Profesional'
    }
    return render(request, 'core/form_profesional.html', contexto)

@login_required
def eliminar_profesional(request, id):
    profesional = get_object_or_404(Profesional, pk=id)

    if request.method == 'POST':
        try:
            profesional.delete()
            return redirect('listado_profesional')
        except ProtectedError:

            error_msg = f"No se puede eliminar a {profesional.nombre} porque tiene citas registradas. Borra sus citas primero."
            return render(request, 'core/eliminar_profesional.html', {'profesional': profesional, 'error': error_msg})

    return render(request, 'core/eliminar_profesional.html', {'profesional': profesional})


@login_required
def reporte_caja(request):
    # Valores por defecto: Hoy
    fecha_inicio = date.today()
    fecha_fin = date.today()

    # Si vienen datos en la URL (?fecha_inicio=...&fecha_fin=...)
    if request.GET.get('fecha_inicio') and request.GET.get('fecha_fin'):
        try:
            fecha_inicio = datetime.strptime(request.GET.get('fecha_inicio'), '%Y-%m-%d').date()
            fecha_fin = datetime.strptime(request.GET.get('fecha_fin'), '%Y-%m-%d').date()
        except ValueError:
            pass  # Si hay error de formato, nos quedamos con "hoy"

    # FILTRO POR RANGO (__range)
    # Buscamos citas realizadas ENTRE inicio y fin (inclusive)
    citas = Cita.objects.filter(
        fecha__range=[fecha_inicio, fecha_fin],
        estado='REALIZADO'
    ).order_by('fecha', 'hora')  # Ordenar cronológicamente

    total_ingresos = citas.aggregate(total=Sum('monto_cobrado'))['total'] or 0

    contexto = {
        'citas': citas,
        'total_ingresos': total_ingresos,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin
    }
    return render(request, 'core/reporte_caja.html', contexto)

@login_required
def editar_cita(request, id):
    cita = get_object_or_404(Cita, pk=id)

    if request.method == 'POST':
        form = CitaForm(request.POST, instance=cita)
        if form.is_valid():
            form.save()
            # Al terminar, volvemos al Dashboard (home) para seguir trabajando
            return redirect('home')
    else:
        form = CitaForm(instance=cita)

    contexto = {
        'form': form,
        'titulo': 'Gestión de Cita'
    }
    # Reutilizamos el template genérico que creamos para clientes (¡Reciclaje Pro!)
    # OJO: Si ese template tenía campos específicos manuales, mejor crea uno nuevo.
    # Si usaste {{ form.as_p }} o un loop genérico, funcionará perfecto.
    # Por seguridad, usemos 'core/form_cita.html' (crealo copiando el de agendar_cita.html)
    return render(request, 'core/agendar_cita.html', contexto)


@login_required
def listado_citas(request):
    # Traer citas desde HOY en adelante
    # Y que NO estén canceladas ni ya realizadas (solo las activas)
    citas = Cita.objects.filter(
        fecha__gte=date.today(),
        estado__in=['PENDIENTE', 'CONFIRMADO']
    ).order_by('fecha', 'hora')  # Ordenar por fecha y luego por hora

    return render(request, 'core/lista_citas.html', {'citas': citas})


@login_required
def finalizar_cita(request, id):
    cita = get_object_or_404(Cita, pk=id)

    if request.method == 'POST':
        form = CobrarCitaForm(request.POST, instance=cita)
        if form.is_valid():
            # 1. Guardamos el monto
            cita_final = form.save(commit=False)
            # 2. Forzamos el estado a REALIZADO (Lógica de negocio automática)
            cita_final.estado = 'REALIZADO'
            cita_final.save()
            return redirect('home')  # Volvemos al dashboard
    else:
        # Pre-llenamos el monto con lo que cuesta el servicio base
        form = CobrarCitaForm(instance=cita, initial={'monto_cobrado': cita.servicio.precio_estimado})

    contexto = {
        'form': form,
        'cita': cita  # Pasamos la cita para mostrar sus datos fijos
    }
    return render(request, 'core/finalizar_cita.html', contexto)

# Vista para cancelar (Botón X)
@login_required
def cancelar_cita(request, id):
    cita = get_object_or_404(Cita, pk=id)

    if request.method == 'POST':
        # Solo si el usuario confirmó en el formulario rojo
        cita.estado = 'CANCELADO'
        cita.save()
        return redirect('listado_citas')

    # Si es GET, le mostramos la pregunta
    return render(request, 'core/cancelar_cita.html', {'cita': cita})

# Vista para confirmar asistencia (Botón Check en Home)
@login_required
def confirmar_cita(request, id):
    cita = get_object_or_404(Cita, pk=id)
    cita.estado = 'CONFIRMADO'
    cita.save()
    return redirect('home') # Volvemos al dashboard de hoy

