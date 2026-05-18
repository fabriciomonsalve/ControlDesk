from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file, session
from app.services.movimiento_service import MovimientoService
from app.services.dashboard_service import DashboardService
from app.services.reportes_service import ReportesService
from app.services.rubro_service import RubroService
from app.services.auth_service import AuthService
from datetime import datetime

main_bp = Blueprint('main', __name__)

@main_bp.route('/index')
def index():
    """Página principal de presentación (landing page)"""
    return render_template('index.html')

@main_bp.route('/login')
def login():
    """Página de login multiempresa"""
    # Si ya está logueado, redirigir al dashboard
    if AuthService.is_logged_in():
        return redirect(url_for('main.dashboard'))
    
    empresas = AuthService.get_all_empresas()
    return render_template('login.html', empresas=empresas)

## 
@main_bp.route('/login', methods=['POST'])
def login_post():
    """Procesa el formulario de login"""
    try:
        empresa_id = request.form.get('empresa_id')
        pin = request.form.get('pin')
        
        if not empresa_id or not pin:
            flash('Por favor seleccione una empresa e ingrese su PIN', 'error')
            return redirect(url_for('main.login'))
        
        result = AuthService.login(int(empresa_id), pin)
        
        if result['success']:
            flash(f'Bienvenido a {result["empresa"]["nombre"]}', 'success')
            return redirect(url_for('main.dashboard'))
        else:
            flash(result['error'], 'error')
            return redirect(url_for('main.login'))
            
    except Exception as e:
        flash(f'Error al iniciar sesión: {str(e)}', 'error')
        return redirect(url_for('main.login'))

@main_bp.route('/logout')
def logout():
    """Cierra la sesión actual"""
    AuthService.logout()
    flash('Sesión cerrada correctamente', 'info')
    return redirect(url_for('main.login'))

@main_bp.route('/')
def dashboard():
    """Página principal del dashboard"""
    # Verificar sesión, si no hay sesión redirigir al index
    if not AuthService.is_logged_in():
        return redirect(url_for('main.index'))
    
    try:
        # Obtener datos del dashboard filtrados por empresa
        empresa_id = session.get('empresa_id')
        dashboard_data = DashboardService.get_dashboard_data(empresa_id=empresa_id)
        
        # Obtener insights semanales
        weekly_insights = DashboardService.get_weekly_insights()
        
        # Depuración: mostrar si estamos usando datos reales o simulados
        print(f"Dashboard usando datos {'reales' if dashboard_data.get('has_real_data') else 'simulados'}")
        print(f"Rubros: {len(dashboard_data.get('rubros_data', []))}")
        print(f"Total ingresos: ${dashboard_data.get('total_ingresos', 0):.2f}")
        print(f"Total gastos: ${dashboard_data.get('total_gastos', 0):.2f}")
        
        return render_template('dashboard.html', weekly_insights=weekly_insights, **dashboard_data)
    except Exception as e:
        print(f"Error en ruta dashboard: {e}")
        import traceback
        traceback.print_exc()
        # En caso de error, mostrar datos simulados
        dashboard_data = DashboardService.get_simulated_data()
        weekly_insights = DashboardService.get_weekly_insights()
        return render_template('dashboard.html', weekly_insights=weekly_insights, **dashboard_data)

@main_bp.route('/dashboard')
def dashboard_alt():
    """Ruta alternativa para dashboard"""
    return redirect(url_for('main.dashboard'))

