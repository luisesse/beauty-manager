from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required,permission_required
from django.db.models import ProtectedError, Sum, Q, Case, When, Value, IntegerField
from django.contrib import messages
from datetime import date, datetime
from .models import Servicio, Cita,  Cliente, Profesional, Gasto, HorarioAtencion, CategoriaGasto
from .forms import CitaForm, ServicioForm, ClienteForm, ProfesionalForm, CobrarCitaForm, GastoForm, HorarioForm, CategoriaGastoForm


# --- FUNCIÓN AUXILIAR PARA SAAS ---
def obtener_mi_empresa(request):
    """
    Devuelve la empresa del usuario logueado.
    Si es admin o no tiene empresa, devuelve None o maneja el error.
    """
    try:
        return request.user.profesional.empresa
    except AttributeError:
        return None


@login_required
def home(request):
    hoy = date.today()
    mi_empresa = obtener_mi_empresa(request)

    orden_prioridad = Case(
        When(estado='PENDIENTE', then=Value(1)),
        When(estado='CONFIRMADO', then=Value(1)),
        default=Value(2),  # cualquier otro van al fondo
        output_field=IntegerField(),
    )

    citas_hoy = Cita.objects.filter(fecha=hoy, empresa=mi_empresa)

    es_estilista = request.user.groups.filter(name='Profesionales').exists()

    if es_estilista:
        # Si es estilista, filtramos extra por SU perfil
        citas_hoy = citas_hoy.filter(profesional=request.user.profesional)

    citas_hoy = citas_hoy.order_by(orden_prioridad, 'hora')

    # 1. Total de citas hoy
    total_citas = citas_hoy.count()

    # 2. Cuántas faltan confirmar (Acción urgente)
    pendientes = citas_hoy.filter(estado='PENDIENTE').count()

    # 3. Proyección de dinero (Suma de precios de servicios de hoy)

    proyeccion = citas_hoy.aggregate(total=Sum('servicio__precio_estimado'))['total'] or 0

    contexto = {
        'citas': citas_hoy,
        'fecha_actual': hoy,
        # Pasamos los datos nuevos
        'kpi_total': total_citas,
        'kpi_pendientes': pendientes,
        'kpi_proyeccion': proyeccion
    }
    return render(request, 'core/home.html', contexto)

    contexto = {
        'citas': citas_hoy,
        'fecha_actual': hoy
    }
    return render(request, 'core/home.html', contexto)

#--- Vistas de Servicios ---

@login_required
def listado_servicios(request):

    mi_empresa = obtener_mi_empresa(request)

    if not mi_empresa:
        messages.error(request, "Tu usuario no tiene una empresa asignada.")
        return render(request, 'core/lista_clientes.html', {'clientes': []})

    busqueda = request.GET.get('q')

    if busqueda:
        servicios = Servicio.objects.filter(
            empresa=mi_empresa
        ).filter(
            Q(nombre__icontains=busqueda)
        ).order_by('nombre')
    else:
        servicios = Servicio.objects.filter(empresa=mi_empresa).order_by('nombre')

    contexto = {
        'mis_servicios': servicios
    }

    return render(request, 'core/lista_servicios.html', contexto)

@login_required
def crear_servicio(request):
    if request.method == 'POST':
        form = ServicioForm(request.POST)
        if form.is_valid():
            servicio_nuevo = form.save(commit=False)
            servicio_nuevo.empresa = obtener_mi_empresa(request)
            servicio_nuevo.save()
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
    mi_empresa = obtener_mi_empresa(request)
    servicio = get_object_or_404(Servicio, pk=id, empresa=mi_empresa)

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
    mi_empresa = obtener_mi_empresa(request)
    servicio = get_object_or_404(Servicio, pk=id, empresa=mi_empresa)

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

    mi_empresa = obtener_mi_empresa(request)

    if not mi_empresa:
        messages.error(request, "Tu usuario no tiene una empresa asignada.")
        return render(request, 'core/lista_clientes.html', {'clientes': []})

    busqueda = request.GET.get('q')

    if busqueda:
        clientes = Cliente.objects.filter(
            empresa=mi_empresa
        ).filter(
            Q(nombre__icontains=busqueda) |
            Q(apellido__icontains=busqueda) |
            Q(ci_ruc__icontains=busqueda)
        ).order_by('nombre', 'apellido')
    else:
        clientes = Cliente.objects.filter(empresa=mi_empresa).order_by('nombre', 'apellido')

    return render(request, 'core/lista_clientes.html', {'clientes': clientes})

