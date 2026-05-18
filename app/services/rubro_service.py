"""
Servicio para gestionar rubros
"""

from typing import List, Dict, Any, Optional
from flask import current_app
from sqlalchemy import func
from app import db
from app.models.rubro import Rubro
from app.models.movimiento import Movimiento
import random


class RubroService:
    """Servicio para operaciones CRUD de rubros"""
    
    @staticmethod
    def _generate_unique_color() -> str:
        """
        Genera un color único que no esté en uso por otros rubros
        Returns:
            Color en formato hexadecimal (ej: #2563eb)
        """
        # Paleta de colores vibrantes y profesionales
        colors = [
            '#2563eb', '#dc2626', '#059669', '#d97706', '#7c3aed',
            '#db2777', '#0891b2', '#65a30d', '#9333ea', '#ea580c',
            '#083344', '#14532d', '#7f1d1d', '#4c1d95', '#831843',
            '#0c4a6e', '#365314', '#450a0a', '#312e81', '#4a044e',
            '#1e3a8a', '#064e3b', '#7c2d12', '#4338ca', '#831843',
            '#0e7490', '#4d7c0f', '#6d28d9', '#c2410c', '#0369a1',
            '#15803d', '#6b21a8', '#9a3412', '#0284c7', '#16a34a',
            '#7e22ce', '#c2410c', '#0ea5e9', '#22c55e', '#a855f7',
            '#f97316', '#06b6d4', '#4ade80', '#c084fc', '#fb923c'
        ]
        
        # Obtener colores ya en uso
        existing_colors = [rubro.color for rubro in Rubro.query.all()]
        
        # Encontrar un color que no esté en uso
        available_colors = [c for c in colors if c not in existing_colors]
        
        if available_colors:
            return random.choice(available_colors)
        
        # Si todos los colores están en uso, generar uno aleatorio
        while True:
            color = '#{:06x}'.format(random.randint(0, 0xFFFFFF))
            if color not in existing_colors:
                return color
    
    @staticmethod
    def get_all_rubros(empresa_id=None) -> List[Dict[str, Any]]:
        """
        Obtiene todos los rubros con sus estadísticas
        Args:
            empresa_id: Opcional. ID de la empresa para filtrar
        Returns:
            Lista de diccionarios con datos de rubros
        """
        try:
            query = Rubro.query
            if empresa_id:
                query = query.filter(Rubro.empresa_id == empresa_id)
            rubros = query.all()
            rubros_data = []
            
            for rubro in rubros:
                # Calcular estadísticas del rubro
                total_ingresos = db.session.query(func.sum(Movimiento.monto)).filter(
                    Movimiento.rubro_id == rubro.id,
                    Movimiento.tipo == 'ingreso'
                ).scalar() or 0
                
                total_gastos = db.session.query(func.sum(Movimiento.monto)).filter(
                    Movimiento.rubro_id == rubro.id,
                    Movimiento.tipo == 'gasto'
                ).scalar() or 0
                
                total_movimientos = db.session.query(func.count(Movimiento.id)).filter(
                    Movimiento.rubro_id == rubro.id
                ).scalar() or 0
                
                ganancia = max(0, float(total_ingresos) - float(total_gastos))
                
                rubros_data.append({
                    'id': rubro.id,
                    'nombre': rubro.nombre,
                    'color': rubro.color,
                    'total_ingresos': float(total_ingresos),
                    'total_gastos': float(total_gastos),
                    'ganancia': ganancia,
                    'total_movimientos': total_movimientos,
                    'created_at': rubro.created_at.isoformat() if rubro.created_at else None,
                    'updated_at': rubro.updated_at.isoformat() if rubro.updated_at else None
                })
            
            return rubros_data
            
        except Exception as e:
            current_app.logger.error(f"Error obteniendo rubros: {str(e)}")
            return []
    
    @staticmethod
    def get_rubro_by_id(rubro_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtiene un rubro por su ID
        Args:
            rubro_id: ID del rubro
        Returns:
            Diccionario con datos del rubro o None
        """
        try:
            rubro = Rubro.query.get(rubro_id)
            if not rubro:
                return None
            
            # Calcular estadísticas
            total_ingresos = db.session.query(func.sum(Movimiento.monto)).filter(
                Movimiento.rubro_id == rubro.id,
                Movimiento.tipo == 'ingreso'
            ).scalar() or 0
            
            total_gastos = db.session.query(func.sum(Movimiento.monto)).filter(
                Movimiento.rubro_id == rubro.id,
                Movimiento.tipo == 'gasto'
            ).scalar() or 0
            
            total_movimientos = db.session.query(func.count(Movimiento.id)).filter(
                Movimiento.rubro_id == rubro.id
            ).scalar() or 0
            
            ganancia = max(0, float(total_ingresos) - float(total_gastos))
            
            return {
                'id': rubro.id,
                'nombre': rubro.nombre,
                'color': rubro.color,
                'total_ingresos': float(total_ingresos),
                'total_gastos': float(total_gastos),
                'ganancia': ganancia,
                'total_movimientos': total_movimientos,
                'created_at': rubro.created_at.isoformat() if rubro.created_at else None,
                'updated_at': rubro.updated_at.isoformat() if rubro.updated_at else None
            }
            
        except Exception as e:
            current_app.logger.error(f"Error obteniendo rubro: {str(e)}")
            return None
    
    @staticmethod
    def create_rubro(nombre: str, empresa_id: int = None) -> Optional[Dict[str, Any]]:
        """
        Crea un nuevo rubro con un color automático único
        Args:
            nombre: Nombre del rubro
            empresa_id: ID de la empresa
        Returns:
            Diccionario con datos del rubro creado o None
        """
        try:
            # Verificar si ya existe un rubro con ese nombre en la misma empresa
            query = Rubro.query.filter(Rubro.nombre == nombre)
            if empresa_id:
                query = query.filter(Rubro.empresa_id == empresa_id)
            existing_rubro = query.first()
            if existing_rubro:
                return None
            
            # Generar color único
            color = RubroService._generate_unique_color()
            
            rubro = Rubro(nombre=nombre, color=color, empresa_id=empresa_id)
            db.session.add(rubro)
            db.session.commit()
            
            return rubro.to_dict()
            
        except Exception as e:
            current_app.logger.error(f"Error creando rubro: {str(e)}")
            db.session.rollback()
            return None
    
    @staticmethod
    def update_rubro(rubro_id: int, nombre: str) -> Optional[Dict[str, Any]]:
        """
        Actualiza un rubro existente
        Args:
            rubro_id: ID del rubro
            nombre: Nuevo nombre del rubro
        Returns:
            Diccionario con datos del rubro actualizado o None
        """
        try:
            rubro = Rubro.query.get(rubro_id)
            if not rubro:
                return None
            
            # Verificar si el nombre ya está en uso por otro rubro
            existing_rubro = Rubro.query.filter(
                Rubro.nombre == nombre,
                Rubro.id != rubro_id
            ).first()
            if existing_rubro:
                return None
            
            rubro.nombre = nombre
            db.session.commit()
            
            return rubro.to_dict()
            
        except Exception as e:
            current_app.logger.error(f"Error actualizando rubro: {str(e)}")
            db.session.rollback()
            return None
    
    @staticmethod
    def delete_rubro(rubro_id: int) -> bool:
        """
        Elimina un rubro
        Args:
            rubro_id: ID del rubro
        Returns:
            True si se eliminó correctamente, False en caso contrario
        """
        try:
            rubro = Rubro.query.get(rubro_id)
            if not rubro:
                return False
            
            db.session.delete(rubro)
            db.session.commit()
            
            return True
            
        except Exception as e:
            current_app.logger.error(f"Error eliminando rubro: {str(e)}")
            db.session.rollback()
            return False
