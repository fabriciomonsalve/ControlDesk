from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app.utils.decorators import admin_required
from app.services.admin_service import AdminService
from app.services.plan_service import PlanService

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    """Dashboard del administrador con métricas globales"""
    metrics = AdminService.get_dashboard_metrics()
    return render_template('admin/dashboard.html', metrics=metrics)

@admin_bp.route('/empresas')
@admin_required
def empresas_list():
    """Listado de empresas con filtros y paginación"""
    search = request.args.get('search', '')
    estado = request.args.get('estado', '')
    plan_id = request.args.get('plan_id', '')
    page = request.args.get('page', 1, type=int)
    
    result = AdminService.get_empresas_list(
        search=search,
        estado=estado if estado else None,
        plan_id=int(plan_id) if plan_id else None,
        page=page
    )
    
    plans = AdminService.get_planes_list()
    
    return render_template('admin/empresas.html', 
                         empresas=result['empresas'],
                         pagination=result,
                         plans=plans,
                         search=search,
                         estado_filter=estado,
                         plan_filter=plan_id)

@admin_bp.route('/empresas/crear', methods=['GET', 'POST'])
@admin_required
def empresas_create():
    """Crear nueva empresa"""
    if request.method == 'POST':
        data = {
            'nombre': request.form.get('nombre'),
            'rut_empresa': request.form.get('rut_empresa'),
            'correo': request.form.get('correo'),
            'telefono': request.form.get('telefono'),
            'direccion': request.form.get('direccion'),
            'estado': request.form.get('estado', 'activa'),
            'pin': request.form.get('pin'),
            'plan_id': int(request.form.get('plan_id')) if request.form.get('plan_id') else None,
            'fecha_inicio_plan': request.form.get('fecha_inicio_plan'),
            'fecha_expiracion_plan': request.form.get('fecha_expiracion_plan')
        }
        
        try:
            empresa = AdminService.create_empresa(data)
            flash(f'Empresa {empresa.nombre} creada exitosamente', 'success')
            return redirect(url_for('admin.empresas_list'))
        except Exception as e:
            flash(f'Error al crear empresa: {str(e)}', 'error')
    
    plans = AdminService.get_planes_list()
    return render_template('admin/empresas_crear.html', plans=plans)

@admin_bp.route('/empresas/<int:empresa_id>/editar', methods=['GET', 'POST'])
@admin_required
def empresas_edit(empresa_id):
    """Editar empresa existente"""
    empresa = AdminService.get_empresa_detalle(empresa_id)
    if not empresa:
        flash('Empresa no encontrada', 'error')
        return redirect(url_for('admin.empresas_list'))
    
    if request.method == 'POST':
        data = {
            'nombre': request.form.get('nombre'),
            'rut_empresa': request.form.get('rut_empresa'),
            'correo': request.form.get('correo'),
            'telefono': request.form.get('telefono'),
            'direccion': request.form.get('direccion'),
            'estado': request.form.get('estado'),
            'pin': request.form.get('pin'),
            'plan_id': int(request.form.get('plan_id')) if request.form.get('plan_id') else None,
            'fecha_inicio_plan': request.form.get('fecha_inicio_plan'),
            'fecha_expiracion_plan': request.form.get('fecha_expiracion_plan')
        }
        
        try:
            empresa_actualizada = AdminService.update_empresa(empresa_id, data)
            flash(f'Empresa {empresa_actualizada.nombre} actualizada exitosamente', 'success')
            return redirect(url_for('admin.empresas_detalle', empresa_id=empresa_id))
        except Exception as e:
            flash(f'Error al actualizar empresa: {str(e)}', 'error')
    
    plans = AdminService.get_planes_list()
    return render_template('admin/empresas_editar.html', empresa=empresa, plans=plans)

@admin_bp.route('/empresas/<int:empresa_id>')
@admin_required
def empresas_detalle(empresa_id):
    """Detalle de una empresa"""
    empresa = AdminService.get_empresa_detalle(empresa_id)
    if not empresa:
        flash('Empresa no encontrada', 'error')
        return redirect(url_for('admin.empresas_list'))
    
    return render_template('admin/empresas_detalle.html', empresa=empresa)

@admin_bp.route('/empresas/<int:empresa_id>/reset', methods=['POST'])
@admin_required
def empresas_reset_data(empresa_id):
    """Resetea todos los datos registrados de una empresa"""
    try:
        AdminService.reset_empresa_data(empresa_id)
        flash('Todos los registros de la empresa han sido eliminados correctamente.', 'success')
    except Exception as e:
        flash(f'Error al resetear los datos: {str(e)}', 'error')
    
    return redirect(url_for('admin.empresas_detalle', empresa_id=empresa_id))

