from app import db
from datetime import datetime


class CortePOS(db.Model):
    """Modelo para almacenar los cortes del sistema POS Abarrotes"""
    __tablename__ = 'cortes_pos'
    
    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=False)
    fecha = db.Column(db.Date, nullable=False)
    ventas_totales = db.Column(db.Numeric(12, 2), nullable=False)
    costos_totales = db.Column(db.Numeric(12, 2), nullable=False)
    ganancias_totales = db.Column(db.Numeric(12, 2), nullable=False)
    archivo_original = db.Column(db.String(255), nullable=False)
    fecha_importacion = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relación con detalles del corte
    detalles = db.relationship('DetalleCortePOS', backref='corte', lazy=True, cascade='all, delete-orphan')
    
    # Timestamps
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def to_dict(self):
        """Convierte el modelo a diccionario"""
        return {
            'id': self.id,
            'empresa_id': self.empresa_id,
            'fecha': self.fecha.isoformat() if self.fecha else None,
            'ventas_totales': float(self.ventas_totales),
            'costos_totales': float(self.costos_totales),
            'ganancias_totales': float(self.ganancias_totales),
            'archivo_original': self.archivo_original,
            'fecha_importacion': self.fecha_importacion.isoformat() if self.fecha_importacion else None,
            'fecha_creacion': self.fecha_creacion.isoformat() if self.fecha_creacion else None,
            'fecha_actualizacion': self.fecha_actualizacion.isoformat() if self.fecha_actualizacion else None
        }
    
    def __repr__(self):
        return f'<CortePOS {self.fecha} - Ventas: ${self.ventas_totales}>'


class DetalleCortePOS(db.Model):
    """Modelo para almacenar los detalles de cada corte POS"""
    __tablename__ = 'detalle_corte_pos'
    
    id = db.Column(db.Integer, primary_key=True)
    corte_id = db.Column(db.Integer, db.ForeignKey('cortes_pos.id'), nullable=False)
    producto = db.Column(db.String(255), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    precio_venta = db.Column(db.Numeric(10, 2), nullable=False)
    precio_costo = db.Column(db.Numeric(10, 2), nullable=False)
    ganancia = db.Column(db.Numeric(10, 2), nullable=False)
    departamento = db.Column(db.String(100), nullable=True)
    
    # Timestamps
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def to_dict(self):
        """Convierte el modelo a diccionario"""
        return {
            'id': self.id,
            'corte_id': self.corte_id,
            'producto': self.producto,
            'cantidad': self.cantidad,
            'precio_venta': float(self.precio_venta),
            'precio_costo': float(self.precio_costo),
            'ganancia': float(self.ganancia),
            'departamento': self.departamento,
            'fecha_creacion': self.fecha_creacion.isoformat() if self.fecha_creacion else None
        }
    
    def __repr__(self):
        return f'<DetalleCortePOS {self.producto} - Cantidad: {self.cantidad}>'
