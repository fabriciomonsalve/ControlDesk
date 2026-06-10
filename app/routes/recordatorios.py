"""
Rutas para el módulo de Recordatorios y Vencimientos
"""

from flask import Blueprint, render_template, request, jsonify, current_app, session
from datetime import datetime
from app.services.recordatorios_service import RecordatoriosService
from app.services.rubro_service import RubroService
from app.services.auth_service import AuthService
from app import db

recordatorios_bp = Blueprint('recordatorios', __name__)


@recordatorios_bp.route('/recordatorios')
def recordatorios():
    """Página principal de gestión de recordatorios"""
    try:
        empresa_actual = AuthService.get_current_empresa()
        empresa_id = empresa_actual['id'] if empresa_actual else None
        
        # Actualizar estados automáticamente
        RecordatoriosService.actualizar_estados_automaticos(empresa_id)
        
        # Obtener parámetros de página
        pendientes_page = request.args.get('pendientes_page', 1, type=int)
        completados_page = request.args.get('completados_page', 1, type=int)
        todos_page = request.args.get('todos_page', 1, type=int)
        
        # Obtener recordatorios por estado con paginación
        pendientes, pendientes_pages, pendientes_total = RecordatoriosService.obtener_pendientes(empresa_id, page=pendientes_page, per_page=5)
        proximos = RecordatoriosService.obtener_proximos(empresa_id)
        vencidos = RecordatoriosService.obtener_vencidos(empresa_id)
        completados, completados_pages, completados_total = RecordatoriosService.obtener_completados(empresa_id, page=completados_page, per_page=5)
        
        # Obtener resumen
        resumen = RecordatoriosService.obtener_resumen(empresa_id)
        
        # Obtener todos los recordatorios con paginación
        todos_recordatorios, todos_pages, todos_total = RecordatoriosService.obtener_todos(empresa_id, page=todos_page, per_page=7)
        
        return render_template(
            'recordatorios.html',
            pendientes=pendientes,
            proximos=proximos,
            vencidos=vencidos,
            completados=completados,
            todos_recordatorios=todos_recordatorios,
            resumen=resumen,
            pendientes_page=pendientes_page,
            pendientes_pages=pendientes_pages,
            pendientes_total=pendientes_total,
            completados_page=completados_page,
            completados_pages=completados_pages,
            completados_total=completados_total,
            todos_page=todos_page,
            todos_pages=todos_pages,
            todos_total=todos_total
        )
    except Exception as e:
        current_app.logger.error(f"Error en ruta recordatorios: {e}")
        return render_template(
            'recordatorios.html', 
            pendientes=[], 
            proximos=[], 
            vencidos=[], 
            completados=[], 
            todos_recordatorios=[], 
            resumen={},
            pendientes_page=1,
            pendientes_pages=1,
            pendientes_total=0,
            completados_page=1,
            completados_pages=1,
            completados_total=0,
            todos_page=1,
            todos_pages=1,
            todos_total=0
        )


@recordatorios_bp.route('/recordatorios/nuevo')
def nuevo_recordatorio():
    """Página para crear nuevo recordatorio"""
    try:
        empresa_actual = AuthService.get_current_empresa()
        empresa_id = empresa_actual['id'] if empresa_actual else None
        rubros = RubroService.get_all_rubros(empresa_id)
        
        return render_template(
            'nuevo_recordatorio.html',
            rubros=rubros,
            prioridades=RecordatoriosService.PRIORIDADES,
            tipos=RecordatoriosService.TIPOS,
            frecuencias=RecordatoriosService.FRECUENCIAS,
            dias_aviso=RecordatoriosService.DIAS_AVISO
        )
    except Exception as e:
        current_app.logger.error(f"Error en ruta nuevo recordatorio: {e}")
        return render_template('nuevo_recordatorio.html', rubros=[])


