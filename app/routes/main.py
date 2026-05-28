from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file, session
from werkzeug.utils import secure_filename
from app import db
from app.services.movimiento_service import MovimientoService
from app.services.dashboard_service import DashboardService
from app.services.reportes_service import ReportesService
from app.services.rubro_service import RubroService
from app.services.auth_service import AuthService
from app.services.categoria_service import CategoriaService
from app.services.importacion_venta_service import ImportacionVentaService
from app.services.notification_service import NotificationService
from app.services.financial_insights_service import FinancialInsightsService
from app.services.plan_service import PlanService
from app.models.notification import Notification
from app.models.categoria import Categoria
from app.models.notification_preference import NotificationPreference
from datetime import datetime
import os

main_bp = Blueprint('main', __name__)

@main_bp.route('/index')
def index():
    """Página principal de presentación (landing page)"""
    return render_template('index.html')

@main_bp.route('/login')
def login():
    """Página de login multiempresa y administrador"""
    # Si ya está logueado, redirigir según el rol
    if AuthService.is_logged_in():
        user_role = session.get('user_role')
        if user_role == 'ADMIN':
            return redirect(url_for('admin.dashboard'))
        else:
            return redirect(url_for('main.dashboard'))
    
    empresas = AuthService.get_all_empresas()
    return render_template('login.html', empresas=empresas)

@main_bp.route('/login', methods=['POST'])
def login_post():
    """Procesa el formulario de login"""
    try:
        login_type = request.form.get('login_type', 'empresa')
        
        # Login de ADMIN por email/contraseña
        if login_type == 'admin':
            email = request.form.get('email')
            password = request.form.get('password')
            
            if not email or not password:
                flash('Por favor ingrese email y contraseña', 'error')
                return redirect(url_for('main.login'))
            
            result = AuthService.login_admin(email, password)
            
            if result['success']:
                flash(f'Bienvenido Administrador', 'success')
                return redirect(url_for('admin.dashboard'))
            else:
                flash(result['error'], 'error')
                return redirect(url_for('main.login'))
        
        # Login de EMPRESA por PIN (flujo actual)
        else:
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
        # En caso de error, mostrar datos vacíos
        dashboard_data = DashboardService.get_empty_data()
        weekly_insights = DashboardService.get_weekly_insights()
        return render_template('dashboard.html', weekly_insights=weekly_insights, **dashboard_data)

@main_bp.route('/dashboard')
def dashboard_alt():
    """Ruta alternativa para dashboard"""
    return redirect(url_for('main.dashboard'))

@main_bp.route('/alertas')
def alertas():
    """Página de alertas y notificaciones"""
    if not AuthService.is_logged_in():
        return redirect(url_for('main.login'))
    return render_template('alertas.html')

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
    
    # Verificar que sea usuario de empresa (no ADMIN accediendo a rutas de empresa)
    user_role = session.get('user_role')
    if user_role == 'ADMIN':
        return redirect(url_for('admin.dashboard'))
    
    try:
        # Obtener empresa_id de la sesión
        empresa_id = session.get('empresa_id')
        
        # Validar acceso a reportes avanzados según el plan
        can_access, message = PlanService.can_access_advanced_reports(empresa_id)
        if not can_access:
            flash(message, 'error')
            return redirect(url_for('main.dashboard'))
        
        # Obtener parámetros de filtro
        fecha_desde = request.args.get('fecha_desde')
        fecha_hasta = request.args.get('fecha_hasta')
        
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

# ============================================
# API endpoints para configuración
# ============================================

