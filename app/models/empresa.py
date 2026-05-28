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
    
    # Campos adicionales para información de contacto
    rut_empresa = db.Column(db.String(20), nullable=True)
    correo = db.Column(db.String(120), nullable=True)
    telefono = db.Column(db.String(20), nullable=True)
    direccion = db.Column(db.String(200), nullable=True)
    ultimo_acceso = db.Column(db.DateTime, nullable=True)
    
    # Campos para sistema de planes
    plan_id = db.Column(db.Integer, db.ForeignKey('planes.id'), nullable=True)
    fecha_inicio_plan = db.Column(db.DateTime, nullable=True)
    fecha_expiracion_plan = db.Column(db.DateTime, nullable=True)
    
    # Relaciones
    rubros = db.relationship('Rubro', backref='empresa', lazy=True, cascade='all, delete-orphan')
    movimientos = db.relationship('Movimiento', backref='empresa', lazy=True, cascade='all, delete-orphan')
    categorias = db.relationship('Categoria', backref='empresa', lazy=True, cascade='all, delete-orphan')
    users = db.relationship('User', backref='empresa', lazy=True)
    
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
            'rut_empresa': self.rut_empresa,
            'correo': self.correo,
            'telefono': self.telefono,
            'direccion': self.direccion,
            'fecha_creacion': self.fecha_creacion.isoformat() if self.fecha_creacion else None,
            'ultimo_acceso': self.ultimo_acceso.isoformat() if self.ultimo_acceso else None,
            'plan_id': self.plan_id,
            'fecha_inicio_plan': self.fecha_inicio_plan.isoformat() if self.fecha_inicio_plan else None,
            'fecha_expiracion_plan': self.fecha_expiracion_plan.isoformat() if self.fecha_expiracion_plan else None,
            'plan': self.plan.to_dict() if self.plan else None
        }
    
    def is_plan_expired(self):
        """Verifica si el plan de la empresa ha expirado"""
        if not self.fecha_expiracion_plan:
            return False
        return datetime.utcnow() > self.fecha_expiracion_plan
    
    def __repr__(self):
        return f'<Empresa {self.nombre}>'
