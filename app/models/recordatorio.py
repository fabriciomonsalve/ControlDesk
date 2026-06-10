from datetime import datetime
from app import db

class Recordatorio(db.Model):
    """Modelo para recordatorios y vencimientos"""
    __tablename__ = 'recordatorios'
    
    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=False)
    
    # Información general
    titulo = db.Column(db.String(200), nullable=False)
    descripcion = db.Column(db.Text, nullable=True)
    tipo = db.Column(db.String(50), nullable=False, default='general')  # pago, tarea, renovacion, mantenimiento, etc.
    prioridad = db.Column(db.String(20), nullable=False, default='media')  # baja, media, alta, critica
    rubro_id = db.Column(db.Integer, db.ForeignKey('rubros.id'), nullable=True)
    
    # Fechas
    fecha_vencimiento = db.Column(db.DateTime, nullable=False)
    fecha_aviso = db.Column(db.DateTime, nullable=True)  # Fecha en que comienza a notificar
    dias_aviso = db.Column(db.Integer, nullable=False, default=3)  # Días antes del vencimiento para avisar
    
    # Monto asociado (opcional)
    monto = db.Column(db.Float, nullable=True)
    
    # Estado
    estado = db.Column(db.String(20), nullable=False, default='pendiente')  # pendiente, proximo, vencido, completado, cancelado
    
    # Recurrencia
    recurrente = db.Column(db.Boolean, default=False)
    frecuencia = db.Column(db.String(20), nullable=True)  # diario, semanal, mensual, trimestral, semestral, anual
    
    # Configuración de sonido
    sonido = db.Column(db.String(100), nullable=True, default='default')
    sonido_activo = db.Column(db.Boolean, default=True)
    
    # Fechas de seguimiento
    fecha_creacion = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    fecha_actualizacion = db.Column(db.DateTime, nullable=True)
    fecha_completado = db.Column(db.DateTime, nullable=True)
    fecha_cancelado = db.Column(db.DateTime, nullable=True)
    
    # Relaciones
    rubro = db.relationship('Rubro', backref='recordatorios')
    historial = db.relationship('HistorialRecordatorio', backref='recordatorio', cascade='all, delete-orphan')
    
    def to_dict(self):
        """Convierte el modelo a diccionario"""
        return {
            'id': self.id,
            'empresa_id': self.empresa_id,
            'titulo': self.titulo,
            'descripcion': self.descripcion,
            'tipo': self.tipo,
            'prioridad': self.prioridad,
            'rubro_id': self.rubro_id,
            'rubro_nombre': self.rubro.nombre if self.rubro else None,
            'fecha_vencimiento': self.fecha_vencimiento.isoformat() if self.fecha_vencimiento else None,
            'fecha_aviso': self.fecha_aviso.isoformat() if self.fecha_aviso else None,
            'dias_aviso': self.dias_aviso,
            'monto': self.monto,
            'estado': self.estado,
            'recurrente': self.recurrente,
            'frecuencia': self.frecuencia,
            'sonido': self.sonido,
            'sonido_activo': self.sonido_activo,
            'fecha_creacion': self.fecha_creacion.isoformat() if self.fecha_creacion else None,
            'fecha_actualizacion': self.fecha_actualizacion.isoformat() if self.fecha_actualizacion else None,
            'fecha_completado': self.fecha_completado.isoformat() if self.fecha_completado else None,
            'fecha_cancelado': self.fecha_cancelado.isoformat() if self.fecha_cancelado else None
        }
    
    def __repr__(self):
        return f'<Recordatorio {self.titulo} - {self.estado}>'
