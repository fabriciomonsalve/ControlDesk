"""
Rutas para el módulo de Gestión de Facturas y Compras
"""

from flask import Blueprint, render_template, request, jsonify, current_app
from werkzeug.utils import secure_filename
import os
from datetime import datetime
from app.services.facturas_service import FacturasService
from app.services.rubro_service import RubroService
from flask_login import login_required, current_user

facturas_bp = Blueprint('facturas', __name__)

# Directorio para guardar archivos
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads', 'facturas')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@facturas_bp.route('/facturas')
def facturas():
    """Página principal de gestión de facturas"""
    try:
        empresa_id = current_user.empresa_id if current_user.is_authenticated else None
        facturas = FacturasService.get_all_facturas(empresa_id)
        return render_template('facturas.html', facturas=facturas)
    except Exception as e:
        current_app.logger.error(f"Error en ruta facturas: {e}")
        return render_template('facturas.html', facturas=[])


@facturas_bp.route('/facturas/previsualizar')
def previsualizar():
    """Página de previsualización de factura"""
    return render_template('previsualizacion_factura.html')


@facturas_bp.route('/facturas/<int:factura_id>')
def detalle_factura(factura_id):
    """Página de detalle de factura"""
    try:
        factura = FacturasService.get_factura_by_id(factura_id)
        if not factura:
            return render_template('facturas.html', facturas=[], error="Factura no encontrada")
        return render_template('detalle_factura.html', factura=factura)
    except Exception as e:
        current_app.logger.error(f"Error en ruta detalle factura: {e}")
        return render_template('facturas.html', facturas=[], error="Error al cargar factura")


@facturas_bp.route('/facturas/previsualizar', methods=['POST'])
def previsualizar_factura():
    """Previsualiza una factura antes de guardar"""
    try:
        # Validar archivo
        if 'archivo' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No se proporcionó ningún archivo'
            }), 400
        
        file = request.files['archivo']
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No se seleccionó ningún archivo'
            }), 400
        
        # Validar archivo
        is_valid, error_msg = FacturasService.validate_file(file)
        if not is_valid:
            return jsonify({
                'success': False,
                'error': error_msg
            }), 400
        
        # Guardar archivo
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{filename}"
        save_path = os.path.join(UPLOAD_FOLDER, filename)
        
        # Procesar archivo
        success, message, extracted_data = FacturasService.procesar_archivo(file, filename, save_path)
        
        if not success:
            return jsonify({
                'success': False,
                'error': message
            }), 400
        
        # Obtener rubros disponibles
        empresa_id = current_user.empresa_id if current_user.is_authenticated else None
        rubros = RubroService.get_all_rubros(empresa_id)
        
        return jsonify({
            'success': True,
            'message': message,
            'data': extracted_data,
            'rubros': rubros,
            'archivo_path': filename
        })
        
    except Exception as e:
        current_app.logger.error(f"Error previsualizando factura: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@facturas_bp.route('/api/facturas', methods=['POST'])
def api_registrar_factura():
    """API endpoint para registrar una factura"""
    try:
        data = request.get_json()
        
        # Validar datos requeridos
        required_fields = ['proveedor', 'numero_factura', 'fecha_factura', 'subtotal', 'iva', 'total', 'productos', 'rubro_asignaciones']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Campo requerido faltante: {field}'
                }), 400
        
        # Convertir fecha
        fecha_factura = datetime.strptime(data['fecha_factura'], '%Y-%m-%d').date()
        
        # Registrar factura
        empresa_id = current_user.empresa_id if current_user.is_authenticated else None
        success, message, factura = FacturasService.registrar_factura(
            empresa_id=empresa_id,
            proveedor=data['proveedor'],
            numero_factura=data['numero_factura'],
            fecha_factura=fecha_factura,
            subtotal=data['subtotal'],
            iva=data['iva'],
            total=data['total'],
            productos=data['productos'],
            rubro_asignaciones=data['rubro_asignaciones'],
            archivo_original=data.get('archivo_path'),
            tipo_archivo=data.get('tipo_archivo')
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': message,
                'factura': factura.to_dict() if factura else None
            })
        else:
            return jsonify({
                'success': False,
                'error': message
            }), 400
            
    except Exception as e:
        current_app.logger.error(f"Error registrando factura: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@facturas_bp.route('/api/facturas', methods=['GET'])
def api_get_facturas():
    """API endpoint para obtener todas las facturas"""
    try:
        empresa_id = current_user.empresa_id if current_user.is_authenticated else None
        facturas = FacturasService.get_all_facturas(empresa_id)
        
        return jsonify({
            'success': True,
            'facturas': facturas
        })
        
    except Exception as e:
        current_app.logger.error(f"Error obteniendo facturas: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@facturas_bp.route('/api/facturas/<int:factura_id>', methods=['GET'])
def api_get_factura(factura_id):
    """API endpoint para obtener una factura por su ID"""
    try:
        factura = FacturasService.get_factura_by_id(factura_id)
        
        if not factura:
            return jsonify({
                'success': False,
                'error': 'Factura no encontrada'
            }), 404
        
        return jsonify({
            'success': True,
            'factura': factura
        })
        
    except Exception as e:
        current_app.logger.error(f"Error obteniendo factura: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@facturas_bp.route('/api/facturas/<int:factura_id>', methods=['DELETE'])
def api_delete_factura(factura_id):
    """API endpoint para eliminar una factura"""
    try:
        success, message = FacturasService.delete_factura(factura_id)
        
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
        current_app.logger.error(f"Error eliminando factura: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
