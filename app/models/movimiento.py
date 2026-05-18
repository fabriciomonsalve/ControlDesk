from app import db
from datetime import datetime

class Movimiento(db.Model):
    """
    Modelo Movimiento - Representa las transacciones financieras
    Puede ser de tipo 'gasto' o 'ingreso'
    """
    __tablename__ = 'movimientos'
    
    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(10), nullable=False)  # 'gasto' o 'ingreso'
    monto = db.Column(db.Numeric(10, 2), nullable=False)  # Decimal con 2 decimales
    fecha = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    descripcion = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Claves foráneas
    rubro_id = db.Column(db.Integer, db.ForeignKey('rubros.id'), nullable=False)
    categoria_id = db.Column(db.Integer, db.ForeignKey('categorias.id'), nullable=False)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=True)
    
    def __repr__(self):
        return f'<Movimiento {self.tipo}: ${self.monto} - {self.descripcion}>'
    
    def to_dict(self):
        """Convierte el modelo a diccionario para JSON"""
        return {
            'id': self.id,
            'tipo': self.tipo,
            'monto': float(self.monto),
            'fecha': self.fecha.isoformat() if self.fecha else None,
            'descripcion': self.descripcion,
            'rubro_id': self.rubro_id,
            'categoria_id': self.categoria_id,
            'rubro_nombre': self.rubro.nombre if self.rubro else None,
            'categoria_nombre': self.categoria.nombre if self.categoria else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @staticmethod
    def validate_tipo(tipo):
        """Valida que el tipo sea 'gasto' o 'ingreso'"""
        return tipo.lower() in ['gasto', 'ingreso']
    
    def set_tipo(self, tipo):
        """Establece el tipo validando el valor"""
        if self.validate_tipo(tipo):
            self.tipo = tipo.lower()
        else:
            raise ValueError("El tipo debe ser 'gasto' o 'ingreso'")
