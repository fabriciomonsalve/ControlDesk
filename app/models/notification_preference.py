from app import db
from datetime import datetime

class NotificationPreference(db.Model):
    """
    Modelo NotificationPreference - Almacena preferencias de notificaciones y seguridad por empresa
    """
    __tablename__ = 'notification_preferences'
    
    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=False)
    
    # Preferencias de notificaciones
    notif_ventas = db.Column(db.Boolean, default=True)  # Notificaciones de ventas
    notif_gastos = db.Column(db.Boolean, default=True)  # Notificaciones de gastos
    notif_financieras = db.Column(db.Boolean, default=True)  # Notificaciones financieras
    notif_resumen = db.Column(db.Boolean, default=False)  # Notificaciones de resumen
    
    # Preferencias de seguridad
    duracion_sesion = db.Column(db.Integer, default=30)  # Duración de sesión en minutos (30, 60, 120, 240)
    auto_logout = db.Column(db.Boolean, default=False)  # Auto-logout después de inactividad
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """Convierte el modelo a diccionario"""
        return {
            'id': self.id,
            'empresa_id': self.empresa_id,
            'notif_ventas': self.notif_ventas,
            'notif_gastos': self.notif_gastos,
            'notif_financieras': self.notif_financieras,
            'notif_resumen': self.notif_resumen,
            'duracion_sesion': self.duracion_sesion,
            'auto_logout': self.auto_logout,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<NotificationPreference empresa_id={self.empresa_id}>'
