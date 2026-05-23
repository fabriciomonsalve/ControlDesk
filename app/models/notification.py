from app import db
from datetime import datetime
import json


class Notification(db.Model):
    """Modelo para notificaciones inteligentes del sistema"""
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(20), default='info', nullable=False)  # success, warning, error, info
    priority = db.Column(db.String(20), default='medium', nullable=False)  # low, medium, high, critical
    category = db.Column(db.String(50), default='system', nullable=False)  # system, financial, sales, inventory, user, report
    user_id = db.Column(db.Integer, nullable=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=False)
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    is_automatic = db.Column(db.Boolean, default=False, nullable=False)  # Si fue generada automáticamente
    insight_type = db.Column(db.String(100), nullable=True)  # Tipo de insight: daily_summary, profit_alert, rubro_analysis, etc.
    
    # Campos adicionales
    action_url = db.Column(db.String(500), nullable=True)  # URL para acción al hacer click
    module = db.Column(db.String(50), nullable=True)  # Módulo del sistema: ventas, reportes, configuracion
    icon = db.Column(db.String(50), nullable=True)  # Icono personalizado (Font Awesome)
    
    # Metadata JSON para información adicional (montos, porcentajes, referencias)
    meta_data = db.Column(db.JSON, nullable=True)
    
    # Referencias analíticas
    analytics_reference = db.Column(db.String(100), nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    read_at = db.Column(db.DateTime, nullable=True)
    
    # Relaciones
    empresa = db.relationship('Empresa', backref='notifications')
    
    def to_dict(self):
        """Convierte el modelo a diccionario"""
        return {
            'id': self.id,
            'title': self.title,
            'message': self.message,
            'type': self.type,
            'priority': self.priority,
            'category': self.category,
            'user_id': self.user_id,
            'empresa_id': self.empresa_id,
            'is_read': self.is_read,
            'is_automatic': self.is_automatic,
            'insight_type': self.insight_type,
            'action_url': self.action_url,
            'module': self.module,
            'icon': self.icon,
            'metadata': self.meta_data,
            'analytics_reference': self.analytics_reference,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'read_at': self.read_at.isoformat() if self.read_at else None
        }
    
    def mark_as_read(self):
        """Marca la notificación como leída"""
        self.is_read = True
        self.read_at = datetime.utcnow()
        db.session.commit()
    
    def delete_notification(self):
        """Elimina la notificación"""
        db.session.delete(self)
        db.session.commit()
    
    @staticmethod
    def get_unread_count(user_id: int = None, empresa_id: int = None) -> int:
        """Obtiene el conteo de notificaciones no leídas"""
        query = Notification.query.filter_by(is_read=False)
        
        if user_id:
            query = query.filter_by(user_id=user_id)
        
        if empresa_id:
            query = query.filter_by(empresa_id=empresa_id)
        
        return query.count()
    
    @staticmethod
    def get_notifications(empresa_id: int, user_id: int = None, limit: int = 50, 
                          unread_only: bool = False, read_only: bool = False,
                          type_filter: str = None, priority_filter: str = None,
                          offset: int = 0, search_query: str = None) -> dict:
        """
        Obtiene notificaciones con filtros y paginación
        
        Args:
            empresa_id: ID de la empresa
            user_id: ID del usuario (opcional)
            limit: Límite de registros
            unread_only: Si solo retornar no leídas
            read_only: Si solo retornar leídas
            type_filter: Filtro por tipo
            priority_filter: Filtro por prioridad
            offset: Offset para paginación
            search_query: Búsqueda en título y mensaje
            
        Returns:
            Diccionario con notificaciones y metadatos
        """
        query = Notification.query.filter_by(empresa_id=empresa_id)
        
        if user_id:
            query = query.filter_by(user_id=user_id)
        
        if unread_only:
            query = query.filter_by(is_read=False)
        
        if read_only:
            query = query.filter_by(is_read=True)
        
        if type_filter:
            query = query.filter_by(type=type_filter)
        
        if priority_filter:
            query = query.filter_by(priority=priority_filter)
        
        if search_query:
            search_pattern = f'%{search_query}%'
            query = query.filter(
                db.or_(
                    Notification.title.ilike(search_pattern),
                    Notification.message.ilike(search_pattern)
                )
            )
        
        # Ordenar por prioridad y fecha
        query = query.order_by(
            db.case(
                (Notification.priority == 'critical', 1),
                (Notification.priority == 'high', 2),
                (Notification.priority == 'medium', 3),
                (Notification.priority == 'low', 4),
                else_=5
            ),
            Notification.created_at.desc()
        )
        
        total = query.count()
        notifications = query.limit(limit).offset(offset).all()
        
        return {
            'notifications': [notif.to_dict() for notif in notifications],
            'total': total,
            'unread_count': Notification.get_unread_count(user_id, empresa_id)
        }
    
    @staticmethod
    def create_notification(empresa_id: int, title: str, message: str, 
                          type: str = 'info', priority: str = 'medium',
                          category: str = 'system', user_id: int = None,
                          is_automatic: bool = False, insight_type: str = None,
                          action_url: str = None, module: str = None,
                          icon: str = None, meta_data: dict = None,
                          analytics_reference: str = None) -> 'Notification':
        """
        Crea una nueva notificación
        
        Args:
            empresa_id: ID de la empresa
            title: Título de la notificación
            message: Mensaje de la notificación
            type: Tipo (success, warning, error, info)
            priority: Prioridad (low, medium, high, critical)
            category: Categoría (system, financial, sales, inventory, user, report)
            user_id: ID del usuario
            is_automatic: Si fue generada automáticamente
            insight_type: Tipo de insight
            action_url: URL para acción
            module: Módulo del sistema
            icon: Icono personalizado
            meta_data: Diccionario con metadatos adicionales
            analytics_reference: Referencia analítica
            
        Returns:
            Instancia de Notification creada
        """
        notification = Notification(
            title=title,
            message=message,
            type=type,
            priority=priority,
            category=category,
            user_id=user_id,
            empresa_id=empresa_id,
            is_automatic=is_automatic,
            insight_type=insight_type,
            action_url=action_url,
            module=module,
            icon=icon,
            meta_data=meta_data,
            analytics_reference=analytics_reference
        )
        
        db.session.add(notification)
        db.session.commit()
        
        return notification
    
    @staticmethod
    def mark_all_as_read(empresa_id: int, user_id: int = None) -> int:
        """Marca todas las notificaciones como leídas"""
        query = Notification.query.filter_by(empresa_id=empresa_id, is_read=False)
        
        if user_id:
            query = query.filter_by(user_id=user_id)
        
        count = query.count()
        
        for notification in query.all():
            notification.mark_as_read()
        
        return count
    
    def __repr__(self):
        return f'<Notification {self.title} - {self.type} - {self.priority}>'
