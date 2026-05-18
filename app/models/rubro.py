from app import db
from datetime import datetime

class Rubro(db.Model):
    """
    Modelo Rubro - Representa las categorías principales de negocio
    Ejemplos: Ferretería, Apicultura, Agricultura
    """
    __tablename__ = 'rubros'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    color = db.Column(db.String(7), nullable=False, default='#2563eb')
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relación: Un rubro tiene muchos movimientos
    movimientos = db.relationship('Movimiento', backref='rubro', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Rubro {self.nombre}>'
    
    def to_dict(self):
        """Convierte el modelo a diccionario para JSON"""
        return {
            'id': self.id,
            'nombre': self.nombre,
            'color': self.color,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