@login_required
def detalle_cliente(request, id):
    mi_empresa = obtener_mi_empresa(request)
    cliente = get_object_or_404(Cliente, pk=id, empresa=mi_empresa)

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

            cliente_nuevo = form.save(commit=False)

            # Le asignamos la empresa del usuario logueado
            cliente_nuevo.empresa = obtener_mi_empresa(request)

            cliente_nuevo.save()

            messages.success(request, f'¡El cliente {form.instance.nombre} se creó correctamente!')
            return redirect('listado_clientes')
    else:
        form = ClienteForm()

    return render(request, 'core/form_cliente.html', {'form': form, 'titulo': 'Nuevo Cliente'})

@login_required
@permission_required('core.change_cliente', raise_exception=True)
def editar_cliente(request, id):
    mi_empresa = obtener_mi_empresa(request)
    cliente = get_object_or_404(Cliente, pk=id, empresa=mi_empresa)

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
    mi_empresa = obtener_mi_empresa(request)
    cliente = get_object_or_404(Cliente, pk=id, empresa=mi_empresa)

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

    mi_empresa = obtener_mi_empresa(request)

    if not mi_empresa:
        messages.error(request, "Tu usuario no tiene una empresa asignada.")
        return render(request, 'core/lista_profesional.html', {'profesional': []})

    busqueda = request.GET.get('q')

    if busqueda:

        profesional = Profesional.objects.filter(
            empresa=mi_empresa
        ).filter(
            Q(nombre__icontains=busqueda) |
            Q(apellido__icontains=busqueda) |
            Q(especialidad__icontains=busqueda)
        ).order_by('nombre', 'apellido')
    else:

        profesional = Profesional.objects.filter(empresa=mi_empresa).order_by('nombre', 'apellido')

    return render(request, 'core/lista_profesional.html', {'profesional': profesional})

@login_required
@permission_required('core.add_profesional', raise_exception=True)
def crear_profesional(request):
    if request.method == 'POST':
        form = ProfesionalForm(request.POST, request.FILES)
        if form.is_valid():
            profesional_nuevo = form.save(commit=False)


            profesional_nuevo.empresa = obtener_mi_empresa(request)

            profesional_nuevo.save()
            messages.success(request, f'¡El profesional {form.instance.nombre} se creó correctamente!')

            return redirect('listado_profesional')
    else:
        form = ProfesionalForm()

    return render(request, 'core/form_profesional.html', {'form': form, 'titulo': 'Nuevo Profesional'})

@login_required
@permission_required('core.add_profesional', raise_exception=True)
def crear_profesional(request):
    mi_empresa = obtener_mi_empresa(request)

    if request.method == 'POST':

        form = ProfesionalForm(request.POST, request.FILES, empresa=mi_empresa)
        if form.is_valid():
            profesional = form.save(commit=False)
            profesional.empresa = mi_empresa
            profesional.save()
            messages.success(request, f'¡El profesional {profesional.nombre} se creó correctamente!')
            return redirect('listado_profesional')
    else:

        form = ProfesionalForm(empresa=mi_empresa)

    return render(request, 'core/form_profesional.html', {'form': form, 'titulo': 'Nuevo Profesional'})

@login_required
@permission_required('core.change_profesional', raise_exception=True)
def editar_profesional(request, id):
    mi_empresa = obtener_mi_empresa(request)

    profesional = get_object_or_404(Profesional, pk=id, empresa=mi_empresa)

    if request.method == 'POST':

        form = ProfesionalForm(request.POST, request.FILES, instance=profesional, empresa=mi_empresa)
        if form.is_valid():
            form.save()
            return redirect('listado_profesional')
    else:
        form = ProfesionalForm(instance=profesional, empresa=mi_empresa)

    contexto = {
        'form': form,
        'titulo': 'Editar Profesional'
    }
    return render(request, 'core/form_profesional.html', contexto)

@login_required
@permission_required('core.delete_profesional', raise_exception=True)
def eliminar_profesional(request, id):
    mi_empresa = obtener_mi_empresa(request)
    profesional = get_object_or_404(Profesional, pk=id, empresa=mi_empresa)

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
    mi_empresa = obtener_mi_empresa(request)  # 1. Obtenemos la empresa

    if request.method == 'POST':
        form = CitaForm(request.POST, empresa=mi_empresa)

        if form.is_valid():
            cita_nueva = form.save(commit=False)

            cita_nueva.empresa = obtener_mi_empresa(request)

            cita_nueva.save()
            messages.success(request, '¡La cita se creó correctamente!')
            return redirect('listado_citas')
    else:

        form = CitaForm(empresa=mi_empresa)

    contexto = {
        'form': form,
        'titulo': 'Agendar Cita'
    }

    return render(request, 'core/agendar_cita.html',  contexto)