@main_bp.route('/api/configuracion/empresa', methods=['POST'])
def api_update_empresa():
    """API endpoint para actualizar configuración de empresa"""
    try:
        if not AuthService.is_logged_in():
            return jsonify({'success': False, 'error': 'No autorizado'}), 401
        
        empresa_id = session.get('empresa_id')
        data = request.get_json()
        
        from app.models.empresa import Empresa
        empresa = Empresa.query.get(empresa_id)
        
        if not empresa:
            return jsonify({'success': False, 'error': 'Empresa no encontrada'}), 404
        
        # Actualizar nombre y estado
        if 'nombre' in data and data['nombre']:
            empresa.nombre = data['nombre']
        
        if 'estado' in data:
            empresa.estado = data['estado']
        
        # Actualizar PIN si se proporciona
        if data.get('pin_actual') and data.get('pin_nuevo'):
            if not empresa.verify_pin(data['pin_actual']):
                return jsonify({'success': False, 'error': 'PIN actual incorrecto'}), 400
            empresa.set_pin(data['pin_nuevo'])
        
        db.session.commit()
        
        # Actualizar sesión
        session['empresa_nombre'] = empresa.nombre
        
        return jsonify({
            'success': True,
            'message': 'Configuración actualizada',
            'empresa': empresa.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error actualizando empresa: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@main_bp.route('/api/configuracion/seguridad', methods=['POST'])
def api_save_seguridad():
    """API endpoint para guardar configuración de seguridad"""
    try:
        if not AuthService.is_logged_in():
            return jsonify({'success': False, 'error': 'No autorizado'}), 401
        
        empresa_id = session.get('empresa_id')
        data = request.get_json()
        
        # Obtener o crear preferencias de la empresa
        notification_pref = NotificationPreference.query.filter_by(empresa_id=empresa_id).first()
        
        if not notification_pref:
            notification_pref = NotificationPreference(
                empresa_id=empresa_id,
                duracion_sesion=data.get('duracion_sesion', 30),
                auto_logout=data.get('auto_logout', False)
            )
            db.session.add(notification_pref)
        else:
            notification_pref.duracion_sesion = data.get('duracion_sesion', notification_pref.duracion_sesion)
            notification_pref.auto_logout = data.get('auto_logout', notification_pref.auto_logout)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Configuración de seguridad guardada',
            'preferences': notification_pref.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error guardando configuración de seguridad: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@main_bp.route('/api/configuracion/seguridad', methods=['GET'])
def api_get_seguridad():
    """API endpoint para obtener configuración de seguridad"""
    try:
        if not AuthService.is_logged_in():
            return jsonify({'success': False, 'error': 'No autorizado'}), 401
        
        empresa_id = session.get('empresa_id')
        notification_pref = NotificationPreference.query.filter_by(empresa_id=empresa_id).first()
        
        if notification_pref:
            return jsonify({
                'success': True,
                'preferences': {
                    'duracion_sesion': notification_pref.duracion_sesion,
                    'auto_logout': notification_pref.auto_logout
                }
            })
        else:
            # Retornar valores por defecto si no hay preferencias guardadas
            return jsonify({
                'success': True,
                'preferences': {
                    'duracion_sesion': 30,
                    'auto_logout': False
                }
            })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@main_bp.route('/api/configuracion/notificaciones', methods=['POST'])
def api_save_notification_preferences():
    """API endpoint para guardar preferencias de notificaciones"""
    try:
        if not AuthService.is_logged_in():
            return jsonify({'success': False, 'error': 'No autorizado'}), 401
        
        empresa_id = session.get('empresa_id')
        data = request.get_json()
        
        # Obtener o crear preferencias de notificaciones de la empresa
        notification_pref = NotificationPreference.query.filter_by(empresa_id=empresa_id).first()
        
        if not notification_pref:
            notification_pref = NotificationPreference(
                empresa_id=empresa_id,
                notif_ventas=data.get('ventas', True),
                notif_gastos=data.get('gastos', True),
                notif_financieras=data.get('financieras', True),
                notif_resumen=data.get('resumen', False)
            )
            db.session.add(notification_pref)
        else:
            notification_pref.notif_ventas = data.get('ventas', notification_pref.notif_ventas)
            notification_pref.notif_gastos = data.get('gastos', notification_pref.notif_gastos)
            notification_pref.notif_financieras = data.get('financieras', notification_pref.notif_financieras)
            notification_pref.notif_resumen = data.get('resumen', notification_pref.notif_resumen)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Preferencias de notificaciones guardadas',
            'preferences': notification_pref.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error guardando preferencias de notificaciones: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@main_bp.route('/api/configuracion/notificaciones', methods=['GET'])
def api_get_notification_preferences():
    """API endpoint para obtener preferencias de notificaciones"""
    try:
        if not AuthService.is_logged_in():
            return jsonify({'success': False, 'error': 'No autorizado'}), 401
        
        empresa_id = session.get('empresa_id')
        notification_pref = NotificationPreference.query.filter_by(empresa_id=empresa_id).first()
        
        if notification_pref:
            return jsonify({
                'success': True,
                'preferences': notification_pref.to_dict()
            })
        else:
            # Retornar valores por defecto si no hay preferencias guardadas
            return jsonify({
                'success': True,
                'preferences': {
                    'notif_ventas': True,
                    'notif_gastos': True,
                    'notif_financieras': True,
                    'notif_resumen': False
                }
            })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


from flask import Response
from werkzeug.wsgi import FileWrapper

@main_bp.route('/api/exportar-pdf', methods=['POST'])
def exportar_pdf():
    """API endpoint para generar y descargar reporte PDF"""
    try:
        # Verificar sesión
        if not AuthService.is_logged_in():
            return jsonify({'success': False, 'error': 'No hay sesión activa'}), 401
        
        # Obtener empresa_id de la sesión
        empresa_id = session.get('empresa_id')
        user_role = session.get('user_role')
        
        # Si es ADMIN, usar la primera empresa disponible o permitir sin empresa_id
        if user_role == 'ADMIN' and not empresa_id:
            return jsonify({'success': False, 'error': 'Los administradores deben seleccionar una empresa para exportar PDF'}), 403
        
        # Validar acceso a exportación PDF según el plan (solo para usuarios de empresa)
        if user_role == 'EMPRESA':
            can_export, message = PlanService.can_export_pdf(empresa_id)
            if not can_export:
                return jsonify({'success': False, 'error': message}), 403
        
        data = request.get_json()
        
        # Obtener parámetros de filtro
        fecha_desde = data.get('fecha_desde')
        fecha_hasta = data.get('fecha_hasta')
        chart_images = data.get('chart_images', {})
        incluir_portada = data.get('incluir_portada', True)
        
        # Obtener datos filtrados por empresa
        resumen = ReportesService.get_resumen_general(fecha_desde, fecha_hasta, empresa_id)
        ganancias_por_rubro = ReportesService.get_ganancias_por_rubro(fecha_desde, fecha_hasta, empresa_id)
        tendencia_mensual = ReportesService.get_tendencia_mensual(empresa_id=empresa_id)
        
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
        
        return Response(
            FileWrapper(pdf_buffer),
            mimetype='application/pdf',
            headers={
                'Content-Disposition': f'attachment; filename={filename}'
            },
            direct_passthrough=True
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

# ==================== RUTAS DE CATEGORÍAS ====================

@main_bp.route('/categorias')
def categorias():
    """Página de listado de categorías"""
    # Verificar sesión
    if not AuthService.is_logged_in():
        return redirect(url_for('main.login'))
    
    try:
        empresa_id = session.get('empresa_id')
        search_term = request.args.get('search', '')
        estado_filter = request.args.get('estado', '')
        
        print(f"Debug - empresa_id: {empresa_id}, search: {search_term}, estado: {estado_filter}")
        
        # Obtener métricas del dashboard
        metrics = CategoriaService.get_dashboard_metrics(empresa_id)
        print(f"Debug - metrics: {metrics}")
        
        # Obtener categorías según filtros
        if search_term:
            categorias = CategoriaService.search_categorias(search_term, empresa_id)
        elif estado_filter:
            categorias = Categoria.query.filter_by(estado=estado_filter, empresa_id=empresa_id).order_by(Categoria.nombre).all()
        else:
            categorias = CategoriaService.get_all_categorias(empresa_id)
        
        print(f"Debug - categorias count: {len(categorias) if categorias else 0}")
        
        return render_template('categorias.html', 
                             categorias=categorias,
                             metrics=metrics,
                             search_term=search_term,
                             estado_filter=estado_filter)
    except Exception as e:
        print(f"Error en ruta categorías: {str(e)}")
        import traceback
        traceback.print_exc()
        flash(f'Error al cargar las categorías: {str(e)}', 'error')
        return render_template('categorias.html', 
                             categorias=[],
                             metrics={},
                             search_term='',
                             estado_filter='')

@main_bp.route('/nueva-categoria', methods=['GET', 'POST'])
def nueva_categoria():
    """Crear nueva categoría"""
    # Verificar sesión
    if not AuthService.is_logged_in():
        return redirect(url_for('main.login'))
    
    if request.method == 'GET':
        return render_template('nueva_categoria.html', form_data={})
    
    # POST request
    try:
        empresa_id = session.get('empresa_id')
        nombre = request.form.get('nombre')
        descripcion = request.form.get('descripcion')
        estado = request.form.get('estado', 'activa')
        icono = request.form.get('icono')
        color = request.form.get('color')
        
        result = CategoriaService.create_categoria(
            nombre=nombre,
            descripcion=descripcion,
            estado=estado,
            icono=icono,
            color=color,
            empresa_id=empresa_id
        )
        
        if result['success']:
            flash('Categoría creada exitosamente', 'success')
            return redirect(url_for('main.categorias'))
        else:
            flash(result['error'], 'error')
            return render_template('nueva_categoria.html', form_data=request.form.to_dict())
        
    except Exception as e:
        flash(f'Error al crear la categoría: {str(e)}', 'error')
        return render_template('nueva_categoria.html', form_data=request.form.to_dict())

@main_bp.route('/editar-categoria/<int:categoria_id>', methods=['GET', 'POST'])
def editar_categoria(categoria_id):
    """Editar categoría existente"""
    # Verificar sesión
    if not AuthService.is_logged_in():
        return redirect(url_for('main.login'))
    
    if request.method == 'GET':
        try:
            categoria = CategoriaService.get_categoria_by_id(categoria_id)
            if not categoria:
                flash('Categoría no encontrada', 'error')
                return redirect(url_for('main.categorias'))
            
            form_data = {
                'id': categoria.id,
                'nombre': categoria.nombre,
                'descripcion': categoria.descripcion,
                'estado': categoria.estado,
                'icono': categoria.icono,
                'color': categoria.color
            }
            
            return render_template('editar_categoria.html', 
                                 categoria=categoria,
                                 form_data=form_data)
        except Exception as e:
            flash('Error al cargar la categoría', 'error')
            return redirect(url_for('main.categorias'))
    
    # POST request
    try:
        nombre = request.form.get('nombre')
        descripcion = request.form.get('descripcion')
        estado = request.form.get('estado')
        icono = request.form.get('icono')
        color = request.form.get('color')
        
        result = CategoriaService.update_categoria(
            categoria_id=categoria_id,
            nombre=nombre,
            descripcion=descripcion,
            estado=estado,
            icono=icono,
            color=color
        )
        
        if result['success']:
            flash('Categoría actualizada exitosamente', 'success')
            return redirect(url_for('main.categorias'))
        else:
            flash(result['error'], 'error')
            categoria = CategoriaService.get_categoria_by_id(categoria_id)
            return render_template('editar_categoria.html',
                                 categoria=categoria,
                                 form_data=request.form.to_dict())
        
    except Exception as e:
        flash(f'Error al actualizar la categoría: {str(e)}', 'error')
        categoria = CategoriaService.get_categoria_by_id(categoria_id)
        return render_template('editar_categoria.html',
                             categoria=categoria,
                             form_data=request.form.to_dict())

@main_bp.route('/eliminar-categoria/<int:categoria_id>', methods=['POST'])
def eliminar_categoria(categoria_id):
    """Eliminar categoría"""
    # Verificar sesión
    if not AuthService.is_logged_in():
        return redirect(url_for('main.login'))
    
    try:
        result = CategoriaService.delete_categoria(categoria_id)
        
        if result['success']:
            flash(result['message'], 'success')
        else:
            flash(result['error'], 'error')
        
        return redirect(url_for('main.categorias'))
        
    except Exception as e:
        flash(f'Error al eliminar la categoría: {str(e)}', 'error')
        return redirect(url_for('main.categorias'))

@main_bp.route('/api/categorias', methods=['GET'])
def api_get_categorias():
    """API endpoint para obtener todas las categorías"""
    try:
        # Verificar sesión
        if not AuthService.is_logged_in():
            return jsonify({'success': False, 'error': 'No autorizado'}), 401
        
        empresa_id = session.get('empresa_id')
        categorias = CategoriaService.get_all_categorias(empresa_id)
        
        return jsonify({
            'success': True,
            'categorias': [cat.to_dict() for cat in categorias]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@main_bp.route('/api/categorias/<int:categoria_id>', methods=['GET'])
def api_get_categoria(categoria_id):
    """API endpoint para obtener una categoría por ID"""
    try:
        # Verificar sesión
        if not AuthService.is_logged_in():
            return jsonify({'success': False, 'error': 'No autorizado'}), 401
        
        categoria = CategoriaService.get_categoria_by_id(categoria_id)
        if categoria:
            return jsonify({
                'success': True,
                'categoria': categoria.to_dict()
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Categoría no encontrada'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Rutas para el módulo de Importar Ventas
@main_bp.route('/importar-ventas')
def importar_ventas():
    """Página para importar ventas desde archivos Excel/CSV"""
    if not AuthService.is_logged_in():
        return redirect(url_for('main.login'))
    
    empresa_id = session.get('empresa_id')
    usuario = session.get('usuario_nombre', 'Usuario')
    
    # Obtener historial de importaciones
    historial = ImportacionVentaService.get_import_history(empresa_id)
    
    # Obtener rubros y categorías disponibles para el selector global
    rubros = MovimientoService.get_rubros_for_select(empresa_id)
    categorias = MovimientoService.get_categorias_for_select(empresa_id)
    
    return render_template('importar_ventas.html', 
                         historial=historial,
                         rubros=rubros,
                         categorias=categorias,
                         usuario=usuario)

@main_bp.route('/api/importar-ventas/upload', methods=['POST'])
def api_upload_file():
    """API endpoint para subir archivo y obtener vista previa"""
    try:
        if not AuthService.is_logged_in():
            return jsonify({'success': False, 'error': 'No autorizado'}), 401
        
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No se proporcionó ningún archivo'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No se seleccionó ningún archivo'}), 400
        
        if not ImportacionVentaService.allowed_file(file.filename):
            return jsonify({'success': False, 'error': 'Formato de archivo no soportado. Use .xlsx, .xls o .csv'}), 400
        
        # Guardar archivo temporalmente
        upload_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'temp_uploads')
        os.makedirs(upload_folder, exist_ok=True)
        
        filename = secure_filename(file.filename)
        file_path = os.path.join(upload_folder, filename)
        file.save(file_path)
        
        # Obtener vista previa del archivo
        success, preview_data, error = ImportacionVentaService.get_file_preview(file_path)
        
        if not success:
            # Eliminar archivo temporal en caso de error
            if os.path.exists(file_path):
                os.remove(file_path)
            return jsonify({'success': False, 'error': error}), 400
        
        # Guardar ruta del archivo en sesión para usarlo después
        session['temp_file_path'] = file_path
        session['temp_filename'] = filename
        
        return jsonify({
            'success': True,
            'preview': preview_data
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error al procesar el archivo: {str(e)}'
        }), 500

@main_bp.route('/api/importar-ventas/import', methods=['POST'])
def api_import_ventas():
    """API endpoint para procesar la importación de ventas"""
    try:
        if not AuthService.is_logged_in():
            return jsonify({'success': False, 'error': 'No autorizado'}), 401
        
        # Obtener datos del request
        data = request.get_json()
        mapping = data.get('mapping', {})
        tipo = data.get('tipo', 'ingreso')
        rubro_id = data.get('rubro_id')
        categoria_id = data.get('categoria_id')
        
        # Convertir a int
        try:
            rubro_id = int(rubro_id) if rubro_id else None
            categoria_id = int(categoria_id) if categoria_id else None
        except (ValueError, TypeError):
            return jsonify({'success': False, 'error': 'Rubro o categoría inválido'}), 400
        
        # Validar que el archivo temporal existe
        file_path = session.get('temp_file_path')
        if not file_path or not os.path.exists(file_path):
            return jsonify({'success': False, 'error': 'Archivo no encontrado. Por favor, vuelva a subir el archivo.'}), 400
        
        empresa_id = session.get('empresa_id')
        usuario = session.get('usuario_nombre', 'Usuario')
        
        # Procesar importación
        success, result, error = ImportacionVentaService.import_ventas(
            file_path, mapping, empresa_id, usuario,
            tipo=tipo, rubro_id=rubro_id, categoria_id=categoria_id
        )
        
        # Eliminar archivo temporal
        if os.path.exists(file_path):
            os.remove(file_path)
        session.pop('temp_file_path', None)
        session.pop('temp_filename', None)
        
        if not success:
            return jsonify({'success': False, 'error': error}), 400
        
        return jsonify({
            'success': True,
            'result': result
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error durante la importación: {str(e)}'
        }), 500

@main_bp.route('/api/importar-ventas/historial', methods=['GET'])
def api_import_historial():
    """API endpoint para obtener el historial de importaciones"""
    try:
        if not AuthService.is_logged_in():
            return jsonify({'success': False, 'error': 'No autorizado'}), 401
        
        empresa_id = session.get('empresa_id')
        historial = ImportacionVentaService.get_import_history(empresa_id)
        
        return jsonify({
            'success': True,
            'historial': historial
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ============================================
# API endpoints para notificaciones
# ============================================

@main_bp.route('/api/notifications', methods=['GET'])
def api_get_notifications():
    """API endpoint para obtener notificaciones"""
    try:
        if not AuthService.is_logged_in():
            return jsonify({'success': False, 'error': 'No autorizado'}), 401
        
        empresa_id = session.get('empresa_id')
        user_id = session.get('user_id')
        
        unread_only = request.args.get('unread_only', 'false').lower() == 'true'
        read_only = request.args.get('read_only', 'false').lower() == 'true'
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        type_filter = request.args.get('type', None)
        priority_filter = request.args.get('priority', None)
        search_query = request.args.get('search', None)
        
        # Calcular offset si se usa page/per_page
        if page > 1:
            offset = (page - 1) * per_page
        else:
            per_page = limit
        
        result = NotificationService.get_notifications(
            empresa_id=empresa_id,
            user_id=user_id,
            limit=per_page,
            unread_only=unread_only,
            read_only=read_only,
            type_filter=type_filter,
            priority_filter=priority_filter,
            offset=offset,
            search_query=search_query
        )
        
        return jsonify({
            'success': True,
            'notifications': result['notifications'],
            'total': result['total'],
            'unread_count': result['unread_count']
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@main_bp.route('/api/notifications/<int:notification_id>/read', methods=['POST'])
def api_mark_notification_read(notification_id):
    """API endpoint para marcar notificación como leída"""
    try:
        if not AuthService.is_logged_in():
            return jsonify({'success': False, 'error': 'No autorizado'}), 401
        
        empresa_id = session.get('empresa_id')
        user_id = session.get('user_id')
        
        success = NotificationService.mark_as_read(notification_id, empresa_id, user_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Notificación marcada como leída'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Notificación no encontrada'
            }), 404
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@main_bp.route('/api/notifications/mark-all-read', methods=['POST'])
def api_mark_all_notifications_read():
    """API endpoint para marcar todas las notificaciones como leídas"""
    try:
        if not AuthService.is_logged_in():
            return jsonify({'success': False, 'error': 'No autorizado'}), 401
        
        empresa_id = session.get('empresa_id')
        user_id = session.get('user_id')
        
        count = NotificationService.mark_all_as_read(empresa_id, user_id)
        
        return jsonify({
            'success': True,
            'message': f'{count} notificaciones marcadas como leídas',
            'count': count
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@main_bp.route('/api/notifications/clear-read', methods=['DELETE'])
def api_clear_read_notifications():
    """API endpoint para eliminar todas las notificaciones leídas"""
    try:
        if not AuthService.is_logged_in():
            return jsonify({'success': False, 'error': 'No autorizado'}), 401
        
        empresa_id = session.get('empresa_id')
        
        count = NotificationService.delete_read(empresa_id)
        
        return jsonify({
            'success': True,
            'message': f'{count} notificaciones eliminadas',
            'count': count
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@main_bp.route('/api/notifications/<int:notification_id>', methods=['DELETE'])
def api_delete_notification(notification_id):
    """API endpoint para eliminar notificación"""
    try:
        if not AuthService.is_logged_in():
            return jsonify({'success': False, 'error': 'No autorizado'}), 401
        
        empresa_id = session.get('empresa_id')
        user_id = session.get('user_id')
        
        success = NotificationService.delete_notification(notification_id, empresa_id, user_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Notificación eliminada'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Notificación no encontrada'
            }), 404
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@main_bp.route('/api/notifications/stats', methods=['GET'])
def api_notification_stats():
    """API endpoint para obtener estadísticas de notificaciones"""
    try:
        if not AuthService.is_logged_in():
            return jsonify({'success': False, 'error': 'No autorizado'}), 401
        
        empresa_id = session.get('empresa_id')
        user_id = session.get('user_id')
        
        stats = NotificationService.get_notification_stats(empresa_id, user_id)
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ============================================
# API endpoints para insights financieros
# ============================================

@main_bp.route('/api/insights/summary', methods=['GET'])
def api_get_financial_summary():
    """API endpoint para obtener resumen financiero"""
    try:
        if not AuthService.is_logged_in():
            return jsonify({'success': False, 'error': 'No autorizado'}), 401
        
        empresa_id = session.get('empresa_id')
        dias = int(request.args.get('dias', 7))
        
        # Calcular directamente sin usar el servicio complejo
        from datetime import datetime, timedelta
        from app.models.movimiento import Movimiento
        
        fecha_fin_actual = datetime.utcnow()
        fecha_inicio_actual = fecha_fin_actual - timedelta(days=dias)
        
        # Período actual
        movimientos_actual = Movimiento.query.filter(
            Movimiento.empresa_id == empresa_id,
            Movimiento.fecha >= fecha_inicio_actual,
            Movimiento.fecha <= fecha_fin_actual
        ).all()
        
        ingresos_actual = sum(m.monto for m in movimientos_actual if m.tipo == 'ingreso')
        gastos_actual = sum(m.monto for m in movimientos_actual if m.tipo == 'gasto')
        ganancia_actual = ingresos_actual - gastos_actual
        
        # Período anterior
        fecha_fin_anterior = fecha_inicio_actual - timedelta(days=1)
        fecha_inicio_anterior = fecha_fin_anterior - timedelta(days=dias)
        
        movimientos_anterior = Movimiento.query.filter(
            Movimiento.empresa_id == empresa_id,
            Movimiento.fecha >= fecha_inicio_anterior,
            Movimiento.fecha <= fecha_fin_anterior
        ).all()
        
        ingresos_anterior = sum(m.monto for m in movimientos_anterior if m.tipo == 'ingreso')
        gastos_anterior = sum(m.monto for m in movimientos_anterior if m.tipo == 'gasto')
        ganancia_anterior = ingresos_anterior - gastos_anterior
        
        # Cálculo de variación porcentual real respecto al periodo anterior.
        # Si no hubo movimientos antes, no hay comparativa posible -> None.
        if ganancia_anterior == 0 and ganancia_actual == 0:
            variacion_ganancia = 0.0
        elif ganancia_anterior == 0:
            # No hay base de comparación
            variacion_ganancia = None
        else:
            variacion = (ganancia_actual - ganancia_anterior) / abs(ganancia_anterior) * 100
            # Limitar a un rango razonable para evitar valores extremos en la UI
            variacion_ganancia = round(max(-999.0, min(999.0, variacion)), 1)
        
        summary = {
            'ganancia_neta': ganancia_actual,
            'total_ingresos': ingresos_actual,
            'total_gastos': gastos_actual,
            'crecimiento': {
                'ganancia_actual': ganancia_actual,
                'ingresos_actual': ingresos_actual,
                'gastos_actual': gastos_actual,
                'variacion_ganancia': variacion_ganancia
            }
        }
        
        return jsonify({
            'success': True,
            'summary': summary
        })
        
    except Exception as e:
        current_app.logger.error(f"Error en api_get_financial_summary: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@main_bp.route('/api/insights/rubro-top', methods=['GET'])
def api_get_rubro_top():
    """API endpoint para obtener rubro top"""
    try:
        if not AuthService.is_logged_in():
            return jsonify({'success': False, 'error': 'No autorizado'}), 401
        
        empresa_id = session.get('empresa_id')
        dias = int(request.args.get('dias', 7))
        
        # Calcular directamente
        from datetime import datetime, timedelta
        from app.models.movimiento import Movimiento
        
        fecha_inicio = datetime.utcnow() - timedelta(days=dias)
        
        # Obtener movimientos de ingresos por rubro
        movimientos = Movimiento.query.filter(
            Movimiento.empresa_id == empresa_id,
            Movimiento.tipo == 'ingreso',
            Movimiento.fecha >= fecha_inicio
        ).all()
        
        # Agrupar por rubro
        rubros_ingresos = {}
        total_ingresos = 0
        
        for mov in movimientos:
            if mov.rubro_id:
                rubro_nombre = mov.rubro.nombre if mov.rubro else 'Sin rubro'
                rubros_ingresos[rubro_nombre] = rubros_ingresos.get(rubro_nombre, 0) + float(mov.monto)
                total_ingresos += float(mov.monto)
        
        if not rubros_ingresos:
            rubro_top = {
                'rubro_nombre': None,
                'ingresos': 0,
                'porcentaje': 0
            }
        else:
            # Encontrar rubro top
            rubro_top_nombre = max(rubros_ingresos, key=rubros_ingresos.get)
            rubro_top_ingresos = rubros_ingresos[rubro_top_nombre]
            porcentaje = (rubro_top_ingresos / total_ingresos * 100) if total_ingresos > 0 else 0
            
            rubro_top = {
                'rubro_nombre': rubro_top_nombre,
                'ingresos': rubro_top_ingresos,
                'porcentaje': porcentaje
            }
        
        return jsonify({
            'success': True,
            'rubro_top': rubro_top
        })
        
    except Exception as e:
        current_app.logger.error(f"Error en api_get_rubro_top: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@main_bp.route('/api/insights/rubro-analysis', methods=['GET'])
def api_get_rubro_analysis():
    """API endpoint para obtener análisis por rubro"""
    try:
        if not AuthService.is_logged_in():
            return jsonify({'success': False, 'error': 'No autorizado'}), 401
        
        empresa_id = session.get('empresa_id')
        dias = int(request.args.get('dias', 7))
        
        analysis = FinancialInsightsService.analizar_por_rubro(empresa_id, dias)
        
        return jsonify({
            'success': True,
            'analysis': analysis
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@main_bp.route('/api/insights/ticket-avg', methods=['GET'])
def api_get_ticket_average():
    """API endpoint para obtener ticket promedio"""
    try:
        if not AuthService.is_logged_in():
            return jsonify({'success': False, 'error': 'No autorizado'}), 401
        
        empresa_id = session.get('empresa_id')
        dias = int(request.args.get('dias', 7))
        
        ticket_avg = FinancialInsightsService.calcular_ticket_promedio(empresa_id, dias)
        
        return jsonify({
            'success': True,
            'ticket_avg': ticket_avg
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@main_bp.route('/api/insights/generate', methods=['POST'])
def api_generate_insights():
    """API endpoint para generar insights automáticos"""
    try:
        if not AuthService.is_logged_in():
            return jsonify({'success': False, 'error': 'No autorizado'}), 401
        
        empresa_id = session.get('empresa_id')
        dias = int(request.args.get('dias', 7))
        
        notifications = FinancialInsightsService.generar_insights_automaticos(empresa_id, dias)
        
        return jsonify({
            'success': True,
            'generated_count': len(notifications),
            'notifications': [notif.to_dict() for notif in notifications]
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