@recordatorios_bp.route('/recordatorios/<int:recordatorio_id>/editar')
def editar_recordatorio(recordatorio_id):
    """Página para editar recordatorio"""
    try:
        from app.models.recordatorio import Recordatorio
        
        recordatorio = Recordatorio.query.get(recordatorio_id)
        if not recordatorio:
            return render_template('recordatorios.html', error="Recordatorio no encontrado")
        
        # Verificar empresa del usuario si está logueado
        empresa_actual = AuthService.get_current_empresa()
        if empresa_actual and recordatorio.empresa_id != empresa_actual['id']:
            return render_template('recordatorios.html', error="No tienes permiso para acceder a este recordatorio")
        
        empresa_id = empresa_actual['id'] if empresa_actual else None
        rubros = RubroService.get_all_rubros(empresa_id)
        
        return render_template(
            'editar_recordatorio.html',
            recordatorio=recordatorio,
            rubros=rubros,
            prioridades=RecordatoriosService.PRIORIDADES,
            tipos=RecordatoriosService.TIPOS,
            frecuencias=RecordatoriosService.FRECUENCIAS,
            dias_aviso=RecordatoriosService.DIAS_AVISO
        )
    except Exception as e:
        current_app.logger.error(f"Error en ruta editar recordatorio: {e}")
        return render_template('recordatorios.html', error="Error al cargar recordatorio")


# API Routes

