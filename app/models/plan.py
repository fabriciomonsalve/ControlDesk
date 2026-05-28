from datetime import datetime
from app import db

class Plan(db.Model):
    """
    Modelo Plan - Define los planes de suscripción con sus límites
    Planes: FREE, BASIC, PRO, ENTERPRISE
    """
    __tablename__ = 'planes'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), unique=True, nullable=False)  # FREE, BASIC, PRO, ENTERPRISE
    descripcion = db.Column(db.String(200), nullable=True)
    precio_mensual = db.Column(db.Float, default=0.0)
    activo = db.Column(db.Boolean, default=True)
    
    # Límites funcionales
    max_rubros = db.Column(db.Integer, default=3)  # Límite de rubros
    max_categorias = db.Column(db.Integer, default=10)  # Límite de categorías
    max_usuarios = db.Column(db.Integer, default=1)  # Límite de usuarios
    max_movimientos_mensuales = db.Column(db.Integer, default=100)  # Límite de movimientos mensuales
    acceso_reportes_avanzados = db.Column(db.Boolean, default=False)  # Acceso a reportes avanzados
    acceso_export_pdf = db.Column(db.Boolean, default=False)  # Acceso a exportar PDF
    
    fecha_creacion = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Relaciones
    empresas = db.relationship('Empresa', backref='plan', lazy=True)
    
    def to_dict(self):
        """Convierte el modelo a diccionario"""
        return {
            'id': self.id,
            'nombre': self.nombre,
            'descripcion': self.descripcion,
            'precio_mensual': self.precio_mensual,
            'activo': self.activo,
            'max_rubros': self.max_rubros,
            'max_categorias': self.max_categorias,
            'max_usuarios': self.max_usuarios,
            'max_movimientos_mensuales': self.max_movimientos_mensuales,
            'acceso_reportes_avanzados': self.acceso_reportes_avanzados,
            'acceso_export_pdf': self.acceso_export_pdf,
            'fecha_creacion': self.fecha_creacion.isoformat() if self.fecha_creacion else None
        }
    
    def __repr__(self):
        return f'<Plan {self.nombre}>'
