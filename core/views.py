from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required,permission_required
from django.db.models import ProtectedError, Sum, Q, Case, When, Value, IntegerField
from django.contrib import messages
from datetime import date, datetime
from .models import Servicio, Cita,  Cliente, Profesional, Gasto
from .forms import CitaForm, ServicioForm, ClienteForm, ProfesionalForm, CobrarCitaForm, GastoForm


@login_required
def home(request):
    hoy = date.today()

    # 1 = Prioridad Alta (Pendiente/Confirmado)
    # 2 = Prioridad Baja (Realizado/Cancelado)
    orden_prioridad = Case(
        When(estado='PENDIENTE', then=Value(1)),
        When(estado='CONFIRMADO', then=Value(1)),
        default=Value(2),  # cualquier otro van al fondo
        output_field=IntegerField(),
    )

    citas_hoy = Cita.objects.filter(fecha=hoy)

    # Si el usuario es un profesional
    if hasattr(request.user, 'profesional'):
        citas_hoy = citas_hoy.filter(profesional=request.user.profesional)

    citas_hoy = citas_hoy.order_by(orden_prioridad, 'hora')

    contexto = {
        'citas': citas_hoy,
        'fecha_actual': hoy
    }
    return render(request, 'core/home.html', contexto)

#--- Vistas de Servicios ---

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
        'titulo': 'Nuevo Servicio',
        'url_cancelar': 'lista_servicios'
    }

    return render(request, 'core/form_servicio.html', contexto)

@login_required
@permission_required('core.change_servicio', raise_exception=True)
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
        'titulo': 'Editar Servicio',
        'url_cancelar': 'lista_servicios'
    }

    return render(request, 'core/form_servicio.html', contexto)

@login_required
@permission_required('core.delete_servicio', raise_exception=True)
def eliminar_servicio(request, id):
    servicio = get_object_or_404(Servicio, pk=id)

    if request.method == 'POST':
        try:
            servicio.delete()
            messages.success(request, "El servicio fue eliminado correctamente.")
            return redirect('lista_servicios')
        except ProtectedError:
            messages.error(request, f"No se puede eliminar '{servicio.nombre}' porque hay Citas que lo usan.")

            return redirect('lista_servicios')

    return render(request, 'core/eliminar_servicio.html', {'servicio': servicio})

#--- Vista Clientes ---

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
@permission_required('core.add_cliente', raise_exception=True)
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

@login_required
@permission_required('core.change_cliente', raise_exception=True)
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
@permission_required('core.delete_cliente', raise_exception=True)
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

#--- Vistas Profesionales ---

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
@permission_required('core.add_profesional', raise_exception=True)
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

@login_required
@permission_required('core.change_profesional', raise_exception=True)
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
@permission_required('core.delete_profesional', raise_exception=True)
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

    if hasattr(request.user, 'profesional'):
        citas = citas.filter(profesional=request.user.profesional)

    busqueda = request.GET.get('q')
    if busqueda:
        citas = citas.filter(
            Q(cliente__nombre__icontains=busqueda) |
            Q(cliente__apellido__icontains=busqueda) |
            Q(profesional__nombre__icontains=busqueda)
        )

    # 3. FILTRO POR FECHA EXACTA (NUEVO) 📅
    fecha_filtro = request.GET.get('fecha')
    if fecha_filtro:
        # Si el usuario elige una fecha, sobrescribe el filtro para mostrar esa fecha exacta
        # incluso si es pasada
        citas = Cita.objects.filter(
            fecha=fecha_filtro,
            estado__in=['PENDIENTE', 'CONFIRMADO']
        ).order_by('hora')

        if hasattr(request.user, 'profesional'):
            citas = citas.filter(profesional=request.user.profesional)

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



#---Vistas Financieras---

