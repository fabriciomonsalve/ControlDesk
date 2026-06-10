from app import db
from datetime import datetime

class FacturaCompra(db.Model):
    """
    Modelo FacturaCompra - Representa facturas de compra
    """
    __tablename__ = 'facturas_compra'
    
    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=True)
    proveedor = db.Column(db.String(200), nullable=False)
    numero_factura = db.Column(db.String(100), nullable=False)
    fecha_factura = db.Column(db.Date, nullable=False)
    subtotal = db.Column(db.Float, default=0.0)
    iva = db.Column(db.Float, default=0.0)
    total = db.Column(db.Float, default=0.0)
    archivo_original = db.Column(db.String(500), nullable=True)
    tipo_archivo = db.Column(db.String(50), nullable=True)
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaciones
    detalles = db.relationship('FacturaDetalle', backref='factura', lazy=True, cascade='all, delete-orphan')
    rubros_distribucion = db.relationship('FacturaRubro', backref='factura', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<FacturaCompra {self.numero_factura}>'
    
    def to_dict(self):
        """Convierte el modelo a diccionario para JSON"""
        return {
            'id': self.id,
            'empresa_id': self.empresa_id,
            'proveedor': self.proveedor,
            'numero_factura': self.numero_factura,
            'fecha_factura': self.fecha_factura.isoformat() if self.fecha_factura else None,
            'subtotal': self.subtotal,
            'iva': self.iva,
            'total': self.total,
            'archivo_original': self.archivo_original,
            'tipo_archivo': self.tipo_archivo,
            'fecha_registro': self.fecha_registro.isoformat() if self.fecha_registro else None
        }