@login_required
def editar_cita(request, id):
    mi_empresa = obtener_mi_empresa(request)
    cita = get_object_or_404(Cita, pk=id, empresa=mi_empresa)

    if request.method == 'POST':
        form = CitaForm(request.POST, instance=cita, empresa=mi_empresa)

        if form.is_valid():
            form.save()
            return redirect('home')

    else:
        form = CitaForm(instance=cita, empresa=mi_empresa)

    contexto = {
        'form': form,
        'titulo': 'Gestión de Cita'
    }

    return render(request, 'core/agendar_cita.html', contexto)


@login_required
def listado_citas(request):
    mi_empresa = obtener_mi_empresa(request)

    # (Opcional) Si es superuser sin empresa, no mostramos nada para evitar error
    if not mi_empresa:
        messages.error(request, "Tu usuario no tiene una empresa asignada.")
        return render(request, 'core/lista_clientes.html', {'clientes': []})

    # Traer citas activas desde HOY en adelante
    # Y que no estén canceladas ni realizadas
    citas = Cita.objects.filter(
            empresa=mi_empresa
        ).filter(
        fecha__gte=date.today(),
        estado__in=['PENDIENTE', 'CONFIRMADO']
    ).order_by('fecha', 'hora')

    es_estilista = request.user.groups.filter(name='Profesionales').exists()

    if es_estilista:

        citas = citas.filter(profesional=request.user.profesional)

    busqueda = request.GET.get('q')
    if busqueda:
        citas = citas.filter(
            empresa=mi_empresa
        ).filter(
            Q(cliente__nombre__icontains=busqueda) |
            Q(cliente__apellido__icontains=busqueda) |
            Q(profesional__nombre__icontains=busqueda)
        )

    # 3. FILTRO POR FECHA EXACTA (NUEVO) 📅
    fecha_filtro = request.GET.get('fecha')
    if fecha_filtro:
        citas = Cita.objects.filter(
            empresa=mi_empresa,
            fecha=fecha_filtro,
            estado__in=['PENDIENTE', 'CONFIRMADO']
        ).order_by('hora')

        if es_estilista:
            citas = citas.filter(profesional=request.user.profesional)

    return render(request, 'core/lista_citas.html', {'citas': citas})


@login_required
def finalizar_cita(request, id):
    mi_empresa = obtener_mi_empresa(request)
    cita = get_object_or_404(Cita, pk=id, empresa=mi_empresa)

    if request.method == 'POST':
        form = CobrarCitaForm(request.POST, instance=cita)
        if form.is_valid():
            # 1. Guardamos el monto
            cita_final = form.save(commit=False)

            notas = request.POST.get('notas_adicionales')
            if notas:
                cita_final.notas_adicionales = notas

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
    mi_empresa = obtener_mi_empresa(request)
    cita = get_object_or_404(Cita, pk=id, empresa=mi_empresa)

    if request.method == 'POST':
        # Solo si el usuario confirmó en el formulario rojo
        cita.estado = 'CANCELADO'
        cita.save()
        return redirect('listado_citas')

    # Si es GET, le mostramos la pregunta
    return render(request, 'core/cancelar_cita.html', {'cita': cita})


@login_required
def confirmar_cita(request, id):
    mi_empresa = obtener_mi_empresa(request)
    cita = get_object_or_404(Cita, pk=id, empresa=mi_empresa)
    cita.estado = 'CONFIRMADO'
    cita.save()
    return redirect('home')

#---Vistas Financieras---

@login_required
@permission_required('core.view_gasto', raise_exception=True)
def reporte_caja(request):
    mi_empresa = obtener_mi_empresa(request)

    fecha_inicio = date.today()
    fecha_fin = date.today()

    if request.GET.get('fecha_inicio') and request.GET.get('fecha_fin'):
        try:
            fecha_inicio = datetime.strptime(request.GET.get('fecha_inicio'), '%Y-%m-%d').date()
            fecha_fin = datetime.strptime(request.GET.get('fecha_fin'), '%Y-%m-%d').date()
        except ValueError:
            pass

    # INGRESOS (Filtrados por empresa)
    citas = Cita.objects.filter(
        empresa=mi_empresa,
        fecha__range=[fecha_inicio, fecha_fin],
        estado='REALIZADO'
    ).order_by('fecha', 'hora')

    total_ingresos = citas.aggregate(total=Sum('monto_cobrado'))['total'] or 0

    ingresos_efectivo = citas.filter(metodo_pago='EFECTIVO').aggregate(t=Sum('monto_cobrado'))['t'] or 0
    ingresos_digital = total_ingresos - ingresos_efectivo

    # EGRESOS (Filtrados por empresa)
    gastos = Gasto.objects.filter(
        empresa=mi_empresa,
        fecha__range=[fecha_inicio, fecha_fin]
    )
    total_egresos = gastos.aggregate(total=Sum('monto'))['total'] or 0

    saldo_neto = total_ingresos - total_egresos
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
    mi_empresa = obtener_mi_empresa(request)

    if not mi_empresa:
        messages.error(request, "Tu usuario no tiene una empresa asignada.")
        return render(request, 'core/lista_gastos.html', {'gastos': []})

    gastos = Gasto.objects.filter(
            empresa=mi_empresa
        ).order_by('-fecha', '-id')
    return render(request, 'core/lista_gastos.html', {'gastos': gastos})

