from app import db

class FacturaRubro(db.Model):
    """
    Modelo FacturaRubro - Representa la distribución de gastos por rubro en una factura
    """
    __tablename__ = 'facturas_rubro'
    
    id = db.Column(db.Integer, primary_key=True)
    factura_id = db.Column(db.Integer, db.ForeignKey('facturas_compra.id'), nullable=False)
    rubro_id = db.Column(db.Integer, db.ForeignKey('rubros.id'), nullable=False)
    monto_total = db.Column(db.Float, default=0.0)
    
    def __repr__(self):
        return f'<FacturaRubro Factura:{self.factura_id} Rubro:{self.rubro_id}>'
    
    def to_dict(self):
        """Convierte el modelo a diccionario para JSON"""
        return {
            'id': self.id,
            'factura_id': self.factura_id,
            'rubro_id': self.rubro_id,
            'monto_total': self.monto_total
        }
