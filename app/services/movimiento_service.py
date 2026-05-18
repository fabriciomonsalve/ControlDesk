"""
Servicio para manejar operaciones CRUD de Movimientos
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from flask import current_app
from app import db
from app.models.movimiento import Movimiento
from app.models.rubro import Rubro
from app.models.categoria import Categoria


class MovimientoService:
    """Servicio para gestionar movimientos financieros"""
    
    @staticmethod
    def get_all_movimientos(tipo: str = None, rubro_id: int = None, categoria_id: int = None, 
                          fecha_desde: str = None, fecha_hasta: str = None, page: int = 1, 
                          per_page: int = 10, empresa_id: int = None) -> Dict[str, Any]:
        """
        Obtiene movimientos con filtros opcionales y paginación
        Args:
            tipo: 'ingreso' o 'gasto'
            rubro_id: ID del rubro
            categoria_id: ID de la categoría
            fecha_desde: Fecha inicial (YYYY-MM-DD)
            fecha_hasta: Fecha final (YYYY-MM-DD)
            page: Número de página (default: 1)
            per_page: Items por página (default: 10)
            empresa_id: ID de la empresa para filtrar
        Returns:
            Dict con movimientos, paginación y total
        """
        try:
            query = Movimiento.query
            
            # Aplicar filtros
            if empresa_id:
                query = query.filter(Movimiento.empresa_id == empresa_id)
            
            if tipo:
                query = query.filter(Movimiento.tipo == tipo)
            
            if rubro_id:
                query = query.filter(Movimiento.rubro_id == rubro_id)
            
            if categoria_id:
                query = query.filter(Movimiento.categoria_id == categoria_id)
            
            if fecha_desde:
                fecha_desde_dt = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
                query = query.filter(Movimiento.fecha >= fecha_desde_dt)
            
            if fecha_hasta:
                fecha_hasta_dt = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
                query = query.filter(Movimiento.fecha <= fecha_hasta_dt)
            
            # Contar total de resultados
            total = query.count()
            
            # Aplicar paginación con ordenamiento por fecha de creación descendente
            offset = (page - 1) * per_page
            movimientos = query.order_by(Movimiento.created_at.desc()).offset(offset).limit(per_page).all()
            
            # Calcular información de paginación
            total_pages = (total + per_page - 1) // per_page
            has_prev = page > 1
            has_next = page < total_pages
            
            return {
                'movimientos': movimientos,
                'total': total,
                'page': page,
                'per_page': per_page,
                'total_pages': total_pages,
                'has_prev': has_prev,
                'has_next': has_next,
                'prev_num': page - 1 if has_prev else None,
                'next_num': page + 1 if has_next else None
            }
            
        except Exception as e:
            current_app.logger.error(f"Error obteniendo movimientos filtrados: {str(e)}")
            return {
                'movimientos': [],
                'total': 0,
                'page': page,
                'per_page': per_page,
                'total_pages': 0,
                'has_prev': False,
                'has_next': False,
                'prev_num': None,
                'next_num': None
            }
    
    @staticmethod
    def get_movimiento_by_id(movimiento_id: int) -> Optional[Movimiento]:
        """
        Obtiene un movimiento por su ID
        """
        try:
            return Movimiento.query.get(movimiento_id)
        except Exception as e:
            current_app.logger.error(f"Error obteniendo movimiento {movimiento_id}: {str(e)}")
            return None
    
    @staticmethod
    def create_movimiento(data: Dict[str, Any], empresa_id: int = None) -> tuple[Optional[Movimiento], Optional[str]]:
        """
        Crea un nuevo movimiento
        
        Args:
            data: Diccionario con los datos del movimiento
            empresa_id: ID de la empresa
            
        Returns:
            Tuple con (movimiento_creado, error_message)
        """
        try:
            # Validaciones básicas
            error = MovimientoService._validate_movimiento_data(data)
            if error:
                return None, error
            
            # Crear nuevo movimiento
            movimiento = Movimiento(
                tipo=data['tipo'],
                monto=float(data['monto']),
                fecha=datetime.strptime(data['fecha'], '%Y-%m-%d').date(),
                descripcion=data.get('descripcion', '').strip(),
                rubro_id=int(data['rubro_id']),
                categoria_id=int(data['categoria_id']),
                empresa_id=empresa_id
            )
            
            db.session.add(movimiento)
            db.session.commit()
            
            return movimiento, None
            
        except ValueError as e:
            db.session.rollback()
            return None, f"Error en el formato de los datos: {str(e)}"
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creando movimiento: {str(e)}")
            return None, "Error al crear el movimiento"
    
    @staticmethod
    def update_movimiento(movimiento_id: int, data: Dict[str, Any]) -> tuple[Optional[Movimiento], Optional[str]]:
        """
        Actualiza un movimiento existente
        
        Args:
            movimiento_id: ID del movimiento a actualizar
            data: Diccionario con los nuevos datos
            
        Returns:
            Tuple con (movimiento_actualizado, error_message)
        """
        try:
            movimiento = MovimientoService.get_movimiento_by_id(movimiento_id)
            if not movimiento:
                return None, "Movimiento no encontrado"
            
            # Validaciones básicas
            error = MovimientoService._validate_movimiento_data(data)
            if error:
                return None, error
            
            # Actualizar campos
            movimiento.tipo = data['tipo']
            movimiento.monto = float(data['monto'])
            movimiento.fecha = datetime.strptime(data['fecha'], '%Y-%m-%d').date()
            movimiento.descripcion = data.get('descripcion', '').strip()
            movimiento.rubro_id = int(data['rubro_id'])
            movimiento.categoria_id = int(data['categoria_id'])
            
            db.session.commit()
            
            return movimiento, None
            
        except ValueError as e:
            db.session.rollback()
            return None, f"Error en el formato de los datos: {str(e)}"
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error actualizando movimiento {movimiento_id}: {str(e)}")
            return None, "Error al actualizar el movimiento"
    
    @staticmethod
    def delete_movimiento(movimiento_id: int) -> tuple[bool, Optional[str]]:
        """
        Elimina un movimiento
        
        Args:
            movimiento_id: ID del movimiento a eliminar
            
        Returns:
            Tuple con (eliminado, error_message)
        """
        try:
            movimiento = MovimientoService.get_movimiento_by_id(movimiento_id)
            if not movimiento:
                return False, "Movimiento no encontrado"
            
            db.session.delete(movimiento)
            db.session.commit()
            
            return True, None
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error eliminando movimiento {movimiento_id}: {str(e)}")
            return False, "Error al eliminar el movimiento"
    
    @staticmethod
    def get_movimientos_by_rubro(rubro_id: int) -> List[Movimiento]:
        """
        Obtiene movimientos filtrados por rubro
        """
        try:
            return Movimiento.query.filter_by(rubro_id=rubro_id).order_by(Movimiento.created_at.desc()).all()
        except Exception as e:
            current_app.logger.error(f"Error obteniendo movimientos del rubro {rubro_id}: {str(e)}")
            return []
    
    @staticmethod
    def get_movimientos_by_tipo(tipo: str) -> List[Movimiento]:
        """
        Obtiene movimientos filtrados por tipo (ingreso/gasto)
        """
        try:
            return Movimiento.query.filter_by(tipo=tipo).order_by(Movimiento.created_at.desc()).all()
        except Exception as e:
            current_app.logger.error(f"Error obteniendo movimientos de tipo {tipo}: {str(e)}")
            return []
    
    @staticmethod
    def get_rubros_for_select(empresa_id: int = None) -> List[Dict[str, Any]]:
        """
        Obtiene lista de rubros para formulario select
        Args:
            empresa_id: ID de la empresa para filtrar
        """
        try:
            query = Rubro.query
            if empresa_id:
                query = query.filter(Rubro.empresa_id == empresa_id)
            rubros = query.all()
            return [{'id': r.id, 'nombre': r.nombre} for r in rubros]
        except Exception as e:
            current_app.logger.error(f"Error obteniendo rubros: {str(e)}")
            return []
    
    @staticmethod
    def get_categorias_for_select(empresa_id: int = None) -> List[Dict[str, Any]]:
        """
        Obtiene lista de categorías para formulario select
        Args:
            empresa_id: ID de la empresa para filtrar
        """
        try:
            from app.models.categoria import Categoria
            query = Categoria.query
            if empresa_id:
                query = query.filter(Categoria.empresa_id == empresa_id)
            categorias = query.all()
            return [{'id': c.id, 'nombre': c.nombre} for c in categorias]
        except Exception as e:
            current_app.logger.error(f"Error obteniendo categorías: {str(e)}")
            return []
    
    @staticmethod
    def _validate_movimiento_data(data: Dict[str, Any]) -> Optional[str]:
        """
        Valida los datos básicos de un movimiento
        
        Args:
            data: Diccionario con los datos a validar
            
        Returns:
            Mensaje de error o None si es válido
        """
        # Validar campos requeridos
        required_fields = ['tipo', 'monto', 'fecha', 'rubro_id', 'categoria_id']
        for field in required_fields:
            if field not in data or not str(data[field]).strip():
                return f"El campo '{field}' es requerido"
        
        # Validar tipo
        if data['tipo'] not in ['ingreso', 'gasto']:
            return "El tipo debe ser 'ingreso' o 'gasto'"
        
        # Validar monto
        try:
            monto = float(data['monto'])
            if monto <= 0:
                return "El monto debe ser mayor a 0"
        except ValueError:
            return "El monto debe ser un número válido"
        
        # Validar fecha
        try:
            datetime.strptime(data['fecha'], '%Y-%m-%d')
        except ValueError:
            return "La fecha debe tener el formato YYYY-MM-DD"
        
        # Validar IDs
        try:
            if int(data['rubro_id']) <= 0:
                return "Debe seleccionar un rubro válido"
            if int(data['categoria_id']) <= 0:
                return "Debe seleccionar una categoría válida"
        except ValueError:
            return "Los IDs deben ser números válidos"
        
        return None