@login_required
def crear_gasto(request):
    mi_empresa = obtener_mi_empresa(request)
    if request.method == 'POST':
        form = GastoForm(request.POST, empresa=mi_empresa)
        if form.is_valid():
            gasto_nuevo = form.save(commit=False)

            gasto_nuevo.empresa = obtener_mi_empresa(request)

            gasto_nuevo.save()

            messages.success(request, 'Gasto registrado correctamente.')
            return redirect('lista_gastos')
    else:
        # Sugerimos la fecha de hoy por defecto
        form = GastoForm(initial={'fecha': date.today()}, empresa=mi_empresa)

    contexto = {
        'form': form,
        'titulo': 'Registrar Nuevo Gasto',
        'url_cancelar': 'lista_gastos'
    }

    return render(request, 'core/form_servicio.html', contexto)


@login_required
def gestion_categorias(request):
    mi_empresa = obtener_mi_empresa(request)

    # Procesar formulario de creación
    if request.method == 'POST':
        form = CategoriaGastoForm(request.POST)
        if form.is_valid():
            cat = form.save(commit=False)
            cat.empresa = mi_empresa
            cat.save()
            messages.success(request, f"Categoría '{cat.nombre}' creada.")
            return redirect('gestion_categorias')
    else:
        form = CategoriaGastoForm()

    # Listar existentes
    categorias = CategoriaGasto.objects.filter(empresa=mi_empresa)

    return render(request, 'core/gestion_categorias.html', {'categorias': categorias, 'form': form})


@login_required
@permission_required('core.delete_gasto', raise_exception=True)  # O el permiso que uses para gerencia
def liquidacion_comisiones(request):
    mi_empresa = obtener_mi_empresa(request)

    fecha_inicio = date.today().replace(day=1)
    fecha_fin = date.today()

    profesionales = Profesional.objects.filter(empresa=mi_empresa)

    profesional_elegido = None
    citas = []
    total_cobrado = 0
    monto_comision = 0

    profesional_id = request.GET.get('profesional_id')
    fecha_ini_get = request.GET.get('fecha_inicio')
    fecha_fin_get = request.GET.get('fecha_fin')

    if profesional_id and fecha_ini_get and fecha_fin_get:
        try:
            fecha_inicio = datetime.strptime(fecha_ini_get, '%Y-%m-%d').date()
            fecha_fin = datetime.strptime(fecha_fin_get, '%Y-%m-%d').date()

            profesional_elegido = get_object_or_404(Profesional, pk=profesional_id, empresa=mi_empresa)

            citas = Cita.objects.filter(
                empresa=mi_empresa,
                profesional=profesional_elegido,
                fecha__range=[fecha_inicio, fecha_fin],
                estado='REALIZADO'
            ).order_by('fecha', 'hora')

            total_cobrado = citas.aggregate(total=Sum('monto_cobrado'))['total'] or 0
            monto_comision = (total_cobrado * profesional_elegido.porcentaje_comision) / 100

        except ValueError:
            pass

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




@login_required
def listado_horarios(request):
    mi_empresa = obtener_mi_empresa(request)

    horarios = HorarioAtencion.objects.filter(empresa=mi_empresa).order_by('dia_semana')
    return render(request, 'core/lista_horarios.html', {'horarios': horarios})

@login_required
@permission_required('core.change_horarioatencion', raise_exception=True)
def editar_horario(request, id):
    mi_empresa = obtener_mi_empresa(request)
    # Solo editamos si el horario pertenece a MI empresa
    horario = get_object_or_404(HorarioAtencion, pk=id, empresa=mi_empresa)

    if request.method == 'POST':
        form = HorarioForm(request.POST, instance=horario)
        if form.is_valid():
            form.save()
            messages.success(request, f"Horario del {horario.get_dia_semana_display()} actualizado.")
            return redirect('listado_horarios')
    else:
        form = HorarioForm(instance=horario)

    contexto = {
        'form': form,
        'titulo': f'Editar Horario: {horario.get_dia_semana_display()}',
        'url_cancelar': 'listado_horarios'
    }

    return render(request, 'core/form_servicio.html', contexto)

