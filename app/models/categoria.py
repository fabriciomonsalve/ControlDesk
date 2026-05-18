from app import db
from datetime import datetime

class Categoria(db.Model):
    """
    Modelo Categoria - Representa las categorías de movimientos
    Ejemplos: Compras, Ventas, Servicios, Insumos, etc.
    """
    __tablename__ = 'categorias'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relación: Una categoría tiene muchos movimientos
    movimientos = db.relationship('Movimiento', backref='categoria', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Categoria {self.nombre}>'
    
    def to_dict(self):
        """Convierte el modelo a diccionario para JSON"""
        return {
            'id': self.id,
            'nombre': self.nombre,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
