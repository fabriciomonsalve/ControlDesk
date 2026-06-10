from app import db
from datetime import datetime


class GananciaRubro(db.Model):
    """Modelo para almacenar las ganancias acumuladas por rubro"""
    __tablename__ = 'ganancias_rubro'
    
    id = db.Column(db.Integer, primary_key=True)
    rubro_id = db.Column(db.Integer, db.ForeignKey('rubros.id'), nullable=False)
    fecha = db.Column(db.Date, nullable=False)
    ventas = db.Column(db.Numeric(12, 2), nullable=False)
    costos = db.Column(db.Numeric(12, 2), nullable=False)
    ganancias = db.Column(db.Numeric(12, 2), nullable=False)
    origen = db.Column(db.String(50), nullable=False, default='Abarrotes POS')
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=False)
    
    # Timestamps
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def to_dict(self):
        """Convierte el modelo a diccionario"""
        return {
            'id': self.id,
            'rubro_id': self.rubro_id,
            'fecha': self.fecha.isoformat() if self.fecha else None,
            'ventas': float(self.ventas),
            'costos': float(self.costos),
            'ganancias': float(self.ganancias),
            'origen': self.origen,
            'empresa_id': self.empresa_id,
            'fecha_creacion': self.fecha_creacion.isoformat() if self.fecha_creacion else None,
            'fecha_actualizacion': self.fecha_actualizacion.isoformat() if self.fecha_actualizacion else None
        }
    
    def __repr__(self):
        return f'<GananciaRubro {self.fecha} - Ganancia: ${self.ganancias}>'
