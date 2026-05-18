from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from app import db

class Empresa(db.Model):
    """
    Modelo Empresa - Representa una empresa PYME en el sistema
    """
    __tablename__ = 'empresas'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False, unique=True)
    pin_hash = db.Column(db.String(255), nullable=False)
    estado = db.Column(db.String(20), nullable=False, default='activa')
    fecha_creacion = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Relaciones
    rubros = db.relationship('Rubro', backref='empresa', lazy=True, cascade='all, delete-orphan')
    movimientos = db.relationship('Movimiento', backref='empresa', lazy=True, cascade='all, delete-orphan')
    categorias = db.relationship('Categoria', backref='empresa', lazy=True, cascade='all, delete-orphan')
    
    def set_pin(self, pin):
        """Establece el PIN de forma segura con hash"""
        self.pin_hash = generate_password_hash(str(pin))
    
    def verify_pin(self, pin):
        """Verifica si el PIN es correcto"""
        return check_password_hash(self.pin_hash, str(pin))
    
    def to_dict(self):
        """Convierte el modelo a diccionario"""
        return {
            'id': self.id,
            'nombre': self.nombre,
            'estado': self.estado,
            'fecha_creacion': self.fecha_creacion.isoformat() if self.fecha_creacion else None
        }
    
    def __repr__(self):
        return f'<Empresa {self.nombre}>'
