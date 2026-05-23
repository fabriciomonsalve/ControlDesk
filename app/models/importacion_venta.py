from app import db
from datetime import datetime


class ImportacionVenta(db.Model):
    """Modelo para el historial de importaciones de ventas"""
    __tablename__ = 'importaciones_ventas'
    
    id = db.Column(db.Integer, primary_key=True)
    archivo = db.Column(db.String(255), nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    registros_importados = db.Column(db.Integer, default=0, nullable=False)
    errores = db.Column(db.Integer, default=0, nullable=False)
    duplicados = db.Column(db.Integer, default=0, nullable=False)
    usuario = db.Column(db.String(100), nullable=False)
    estado = db.Column(db.String(50), default='completado', nullable=False)
    errores_detalle = db.Column(db.Text, nullable=True)
    
    # Campos para multi-tenancy
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=False)
    empresa = db.relationship('Empresa', backref='importaciones_ventas')
    
    # Timestamps
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def to_dict(self):
        """Convierte el modelo a diccionario"""
        return {
            'id': self.id,
            'archivo': self.archivo,
            'fecha': self.fecha.isoformat() if self.fecha else None,
            'registros_importados': self.registros_importados,
            'errores': self.errores,
            'duplicados': self.duplicados,
            'usuario': self.usuario,
            'estado': self.estado,
            'errores_detalle': self.errores_detalle,
            'empresa_id': self.empresa_id,
            'fecha_creacion': self.fecha_creacion.isoformat() if self.fecha_creacion else None,
            'fecha_actualizacion': self.fecha_actualizacion.isoformat() if self.fecha_actualizacion else None
        }
    
    def __repr__(self):
        return f'<ImportacionVenta {self.archivo} - {self.fecha}>'