@admin_bp.route('/empresas/<int:empresa_id>/desactivar', methods=['POST'])
@admin_required
def empresas_desactivar(empresa_id):
    """Desactivar empresa"""
    empresa = AdminService.deactivate_empresa(empresa_id)
    if empresa:
        flash(f'Empresa {empresa.nombre} desactivada exitosamente', 'success')
    else:
        flash('Empresa no encontrada', 'error')
    
    return redirect(url_for('admin.empresas_list'))

@admin_bp.route('/empresas/<int:empresa_id>/activar', methods=['POST'])
@admin_required
def empresas_activar(empresa_id):
    """Activar empresa"""
    empresa = AdminService.activate_empresa(empresa_id)
    if empresa:
        flash(f'Empresa {empresa.nombre} activada exitosamente', 'success')
    else:
        flash('Empresa no encontrada', 'error')
    
    return redirect(url_for('admin.empresas_list'))

@admin_bp.route('/planes')
@admin_required
def planes_list():
    """Listado de planes"""
    plans = AdminService.get_planes_list()
    return render_template('admin/planes.html', plans=plans)


@admin_bp.route('/planes/<int:plan_id>/toggle', methods=['POST'])
@admin_required
def planes_toggle(plan_id):
    """Activar/Desactivar plan"""
    try:
        plan = AdminService.toggle_plan_status(plan_id)
        if plan:
            estado = 'activado' if plan.activo else 'desactivado'
            flash(f'Plan {plan.nombre} {estado} exitosamente', 'success')
        else:
            flash('Plan no encontrado', 'error')
    except Exception as e:
        flash(f'Error al cambiar estado del plan: {str(e)}', 'error')
    
    return redirect(url_for('admin.planes_list'))

@admin_bp.route('/planes/crear', methods=['GET', 'POST'])
@admin_required
def planes_create():
    """Crear nuevo plan"""
    if request.method == 'POST':
        data = {
            'nombre': request.form.get('nombre'),
            'descripcion': request.form.get('descripcion'),
            'precio_mensual': float(request.form.get('precio_mensual', 0)),
            'max_rubros': int(request.form.get('max_rubros', 3)),
            'max_categorias': int(request.form.get('max_categorias', 10)),
            'max_usuarios': int(request.form.get('max_usuarios', 1)),
            'max_movimientos_mensuales': int(request.form.get('max_movimientos_mensuales', 100)),
            'acceso_reportes_avanzados': request.form.get('acceso_reportes_avanzados') == 'on',
            'acceso_export_pdf': request.form.get('acceso_export_pdf') == 'on',
            'activo': request.form.get('activo') == 'on'
        }
        
        try:
            plan = AdminService.create_plan(data)
            flash(f'Plan {plan.nombre} creado exitosamente', 'success')
            return redirect(url_for('admin.planes_list'))
        except Exception as e:
            flash(f'Error al crear plan: {str(e)}', 'error')
    
    return render_template('admin/planes_crear.html')

@admin_bp.route('/planes/<int:plan_id>/editar', methods=['GET', 'POST'])
@admin_required
def planes_edit(plan_id):
    """Editar plan existente"""
    # Obtener plan actual
    from app.models.plan import Plan
    plan = Plan.query.get(plan_id)
    if not plan:
        flash('Plan no encontrado', 'error')
        return redirect(url_for('admin.planes_list'))
    
    if request.method == 'POST':
        data = {
            'nombre': request.form.get('nombre'),
            'descripcion': request.form.get('descripcion'),
            'precio_mensual': float(request.form.get('precio_mensual', 0)),
            'max_rubros': int(request.form.get('max_rubros', 3)),
            'max_categorias': int(request.form.get('max_categorias', 10)),
            'max_usuarios': int(request.form.get('max_usuarios', 1)),
            'max_movimientos_mensuales': int(request.form.get('max_movimientos_mensuales', 100)),
            'acceso_reportes_avanzados': request.form.get('acceso_reportes_avanzados') == 'on',
            'acceso_export_pdf': request.form.get('acceso_export_pdf') == 'on',
            'activo': request.form.get('activo') == 'on'
        }
        
        try:
            plan_actualizado = AdminService.update_plan(plan_id, data)
            flash(f'Plan {plan_actualizado.nombre} actualizado exitosamente', 'success')
            return redirect(url_for('admin.planes_list'))
        except Exception as e:
            flash(f'Error al actualizar plan: {str(e)}', 'error')
    
    return render_template('admin/planes_editar.html', plan=plan)

