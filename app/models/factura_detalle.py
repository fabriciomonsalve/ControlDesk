from app import db

class FacturaDetalle(db.Model):
    """
    Modelo FacturaDetalle - Representa los detalles de productos en una factura
    """
    __tablename__ = 'facturas_detalle'
    
    id = db.Column(db.Integer, primary_key=True)
    factura_id = db.Column(db.Integer, db.ForeignKey('facturas_compra.id'), nullable=False)
    producto = db.Column(db.String(200), nullable=False)
    cantidad = db.Column(db.Float, default=1.0)
    precio_unitario = db.Column(db.Float, default=0.0)
    total_linea = db.Column(db.Float, default=0.0)
    rubro_id = db.Column(db.Integer, db.ForeignKey('rubros.id'), nullable=True)
    
    def __repr__(self):
        return f'<FacturaDetalle {self.producto}>'
    
    def to_dict(self):
        """Convierte el modelo a diccionario para JSON"""
        return {
            'id': self.id,
            'factura_id': self.factura_id,
            'producto': self.producto,
            'cantidad': self.cantidad,
            'precio_unitario': self.precio_unitario,
            'total_linea': self.total_linea,
            'rubro_id': self.rubro_id
        }
