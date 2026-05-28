from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from app import db

class User(db.Model):
    """
    Modelo User - Sistema de roles para administración global
    Roles: ADMIN (administrador de la plataforma), EMPRESA (usuario normal)
    """
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='EMPRESA')  # ADMIN o EMPRESA
    nombre = db.Column(db.String(100), nullable=True)
    activo = db.Column(db.Boolean, default=True)
    fecha_creacion = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    ultimo_acceso = db.Column(db.DateTime, nullable=True)
    
    # Relación con empresa (para usuarios de tipo EMPRESA)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=True)
    
    def set_password(self, password):
        """Establece la contraseña de forma segura con hash"""
        self.password_hash = generate_password_hash(str(password))
    
    def verify_password(self, password):
        """Verifica si la contraseña es correcta"""
        return check_password_hash(self.password_hash, str(password))
    
    def is_admin(self):
        """Verifica si el usuario es administrador"""
        return self.role == 'ADMIN'
    
    def is_empresa(self):
        """Verifica si el usuario es de tipo empresa"""
        return self.role == 'EMPRESA'
    
    def to_dict(self):
        """Convierte el modelo a diccionario"""
        return {
            'id': self.id,
            'email': self.email,
            'role': self.role,
            'nombre': self.nombre,
            'activo': self.activo,
            'fecha_creacion': self.fecha_creacion.isoformat() if self.fecha_creacion else None,
            'ultimo_acceso': self.ultimo_acceso.isoformat() if self.ultimo_acceso else None,
            'empresa_id': self.empresa_id
        }
    
    def __repr__(self):
        return f'<User {self.email} - {self.role}>'