@login_required
@permission_required('core.view_gasto', raise_exception=True)
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

    # --- DESGLOSE POR TIPO DE PAGO ---
    # Efectivo
    ingresos_efectivo = citas.filter(metodo_pago='EFECTIVO').aggregate(t=Sum('monto_cobrado'))['t'] or 0
    # Banco - QR/TC/TD/SIPAP
    ingresos_digital = total_ingresos - ingresos_efectivo

    # EGRESOS
    # Gastos de caja chica en efectivo
    gastos = Gasto.objects.filter(fecha__range=[fecha_inicio, fecha_fin])
    total_egresos = gastos.aggregate(total=Sum('monto'))['total'] or 0

    # SALDO FINAL DEL DÍA
    saldo_neto = total_ingresos - total_egresos

    # Efectivo que entró - Gastos que pagué en efectivo
    caja_fisica = ingresos_efectivo - total_egresos

    contexto = {
        'citas': citas,
        'gastos': gastos,
        'total_ingresos': total_ingresos,
        'total_egresos': total_egresos,
        'saldo_neto': saldo_neto,
        'ingresos_efectivo': ingresos_efectivo,
        'ingresos_digital': ingresos_digital,
        'caja_fisica': caja_fisica,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin
    }
    return render(request, 'core/reporte_caja.html', contexto)


@login_required
@permission_required('core.view_gasto', raise_exception=True)
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
        'titulo': 'Registrar Nuevo Gasto',
        'url_cancelar': 'lista_gastos'
    }

    return render(request, 'core/form_servicio.html', contexto)


@login_required
@permission_required('core.delete_gasto', raise_exception=True)
def liquidacion_comisiones(request):

    fecha_inicio = date.today().replace(day=1)  # Por defecto, primer día del mes actual
    fecha_fin = date.today()
    profesionales = Profesional.objects.all()

    # Definir Variables de resultado
    profesional_elegido = None
    citas = []
    total_cobrado = 0
    monto_comision = 0

    # Filtro buscar
    profesional_id = request.GET.get('profesional_id')
    fecha_ini_get = request.GET.get('fecha_inicio')
    fecha_fin_get = request.GET.get('fecha_fin')

    if profesional_id and fecha_ini_get and fecha_fin_get:
        try:
            # Convertir fechas de texto a objetos date
            fecha_inicio = datetime.strptime(fecha_ini_get, '%Y-%m-%d').date()
            fecha_fin = datetime.strptime(fecha_fin_get, '%Y-%m-%d').date()

            profesional_elegido = get_object_or_404(Profesional, pk=profesional_id)

            # Obtener las Ctas con estado Realizada del profesional en ese rango de fechas
            citas = Cita.objects.filter(
                profesional=profesional_elegido,
                fecha__range=[fecha_inicio, fecha_fin],
                estado='REALIZADO'
            ).order_by('fecha', 'hora')

            # Suma lo cobrado por el profesional por cada servicio.
            total_cobrado = citas.aggregate(total=Sum('monto_cobrado'))['total'] or 0

            # Calcular la comisión.
            monto_comision = (total_cobrado * profesional_elegido.porcentaje_comision) / 100

        except ValueError:
            pass  # Si hay error de fechas, nada

    contexto = {
        'profesionales': profesionales,
        'profesional_elegido': profesional_elegido,
        'citas': citas,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'total_cobrado': total_cobrado,
        'monto_comision': monto_comision
    }
    return render(request, 'core/liquidacion_comisiones.html', contexto)

@login_required
def mis_comisiones(request):

    if not hasattr(request.user, 'profesional'):
        return redirect('home')

    profesional = request.user.profesional
    fecha_inicio = date.today().replace(day=1)
    fecha_fin = date.today()

    if request.GET.get('fecha_inicio') and request.GET.get('fecha_fin'):
        try:
            fecha_inicio = datetime.strptime(request.GET.get('fecha_inicio'), '%Y-%m-%d').date()
            fecha_fin = datetime.strptime(request.GET.get('fecha_fin'), '%Y-%m-%d').date()
        except ValueError:
            pass

    citas = Cita.objects.filter(
        profesional=profesional,
        fecha__range=[fecha_inicio, fecha_fin],
        estado='REALIZADO'
    ).order_by('fecha')

    total_vendido = citas.aggregate(t=Sum('monto_cobrado'))['t'] or 0
    mi_comision = (total_vendido * profesional.porcentaje_comision) / 100

    contexto = {
        'citas': citas,
        'total_vendido': total_vendido,
        'mi_comision': mi_comision,
        'profesional': profesional,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin
    }
    return render(request, 'core/mis_comisiones.html', contexto)


