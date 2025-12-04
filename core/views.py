from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import ProtectedError, Sum, Q
from django.contrib import messages
from datetime import date, datetime
from .models import Servicio, Cita,  Cliente, Profesional, Gasto
from .forms import CitaForm, ServicioForm, ClienteForm, ProfesionalForm, CobrarCitaForm, GastoForm


@login_required
def listado_servicios(request):
    busqueda = request.GET.get('q')

    if busqueda:

        servicios = Servicio.objects.filter(
            Q(nombre__icontains=busqueda)
        ).order_by('nombre')
    else:

        servicios = Servicio.objects.all().order_by('nombre')

    contexto = {
        'mis_servicios': servicios
    }

    return render(request, 'core/lista_servicios.html', contexto)

@login_required
def crear_servicio(request):
    if request.method == 'POST':
        form = ServicioForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, f'¡Servicio {form.instance.nombre} se creó correctamente!')
            return redirect('lista_servicios')
    else:
        form = ServicioForm()

    contexto = {
        'form': form,
        'titulo': 'Nuevo Servicio'
    }

    return render(request, 'core/form_servicio.html', contexto)

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
    servicio = get_object_or_404(Servicio, pk=id)

    if request.method == 'POST':

        servicio.delete()
        messages.warning(request, f'El Servicio {servicio.nombre} ha sido eliminado permanentemente.')
        return redirect('lista_servicios')

    # Si no es POST, mostramos la página de "¿Estás seguro?"
    return render(request, 'core/eliminar_servicio.html', {'servicio': servicio})

@login_required
def home(request):

    hoy = date.today()

    citas_hoy = Cita.objects.filter(fecha=hoy).order_by('hora')

    contexto = {
        'citas': citas_hoy,
        'fecha_actual': hoy
    }
    return render(request, 'core/home.html', contexto)

@login_required
def listado_clientes(request):

    busqueda = request.GET.get('q')

    if busqueda:

        clientes = Cliente.objects.filter(
            Q(nombre__icontains=busqueda) |
            Q(apellido__icontains=busqueda) |
            Q(ci_ruc__icontains=busqueda)
        ).order_by('nombre', 'apellido')
    else:

        clientes = Cliente.objects.all().order_by('nombre', 'apellido')

    return render(request, 'core/lista_clientes.html', {'clientes': clientes})

@login_required
def detalle_cliente(request, id):

    cliente = get_object_or_404(Cliente, pk=id)

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
            messages.success(request, f'¡El cliente {form.instance.nombre} se creó correctamente!')

            return redirect('listado_clientes')
    else:
        form = ClienteForm()

    return render(request, 'core/form_cliente.html', {'form': form, 'titulo': 'Nuevo Cliente'})

def editar_cliente(request, id):

    cliente = get_object_or_404(Cliente, pk=id)

    if request.method == 'POST':

        form = ClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            form.save()
            return redirect('listado_clientes')
    else:

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
            messages.warning(request, f'El cliente {cliente.nombre} ha sido eliminado permanentemente.')
            return redirect('listado_clientes')
        except ProtectedError:
            # Si entra aquí, es porque el cliente tiene citas y la DB lo protegió.
            # No borramos nada y renderizamos la misma página pero con un error.
            messages.error(request, f'No se puede eliminar: El cliente {cliente.nombre} tiene citas registradas.')
            return render(request, 'core/eliminar_cliente.html', {'cliente': cliente, 'error': messages.error})

    return render(request, 'core/eliminar_cliente.html', {'cliente': cliente})

@login_required
def listado_profesional(request):
    busqueda = request.GET.get('q')

    if busqueda:

        profesional = Profesional.objects.filter(
            Q(nombre__icontains=busqueda) |
            Q(apellido__icontains=busqueda) |
            Q(especialidad__icontains=busqueda)
        ).order_by('nombre', 'apellido')
    else:

        profesional = Profesional.objects.all().order_by('nombre', 'apellido')

    return render(request, 'core/lista_profesional.html', {'profesional': profesional})

@login_required
def crear_profesional(request):
    if request.method == 'POST':
        form = ProfesionalForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, f'¡El profesional {form.instance.nombre} se creó correctamente!')

            return redirect('listado_profesional')
    else:
        form = ProfesionalForm()

    return render(request, 'core/form_profesional.html', {'form': form, 'titulo': 'Nuevo Profesional'})