@recordatorios_bp.route('/api/recordatorios', methods=['POST'])
def api_crear_recordatorio():
    """API endpoint para crear un nuevo recordatorio"""
    try:
        data = request.get_json()
        
        # Validar campos requeridos
        required_fields = ['titulo', 'fecha_vencimiento']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Campo requerido faltante: {field}'
                }), 400
        
        # Convertir fecha
        fecha_vencimiento = datetime.strptime(data['fecha_vencimiento'], '%Y-%m-%dT%H:%M')
        
        empresa_actual = AuthService.get_current_empresa()
        empresa_id = empresa_actual['id'] if empresa_actual else None
        success, message, recordatorio = RecordatoriosService.crear_recordatorio(
            empresa_id=empresa_id,
            titulo=data['titulo'],
            fecha_vencimiento=fecha_vencimiento,
            tipo=data.get('tipo', 'general'),
            prioridad=data.get('prioridad', 'media'),
            descripcion=data.get('descripcion'),
            rubro_id=data.get('rubro_id'),
            monto=data.get('monto'),
            dias_aviso=data.get('dias_aviso', 3),
            recurrente=data.get('recurrente', False),
            frecuencia=data.get('frecuencia'),
            sonido=data.get('sonido', 'default')
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': message,
                'recordatorio': recordatorio.to_dict() if recordatorio else None
            })
        else:
            return jsonify({
                'success': False,
                'error': message
            }), 400
            
    except Exception as e:
        current_app.logger.error(f"Error creando recordatorio: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@recordatorios_bp.route('/api/recordatorios/<int:recordatorio_id>/estado', methods=['PUT'])
def api_actualizar_estado(recordatorio_id):
    """API endpoint para actualizar el estado de un recordatorio"""
    try:
        data = request.get_json()
        nuevo_estado = data.get('estado')
        
        if not nuevo_estado:
            return jsonify({
                'success': False,
                'error': 'Estado no proporcionado'
            }), 400
        
        empresa_actual = AuthService.get_current_empresa()
        usuario = empresa_actual['nombre'] if empresa_actual else None
        success, message = RecordatoriosService.actualizar_estado(
            recordatorio_id=recordatorio_id,
            nuevo_estado=nuevo_estado,
            usuario=usuario
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': message
            })
        else:
            return jsonify({
                'success': False,
                'error': message
            }), 400
            
    except Exception as e:
        current_app.logger.error(f"Error actualizando estado: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@recordatorios_bp.route('/api/recordatorios/<int:recordatorio_id>/completar', methods=['POST'])
def api_completar_recordatorio(recordatorio_id):
    """API endpoint para completar un recordatorio"""
    try:
        from app.models.recordatorio import Recordatorio
        
        recordatorio = Recordatorio.query.get(recordatorio_id)
        if not recordatorio:
            return jsonify({
                'success': False,
                'error': 'Recordatorio no encontrado'
            }), 404
        
        # Verificar empresa del usuario si está logueado
        empresa_actual = AuthService.get_current_empresa()
        if empresa_actual and recordatorio.empresa_id != empresa_actual['id']:
            return jsonify({
                'success': False,
                'error': 'No tienes permiso para acceder a este recordatorio'
            }), 403
        
        empresa_actual = AuthService.get_current_empresa()
        usuario = empresa_actual['nombre'] if empresa_actual else None
        success, message = RecordatoriosService.actualizar_estado(
            recordatorio_id=recordatorio_id,
            nuevo_estado='completado',
            usuario=usuario
        )
        
        if not success:
            return jsonify({
                'success': False,
                'error': message
            }), 400
        
        # Si tiene monto asociado, preguntar si registrar gasto
        response = {
            'success': True,
            'message': message,
            'registrar_gasto': False
        }
        
        if recordatorio.monto and recordatorio.monto > 0:
            response['registrar_gasto'] = True
            response['monto'] = recordatorio.monto
        
        return jsonify(response)
            
    except Exception as e:
        current_app.logger.error(f"Error completando recordatorio: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@recordatorios_bp.route('/api/recordatorios/<int:recordatorio_id>/registrar-gasto', methods=['POST'])
def api_registrar_gasto(recordatorio_id):
    """API endpoint para registrar gasto desde recordatorio"""
    try:
        from app.models.recordatorio import Recordatorio
        
        recordatorio = Recordatorio.query.get(recordatorio_id)
        if not recordatorio:
            return jsonify({
                'success': False,
                'error': 'Recordatorio no encontrado'
            }), 404
        
        # Verificar empresa del usuario si está logueado
        empresa_actual = AuthService.get_current_empresa()
        if empresa_actual and recordatorio.empresa_id != empresa_actual['id']:
            return jsonify({
                'success': False,
                'error': 'No tienes permiso para acceder a este recordatorio'
            }), 403
        
        empresa_actual = AuthService.get_current_empresa()
        usuario = empresa_actual['nombre'] if empresa_actual else None
        success, message, movimiento = RecordatoriosService.registrar_gasto(
            recordatorio_id=recordatorio_id,
            usuario=usuario
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': message,
                'movimiento': movimiento.to_dict() if movimiento else None
            })
        else:
            return jsonify({
                'success': False,
                'error': message
            }), 400
            
    except Exception as e:
        current_app.logger.error(f"Error registrando gasto: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@recordatorios_bp.route('/api/recordatorios/<int:recordatorio_id>', methods=['PUT'])
def api_actualizar_recordatorio(recordatorio_id):
    """API endpoint para actualizar un recordatorio"""
    try:
        from app.models.recordatorio import Recordatorio
        
        recordatorio = Recordatorio.query.get(recordatorio_id)
        if not recordatorio:
            return jsonify({
                'success': False,
                'error': 'Recordatorio no encontrado'
            }), 404
        
        # Verificar empresa del usuario si está logueado
        empresa_actual = AuthService.get_current_empresa()
        if empresa_actual and recordatorio.empresa_id != empresa_actual['id']:
            return jsonify({
                'success': False,
                'error': 'No tienes permiso para acceder a este recordatorio'
            }), 403
        
        data = request.get_json()
        
        # Actualizar campos
        if 'titulo' in data:
            recordatorio.titulo = data['titulo']
        if 'descripcion' in data:
            recordatorio.descripcion = data['descripcion']
        if 'tipo' in data:
            recordatorio.tipo = data['tipo']
        if 'prioridad' in data:
            recordatorio.prioridad = data['prioridad']
        if 'rubro_id' in data:
            recordatorio.rubro_id = data['rubro_id']
        if 'monto' in data:
            recordatorio.monto = data['monto']
        if 'dias_aviso' in data:
            recordatorio.dias_aviso = data['dias_aviso']
            # Recalcular fecha de aviso
            from app.services.recordatorios_service import RecordatoriosService
            recordatorio.fecha_aviso = RecordatoriosService.calcular_fecha_aviso(
                recordatorio.fecha_vencimiento, 
                data['dias_aviso']
            )
        if 'recurrente' in data:
            recordatorio.recurrente = data['recurrente']
        if 'frecuencia' in data:
            recordatorio.frecuencia = data['frecuencia']
        if 'sonido' in data:
            recordatorio.sonido = data['sonido']
        
        recordatorio.fecha_actualizacion = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Recordatorio actualizado exitosamente',
            'recordatorio': recordatorio.to_dict()
        })
        
    except Exception as e:
        current_app.logger.error(f"Error actualizando recordatorio: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@recordatorios_bp.route('/api/recordatorios/<int:recordatorio_id>', methods=['DELETE'])
def api_eliminar_recordatorio(recordatorio_id):
    """API endpoint para eliminar un recordatorio"""
    try:
        from app.models.recordatorio import Recordatorio
        
        recordatorio = Recordatorio.query.get(recordatorio_id)
        if not recordatorio:
            return jsonify({
                'success': False,
                'error': 'Recordatorio no encontrado'
            }), 404
        
        # Verificar empresa del usuario si está logueado
        empresa_actual = AuthService.get_current_empresa()
        if empresa_actual and recordatorio.empresa_id != empresa_actual['id']:
            return jsonify({
                'success': False,
                'error': 'No tienes permiso para eliminar este recordatorio'
            }), 403
        
        success, message = RecordatoriosService.eliminar_recordatorio(recordatorio_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': message
            })
        else:
            return jsonify({
                'success': False,
                'error': message
            }), 404
            
    except Exception as e:
        current_app.logger.error(f"Error eliminando recordatorio: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@recordatorios_bp.route('/api/recordatorios/resumen', methods=['GET'])
def api_obtener_resumen():
    """API endpoint para obtener el resumen de recordatorios"""
    try:
        empresa_actual = AuthService.get_current_empresa()
        empresa_id = empresa_actual['id'] if empresa_actual else None
        resumen = RecordatoriosService.obtener_resumen(empresa_id)
        
        return jsonify({
            'success': True,
            'resumen': resumen
        })
        
    except Exception as e:
        current_app.logger.error(f"Error obteniendo resumen: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@recordatorios_bp.route('/api/recordatorios/alertas', methods=['GET'])
def api_obtener_alertas():
    """API endpoint para obtener alertas de recordatorios (próximos y vencidos)"""
    try:
        empresa_actual = AuthService.get_current_empresa()
        empresa_id = empresa_actual['id'] if empresa_actual else None
        
        # Actualizar estados automáticamente
        RecordatoriosService.actualizar_estados_automaticos(empresa_id)
        
        # Obtener próximos y vencidos
        proximos = RecordatoriosService.obtener_proximos(empresa_id)
        vencidos = RecordatoriosService.obtener_vencidos(empresa_id)
        
        alertas = []
        
        for r in proximos:
            alertas.append({
                'id': r.id,
                'titulo': r.titulo,
                'fecha_vencimiento': r.fecha_vencimiento.isoformat(),
                'prioridad': r.prioridad,
                'tipo': 'proximo',
                'monto': r.monto,
                'rubro': r.rubro.nombre if r.rubro else None
            })
        
        for r in vencidos:
            alertas.append({
                'id': r.id,
                'titulo': r.titulo,
                'fecha_vencimiento': r.fecha_vencimiento.isoformat(),
                'prioridad': r.prioridad,
                'tipo': 'vencido',
                'monto': r.monto,
                'rubro': r.rubro.nombre if r.rubro else None
            })
        
        # Ordenar por fecha de vencimiento
        alertas.sort(key=lambda x: x['fecha_vencimiento'])
        
        return jsonify({
            'success': True,
            'alertas': alertas,
            'total': len(alertas),
            'proximos': len(proximos),
            'vencidos': len(vencidos)
        })
        
    except Exception as e:
        current_app.logger.error(f"Error obteniendo alertas: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@recordatorios_bp.route('/api/recordatorios/actualizar-estados', methods=['POST'])
def api_actualizar_estados():
    """API endpoint para actualizar automáticamente los estados"""
    try:
        empresa_actual = AuthService.get_current_empresa()
        empresa_id = empresa_actual['id'] if empresa_actual else None
        actualizados = RecordatoriosService.actualizar_estados_automaticos(empresa_id)
        
        return jsonify({
            'success': True,
            'actualizados': actualizados
        })
        
    except Exception as e:
        current_app.logger.error(f"Error actualizando estados: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
