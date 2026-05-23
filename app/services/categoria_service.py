from app.models.categoria import Categoria
from app import db
from typing import List, Dict, Optional

class CategoriaService:
    """Servicio para gestionar categorías"""
    
    @staticmethod
    def get_all_categorias(empresa_id: Optional[int] = None) -> List[Categoria]:
        """
        Obtiene todas las categorías, opcionalmente filtradas por empresa
        Args:
            empresa_id: ID de la empresa para filtrar (opcional)
        Returns:
            Lista de categorías
        """
        query = Categoria.query
        if empresa_id:
            query = query.filter_by(empresa_id=empresa_id)
        return query.order_by(Categoria.nombre).all()
    
    @staticmethod
    def get_categorias_activas(empresa_id: Optional[int] = None) -> List[Categoria]:
        """
        Obtiene solo las categorías activas
        Args:
            empresa_id: ID de la empresa para filtrar (opcional)
        Returns:
            Lista de categorías activas
        """
        query = Categoria.query.filter_by(estado='activa')
        if empresa_id:
            query = query.filter_by(empresa_id=empresa_id)
        return query.order_by(Categoria.nombre).all()
    
    @staticmethod
    def get_categoria_by_id(categoria_id: int) -> Optional[Categoria]:
        """
        Obtiene una categoría por su ID
        Args:
            categoria_id: ID de la categoría
        Returns:
            Categoría o None si no existe
        """
        return Categoria.query.get(categoria_id)
    
    @staticmethod
    def create_categoria(nombre: str, descripcion: str = None, estado: str = 'activa',
                        icono: str = None, color: str = None, empresa_id: int = None) -> Dict:
        """
        Crea una nueva categoría
        Args:
            nombre: Nombre de la categoría
            descripcion: Descripción de la categoría
            estado: Estado de la categoría (activa/inactiva)
            icono: Icono de FontAwesome
            color: Color en formato hex
            empresa_id: ID de la empresa
        Returns:
            Dict con success, categoria o error
        """
        try:
            # Verificar si ya existe una categoría con el mismo nombre
            existing = Categoria.query.filter_by(nombre=nombre).first()
            if existing:
                return {
                    'success': False,
                    'error': f'Ya existe una categoría con el nombre "{nombre}"'
                }
            
            categoria = Categoria(
                nombre=nombre,
                descripcion=descripcion,
                estado=estado,
                icono=icono,
                color=color,
                empresa_id=empresa_id
            )
            
            db.session.add(categoria)
            db.session.commit()
            
            return {
                'success': True,
                'categoria': categoria.to_dict()
            }
            
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'error': f'Error al crear categoría: {str(e)}'
            }
    
    @staticmethod
    def update_categoria(categoria_id: int, nombre: str = None, descripcion: str = None,
                        estado: str = None, icono: str = None, color: str = None) -> Dict:
        """
        Actualiza una categoría existente
        Args:
            categoria_id: ID de la categoría
            nombre: Nuevo nombre
            descripcion: Nueva descripción
            estado: Nuevo estado
            icono: Nuevo icono
            color: Nuevo color
        Returns:
            Dict con success, categoria o error
        """
        try:
            categoria = Categoria.query.get(categoria_id)
            
            if not categoria:
                return {
                    'success': False,
                    'error': 'Categoría no encontrada'
                }
            
            # Verificar si tiene movimientos asociados - no permitir editar si tiene
            movimientos_count = categoria.get_movimientos_count()
            if movimientos_count > 0:
                return {
                    'success': False,
                    'error': f'No se puede editar la categoría porque tiene {movimientos_count} movimientos asociados. Solo se pueden editar categorías sin movimientos.'
                }
            
            # Verificar si el nuevo nombre ya existe en otra categoría
            if nombre and nombre != categoria.nombre:
                existing = Categoria.query.filter_by(nombre=nombre).first()
                if existing:
                    return {
                        'success': False,
                        'error': f'Ya existe una categoría con el nombre "{nombre}"'
                    }
                categoria.nombre = nombre
            
            if descripcion is not None:
                categoria.descripcion = descripcion
            
            if estado is not None:
                categoria.estado = estado
            
            if icono is not None:
                categoria.icono = icono
            
            if color is not None:
                categoria.color = color
            
            db.session.commit()
            
            return {
                'success': True,
                'categoria': categoria.to_dict()
            }
            
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'error': f'Error al actualizar categoría: {str(e)}'
            }
    
    @staticmethod
    def delete_categoria(categoria_id: int) -> Dict:
        """
        Elimina una categoría
        Args:
            categoria_id: ID de la categoría
        Returns:
            Dict con success o error
        """
        try:
            categoria = Categoria.query.get(categoria_id)
            
            if not categoria:
                return {
                    'success': False,
                    'error': 'Categoría no encontrada'
                }
            
            # Verificar si tiene movimientos asociados
            movimientos_count = categoria.get_movimientos_count()
            if movimientos_count > 0:
                return {
                    'success': False,
                    'error': f'No se puede eliminar la categoría porque tiene {movimientos_count} movimientos asociados'
                }
            
            db.session.delete(categoria)
            db.session.commit()
            
            return {
                'success': True,
                'message': 'Categoría eliminada exitosamente'
            }
            
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'error': f'Error al eliminar categoría: {str(e)}'
            }
    
    @staticmethod
    def get_dashboard_metrics(empresa_id: Optional[int] = None) -> Dict:
        """
        Obtiene métricas del dashboard de categorías
        Args:
            empresa_id: ID de la empresa para filtrar (opcional)
        Returns:
            Dict con métricas
        """
        query = Categoria.query
        if empresa_id:
            query = query.filter_by(empresa_id=empresa_id)
        
        categorias = query.all()
        
        total = len(categorias)
        activas = sum(1 for c in categorias if c.estado == 'activa')
        inactivas = sum(1 for c in categorias if c.estado == 'inactiva')
        
        # Encontrar la categoría más utilizada
        categoria_mas_usada = None
        max_usos = 0
        for cat in categorias:
            usos = cat.get_movimientos_count()
            if usos > max_usos:
                max_usos = usos
                categoria_mas_usada = cat
        
        return {
            'total': total,
            'activas': activas,
            'inactivas': inactivas,
            'categoria_mas_usada': categoria_mas_usada.to_dict() if categoria_mas_usada else None
        }
    
    @staticmethod
    def search_categorias(search_term: str, empresa_id: Optional[int] = None) -> List[Categoria]:
        """
        Busca categorías por nombre o descripción
        Args:
            search_term: Término de búsqueda
            empresa_id: ID de la empresa para filtrar (opcional)
        Returns:
            Lista de categorías que coinciden
        """
        query = Categoria.query.filter(
            db.or_(
                Categoria.nombre.ilike(f'%{search_term}%'),
                Categoria.descripcion.ilike(f'%{search_term}%')
            )
        )
        
        if empresa_id:
            query = query.filter_by(empresa_id=empresa_id)
        
        return query.order_by(Categoria.nombre).all()
    
    @staticmethod
    def get_categorias_for_select(empresa_id: Optional[int] = None) -> List[Dict]:
        """
        Obtiene categorías para select dropdown
        Args:
            empresa_id: ID de la empresa para filtrar (opcional)
        Returns:
            Lista de diccionarios con id y nombre
        """
        categorias = CategoriaService.get_categorias_activas(empresa_id)
        return [{'id': c.id, 'nombre': c.nombre} for c in categorias]