def editar_profesional(request, id):

    profesional = get_object_or_404(Profesional, pk=id)

    if request.method == 'POST':

        form = ProfesionalForm(request.POST, request.FILES, instance=profesional)
        if form.is_valid():
            form.save()
            return redirect('listado_profesional')
    else:

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
            messages.warning(request, f'El profesional {profesional.nombre} ha sido eliminado permanentemente.')
            return redirect('listado_profesional')
        except ProtectedError:

            messages.error(request,f'No se puede eliminar, el profesional {profesional.nombre} tiene citas registradas.')
            return render(request, 'core/eliminar_profesional.html', {'profesional': profesional, 'error': messages.error})

    return render(request, 'core/eliminar_profesional.html', {'profesional': profesional})


#---Vistas de Citas---

@login_required
def agendar_cita(request):
    if request.method == 'POST':

        form = CitaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '¡La cita se creó correctamente!')
            return redirect('listado_citas')
    else:

        form = CitaForm()

    contexto = {
        'form': form,
        'titulo': 'Agendar Cita'
    }

    return render(request, 'core/agendar_cita.html',  contexto)

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

    return render(request, 'core/agendar_cita.html', contexto)


@login_required
def listado_citas(request):
    # Traer citas activas desde HOY en adelante
    # Y que no estén canceladas ni realizadas
    citas = Cita.objects.filter(
        fecha__gte=date.today(),
        estado__in=['PENDIENTE', 'CONFIRMADO']
    ).order_by('fecha', 'hora')

    busqueda = request.GET.get('q')
    if busqueda:
        citas = citas.filter(
            Q(cliente__nombre__icontains=busqueda) |
            Q(cliente__apellido__icontains=busqueda) |
            Q(profesional__nombre__icontains=busqueda)
        )

    return render(request, 'core/lista_citas.html', {'citas': citas})


@login_required
def finalizar_cita(request, id):
    cita = get_object_or_404(Cita, pk=id)

    if request.method == 'POST':
        form = CobrarCitaForm(request.POST, instance=cita)
        if form.is_valid():
            # 1. Guardamos el monto
            cita_final = form.save(commit=False)
            # 2. Forzamos el estado a REALIZADO
            cita_final.estado = 'REALIZADO'
            cita_final.save()
            messages.success(request, '¡Cobro registrado exitosamente!')
            return redirect('home')
    else:
        # Pre-llenamos el monto con lo que cuesta el servicio base
        form = CobrarCitaForm(instance=cita, initial={'monto_cobrado': cita.servicio.precio_estimado})

    contexto = {
        'form': form,
        'cita': cita  # Pasamos la cita para mostrar sus datos fijos
    }
    return render(request, 'core/finalizar_cita.html', contexto)


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


@login_required
def confirmar_cita(request, id):
    cita = get_object_or_404(Cita, pk=id)
    cita.estado = 'CONFIRMADO'
    cita.save()
    return redirect('home')

#---Vista de Caja---

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

    # INGRESOS
    citas = Cita.objects.filter(
        fecha__range=[fecha_inicio, fecha_fin],
        estado='REALIZADO'
    ).order_by('fecha', 'hora')

    total_ingresos = citas.aggregate(total=Sum('monto_cobrado'))['total'] or 0

    # 2. EGRESOS
    gastos = Gasto.objects.filter(
        fecha__range=[fecha_inicio, fecha_fin]
    ).order_by('fecha')

    total_egresos = gastos.aggregate(total=Sum('monto'))['total'] or 0

    saldo_neto = total_ingresos - total_egresos

    contexto = {
        'citas': citas,
        'gastos': gastos,
        'total_ingresos': total_ingresos,
        'total_egresos': total_egresos,
        'saldo_neto': saldo_neto,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin
    }
    return render(request, 'core/reporte_caja.html', contexto)


#---Vistas de Gastos---

@login_required
def lista_gastos(request):
    gastos = Gasto.objects.all().order_by('-fecha', '-id')
    return render(request, 'core/lista_gastos.html', {'gastos': gastos})

@login_required
def crear_gasto(request):
    if request.method == 'POST':
        form = GastoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Gasto registrado correctamente.')
            return redirect('lista_gastos')
    else:
        # Sugerimos la fecha de hoy por defecto
        form = GastoForm(initial={'fecha': date.today()})

    contexto = {
        'form': form,
        'titulo': 'Registrar Nuevo Gasto'
    }

    return render(request, 'core/form_servicio.html', contexto)
