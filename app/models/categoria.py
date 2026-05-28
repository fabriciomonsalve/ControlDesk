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
    descripcion = db.Column(db.Text, nullable=True)
    estado = db.Column(db.String(20), nullable=False, default='activa')  # activa/inactiva
    icono = db.Column(db.String(50), nullable=True)  # FontAwesome icon class
    color = db.Column(db.String(7), nullable=True)  # Hex color code
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=True)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relación: Una categoría tiene muchos movimientos
    movimientos = db.relationship('Movimiento', backref='categoria', lazy=True, cascade='all, delete-orphan')
    
    def get_movimientos_count(self):
        """Obtiene la cantidad de movimientos asociados"""
        return len(self.movimientos)
    
    def __repr__(self):
        return f'<Categoria {self.nombre}>'
    
    def to_dict(self):
        """Convierte el modelo a diccionario para JSON"""
        return {
            'id': self.id,
            'nombre': self.nombre,
            'descripcion': self.descripcion,
            'estado': self.estado,
            'icono': self.icono,
            'color': self.color,
            'empresa_id': self.empresa_id,
            'fecha_creacion': self.fecha_creacion.isoformat() if self.fecha_creacion else None,
            'fecha_actualizacion': self.fecha_actualizacion.isoformat() if self.fecha_actualizacion else None,
            'movimientos_count': self.get_movimientos_count()
        }
