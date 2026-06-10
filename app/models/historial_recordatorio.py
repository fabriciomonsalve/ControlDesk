from datetime import datetime
from app import db

class HistorialRecordatorio(db.Model):
    """Modelo para historial de cambios en recordatorios"""
    __tablename__ = 'historial_recordatorios'
    
    id = db.Column(db.Integer, primary_key=True)
    recordatorio_id = db.Column(db.Integer, db.ForeignKey('recordatorios.id'), nullable=False)
    
    accion = db.Column(db.String(50), nullable=False)  # creado, actualizado, completado, cancelado, reabierto, recurrente_generado
    usuario = db.Column(db.String(100), nullable=True)  # Nombre o email del usuario
    fecha = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    observacion = db.Column(db.Text, nullable=True)
    
    # Datos de snapshot (opcional, para guardar estado anterior)
    estado_anterior = db.Column(db.String(20), nullable=True)
    estado_nuevo = db.Column(db.String(20), nullable=True)
    
    def to_dict(self):
        """Convierte el modelo a diccionario"""
        return {
            'id': self.id,
            'recordatorio_id': self.recordatorio_id,
            'accion': self.accion,
            'usuario': self.usuario,
            'fecha': self.fecha.isoformat() if self.fecha else None,
            'observacion': self.observacion,
            'estado_anterior': self.estado_anterior,
            'estado_nuevo': self.estado_nuevo
        }
    
    def __repr__(self):
        return f'<HistorialRecordatorio {self.recordatorio_id} - {self.accion}>'