@main_bp.route('/api/chart-data')
def get_chart_data():
    """API endpoint para obtener datos de gráficos filtrados por mes"""
    try:
        # Verificar sesión
        if not AuthService.is_logged_in():
            return jsonify({'success': False, 'error': 'No autorizado'}), 401
        
        mes = request.args.get('mes', '')
        empresa_id = session.get('empresa_id')
        
        # Obtener datos del dashboard con filtro de mes y empresa
        dashboard_data = DashboardService.get_dashboard_data(mes_filter=mes if mes else None, empresa_id=empresa_id)
        
        return jsonify({
            'success': True,
            'data': {
                'ganancias_chart': dashboard_data.get('chart_data', {}).get('ganancias_chart', {}),
                'gastos_chart': dashboard_data.get('chart_data', {}).get('gastos_chart', {}),
                'ingresos_vs_gastos_chart': dashboard_data.get('chart_data', {}).get('ingresos_vs_gastos_chart', {})
            }
        })
    except Exception as e:
        print(f"Error en API de chart data: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@main_bp.route('/movimientos')
def movimientos():
    """Página de listado de movimientos con filtros y paginación"""
    # Verificar sesión
    if not AuthService.is_logged_in():
        return redirect(url_for('main.login'))
    
    try:
        # Obtener parámetros de filtro
        tipo = request.args.get('tipo')
        rubro_id = request.args.get('rubro_id')
        categoria_id = request.args.get('categoria_id')
        fecha_desde = request.args.get('fecha_desde')
        fecha_hasta = request.args.get('fecha_hasta')
        empresa_id = session.get('empresa_id')
        
        # Obtener parámetros de paginación
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # Convertir IDs a enteros si existen
        if rubro_id:
            rubro_id = int(rubro_id)
        if categoria_id:
            categoria_id = int(categoria_id)
        
        # Obtener movimientos filtrados y paginados
        result = MovimientoService.get_all_movimientos(
            tipo=tipo,
            rubro_id=rubro_id,
            categoria_id=categoria_id,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            page=page,
            per_page=per_page,
            empresa_id=empresa_id
        )
        
        # Obtener datos para los selectores
        rubros = MovimientoService.get_rubros_for_select(empresa_id)
        categorias = MovimientoService.get_categorias_for_select(empresa_id)
        
        return render_template('movimientos.html', 
                             movimientos=result['movimientos'],
                             rubros=rubros,
                             categorias=categorias,
                             pagination=result)
    except Exception as e:
        flash('Error al cargar los movimientos', 'error')
        return render_template('movimientos.html', 
                             movimientos=[],
                             rubros=[],
                             categorias=[],
                             pagination={
                                 'total': 0,
                                 'page': 1,
                                 'per_page': 10,
                                 'total_pages': 0,
                                 'has_prev': False,
                                 'has_next': False,
                                 'prev_num': None,
                                 'next_num': None
                             })

@main_bp.route('/reportes')
def reportes():
    """Página de reportes financieros"""
    # Verificar sesión
    if not AuthService.is_logged_in():
        return redirect(url_for('main.login'))
    
    try:
        # Obtener parámetros de filtro
        fecha_desde = request.args.get('fecha_desde')
        fecha_hasta = request.args.get('fecha_hasta')
        empresa_id = session.get('empresa_id')
        
        # Obtener datos de reportes filtrados por empresa
        resumen = ReportesService.get_resumen_general(fecha_desde, fecha_hasta, empresa_id)
        ganancias_por_rubro = ReportesService.get_ganancias_por_rubro(fecha_desde, fecha_hasta, empresa_id)
        tendencia_mensual = ReportesService.get_tendencia_mensual(empresa_id=empresa_id)
        
        return render_template('reportes.html',
                             resumen=resumen,
                             ganancias_por_rubro=ganancias_por_rubro,
                             tendencia_mensual=tendencia_mensual)
    except Exception as e:
        flash('Error al cargar los reportes', 'error')
        return render_template('reportes.html',
                             resumen={},
                             ganancias_por_rubro=[],
                             tendencia_mensual=[])

@main_bp.route('/nuevo-movimiento', methods=['GET', 'POST'])
def nuevo_movimiento():
    """Crear nuevo movimiento"""
    if request.method == 'GET':
        try:
            empresa_id = session.get('empresa_id')
            rubros = MovimientoService.get_rubros_for_select(empresa_id)
            categorias = MovimientoService.get_categorias_for_select(empresa_id)
            return render_template('nuevo_movimiento.html', 
                             rubros=rubros, 
                             categorias=categorias,
                             form_data={})
        except Exception as e:
            flash('Error al cargar el formulario', 'error')
            return render_template('nuevo_movimiento.html', 
                             rubros=[], 
                             categorias=[],
                             form_data={})
    
    # POST request
    try:
        empresa_id = session.get('empresa_id')
        movimiento, error = MovimientoService.create_movimiento(request.form.to_dict(), empresa_id)
        
        if error:
            flash(error, 'error')
            empresa_id = session.get('empresa_id')
            rubros = MovimientoService.get_rubros_for_select(empresa_id)
            categorias = MovimientoService.get_categorias_for_select(empresa_id)
            return render_template('nuevo_movimiento.html', 
                             rubros=rubros, 
                             categorias=categorias,
                             form_data=request.form.to_dict())
        
        flash('Movimiento creado exitosamente', 'success')
        return redirect(url_for('main.movimientos'))
        
    except Exception as e:
        flash('Error al crear el movimiento', 'error')
        return redirect(url_for('main.movimientos'))

@main_bp.route('/editar-movimiento/<int:movimiento_id>', methods=['GET', 'POST'])
def editar_movimiento(movimiento_id):
    if request.method == 'GET':
        try:
            movimiento = MovimientoService.get_movimiento_by_id(movimiento_id)
            if not movimiento:
                flash('Movimiento no encontrado', 'error')
                return redirect(url_for('main.movimientos'))
            
            empresa_id = session.get('empresa_id')
            rubros = MovimientoService.get_rubros_for_select(empresa_id)
            categorias = MovimientoService.get_categorias_for_select(empresa_id)
            
            form_data = {
                'id': movimiento.id,
                'tipo': movimiento.tipo,
                'monto': movimiento.monto,
                'fecha': movimiento.fecha.strftime('%Y-%m-%d'),
                'descripcion': movimiento.descripcion,
                'rubro_id': movimiento.rubro_id,
                'categoria_id': movimiento.categoria_id
            }
            
            return render_template('editar_movimiento.html', 
                             movimiento=movimiento,
                             rubros=rubros, 
                             categorias=categorias,
                             form_data=form_data)
        except Exception as e:
            flash('Error al cargar el movimiento', 'error')
            return redirect(url_for('main.movimientos'))
    
    # POST request
    try:
        movimiento, error = MovimientoService.update_movimiento(movimiento_id, request.form.to_dict())
        
        if error:
            flash(error, 'error')
            empresa_id = session.get('empresa_id')
            rubros = MovimientoService.get_rubros_for_select(empresa_id)
            categorias = MovimientoService.get_categorias_for_select(empresa_id)
            return render_template('editar_movimiento.html', 
                             movimiento=movimiento,
                             rubros=rubros, 
                             categorias=categorias,
                             form_data=request.form.to_dict())
        
        flash('Movimiento actualizado exitosamente', 'success')
        return redirect(url_for('main.movimientos'))
        
    except Exception as e:
        flash('Error al actualizar el movimiento', 'error')
        return redirect(url_for('main.movimientos'))

@main_bp.route('/eliminar-movimiento/<int:movimiento_id>', methods=['POST'])
def eliminar_movimiento(movimiento_id):
    """Eliminar movimiento"""
    try:
        eliminado, error = MovimientoService.delete_movimiento(movimiento_id)
        
        if error:
            flash(error, 'error')
        else:
            flash('Movimiento eliminado exitosamente', 'success')
            
    except Exception as e:
        flash('Error al eliminar el movimiento', 'error')
    
    return redirect(url_for('main.movimientos'))

@main_bp.route('/api/movimientos')
def api_movimientos():
    """API endpoint para obtener movimientos en JSON"""
    try:
        movimientos = MovimientoService.get_all_movimientos()
        return jsonify([mov.to_dict() for mov in movimientos])
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@main_bp.route('/configuracion')
def configuracion():
    """Página de configuración"""
    return render_template('configuracion.html')

@main_bp.route('/api/exportar-pdf', methods=['POST'])
def exportar_pdf():
    """API endpoint para generar y descargar reporte PDF"""
    try:
        data = request.get_json()
        
        # Obtener parámetros de filtro
        fecha_desde = data.get('fecha_desde')
        fecha_hasta = data.get('fecha_hasta')
        chart_images = data.get('chart_images', {})
        incluir_portada = data.get('incluir_portada', True)
        
        # Obtener datos filtrados
        resumen = ReportesService.get_resumen_general(fecha_desde, fecha_hasta)
        ganancias_por_rubro = ReportesService.get_ganancias_por_rubro(fecha_desde, fecha_hasta)
        tendencia_mensual = ReportesService.get_tendencia_mensual()
        
        # Generar PDF
        pdf_buffer = ReportesService.generate_financial_report_pdf(
            resumen=resumen,
            ganancias_por_rubro=ganancias_por_rubro,
            tendencia_mensual=tendencia_mensual,
            chart_images=chart_images,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            incluir_portada=incluir_portada
        )
        
        # Generar nombre de archivo dinámico basado en fechas del filtro
        if fecha_desde and fecha_hasta:
            # Formatear fechas para el nombre del archivo (reemplazar guiones por guiones bajos)
            fecha_desde_formatted = fecha_desde.replace('-', '_')
            fecha_hasta_formatted = fecha_hasta.replace('-', '_')
            filename = f'reporte-financiero_{fecha_desde_formatted}_a_{fecha_hasta_formatted}.pdf'
        elif fecha_desde:
            fecha_desde_formatted = fecha_desde.replace('-', '_')
            filename = f'reporte-financiero_desde_{fecha_desde_formatted}.pdf'
        elif fecha_hasta:
            fecha_hasta_formatted = fecha_hasta.replace('-', '_')
            filename = f'reporte-financiero_hasta_{fecha_hasta_formatted}.pdf'
        else:
            fecha_actual = datetime.now().strftime('%Y-%m-%d')
            filename = f'reporte-financiero-{fecha_actual}.pdf'
        
        # Enviar archivo
        return send_file(
            pdf_buffer,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )
        
    except Exception as e:
        print(f"Error generando PDF: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Rutas para el módulo de Rubros
@main_bp.route('/rubros/<int:rubro_id>/timeline')
def rubro_timeline(rubro_id):
    """Página de línea de tiempo de movimientos de un rubro"""
    try:
        rubro = RubroService.get_rubro_by_id(rubro_id)
        if not rubro:
            flash('Rubro no encontrado', 'error')
            return redirect(url_for('main.rubros'))
        
        movimientos = MovimientoService.get_movimientos_by_rubro(rubro_id)
        return render_template('rubro_timeline.html', rubro=rubro, movimientos=movimientos)
    except Exception as e:
        flash('Error al cargar la línea de tiempo', 'error')
        return redirect(url_for('main.rubros'))

@main_bp.route('/rubros')
def rubros():
    """Página de gestión de rubros"""
    # Verificar sesión
    if not AuthService.is_logged_in():
        return redirect(url_for('main.login'))
    
    try:
        empresa_id = session.get('empresa_id')
        rubros_data = RubroService.get_all_rubros(empresa_id=empresa_id)
        return render_template('rubros.html', rubros=rubros_data)
    except Exception as e:
        print(f"Error en ruta rubros: {e}")
        return render_template('rubros.html', rubros=[])

@main_bp.route('/api/rubros', methods=['GET'])
def api_get_rubros():
    """API endpoint para obtener todos los rubros"""
    try:
        rubros = RubroService.get_all_rubros()
        return jsonify({
            'success': True,
            'rubros': rubros
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@main_bp.route('/api/rubros/<int:rubro_id>', methods=['GET'])
def api_get_rubro(rubro_id):
    """API endpoint para obtener un rubro por ID"""
    try:
        rubro = RubroService.get_rubro_by_id(rubro_id)
        if rubro:
            return jsonify({
                'success': True,
                'rubro': rubro
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Rubro no encontrado'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@main_bp.route('/api/rubros', methods=['POST'])
def api_create_rubro():
    """API endpoint para crear un nuevo rubro"""
    try:
        data = request.get_json()
        nombre = data.get('nombre')
        
        if not nombre:
            return jsonify({
                'success': False,
                'error': 'El nombre es requerido'
            }), 400
        
        empresa_id = session.get('empresa_id')
        
        rubro = RubroService.create_rubro(nombre, empresa_id)
        if rubro:
            return jsonify({
                'success': True,
                'rubro': rubro,
                'message': 'Rubro creado exitosamente'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Ya existe un rubro con ese nombre'
            }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@main_bp.route('/api/rubros/<int:rubro_id>', methods=['PUT'])
def api_update_rubro(rubro_id):
    """API endpoint para actualizar un rubro"""
    try:
        data = request.get_json()
        nombre = data.get('nombre')
        
        if not nombre:
            return jsonify({
                'success': False,
                'error': 'El nombre es requerido'
            }), 400
        
        rubro = RubroService.update_rubro(rubro_id, nombre)
        if rubro:
            return jsonify({
                'success': True,
                'rubro': rubro,
                'message': 'Rubro actualizado exitosamente'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Rubro no encontrado o nombre ya en uso'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@main_bp.route('/api/rubros/<int:rubro_id>', methods=['DELETE'])
def api_delete_rubro(rubro_id):
    """API endpoint para eliminar un rubro"""
    try:
        success = RubroService.delete_rubro(rubro_id)
        if success:
            return jsonify({
                'success': True,
                'message': 'Rubro eliminado exitosamente'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Rubro no encontrado'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
