from datetime import datetime, timedelta
from sqlalchemy import func, and_
from app.models.empresa import Empresa
from app.models.plan import Plan
from app.models.rubro import Rubro
from app.models.categoria import Categoria
from app.models.movimiento import Movimiento
from app.models.user import User
from app import db

class AdminService:
    """Servicio para lógica de administración global"""
    
    @staticmethod
    def get_dashboard_metrics():
        """
        Retorna métricas globales para el dashboard admin
        """
        # Total empresas
        total_empresas = Empresa.query.count()
        
        # Empresas activas
        empresas_activas = Empresa.query.filter_by(estado='activa').count()
        
        # Total usuarios
        total_usuarios = User.query.count()
        
        # Total movimientos
        total_movimientos = Movimiento.query.count()
        
        # Empresas inactivas
        empresas_inactivas = Empresa.query.filter_by(estado='inactiva').count()
        
        # Empresas con plan expirado
        empresas_expiradas = 0
        empresas = Empresa.query.all()
        for empresa in empresas:
            if empresa.is_plan_expired():
                empresas_expiradas += 1
        
        # Planes activos
        planes_activos = Plan.query.filter_by(activo=True).count()
        
        # Rubros y categorías totales
        total_rubros = Rubro.query.count()
        total_categorias = Categoria.query.count()
        
        # Empresas creadas este mes
        inicio_mes = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        empresas_este_mes = Empresa.query.filter(Empresa.fecha_creacion >= inicio_mes).count()
        
        # Empresas creadas esta semana
        inicio_semana = datetime.utcnow() - timedelta(days=datetime.utcnow().weekday())
        empresas_esta_semana = Empresa.query.filter(Empresa.fecha_creacion >= inicio_semana).count()
        
        # Distribución por plan
        planes_uso = db.session.query(
            Plan.nombre,
            func.count(Empresa.id).label('count')
        ).outerjoin(
            Empresa, Plan.id == Empresa.plan_id
        ).group_by(Plan.nombre).all()
        
        distribucion_planes = [
            {
                'plan_nombre': plan_nombre,
                'cantidad': count
            }
            for plan_nombre, count in planes_uso
        ]
        
        # Empresas recientes (últimos 7 días) como diccionarios
        fecha_7_dias = datetime.utcnow() - timedelta(days=7)
        empresas_recientes_objs = Empresa.query.filter(
            Empresa.fecha_creacion >= fecha_7_dias
        ).order_by(Empresa.fecha_creacion.desc()).limit(5).all()
        
        empresas_recientes = [
            {
                'id': emp.id,
                'nombre': emp.nombre,
                'correo': emp.correo,
                'estado': emp.estado
            }
            for emp in empresas_recientes_objs
        ]
        
        return {
            'total_empresas': total_empresas,
            'empresas_activas': empresas_activas,
            'empresas_inactivas': empresas_inactivas,
            'empresas_expiradas': empresas_expiradas,
            'total_usuarios': total_usuarios,
            'total_movimientos': total_movimientos,
            'planes_activos': planes_activos,
            'total_rubros': total_rubros,
            'total_categorias': total_categorias,
            'empresas_este_mes': empresas_este_mes,
            'empresas_esta_semana': empresas_esta_semana,
            'distribucion_planes': distribucion_planes,
            'empresas_recientes': empresas_recientes
        }
    
    @staticmethod
    def get_empresas_list(search=None, estado=None, plan_id=None, page=1, per_page=20):
        """
        Retorna lista de empresas con filtros y paginación
        """
        query = Empresa.query
        
        # Filtro por búsqueda
        if search:
            query = query.filter(
                Empresa.nombre.ilike(f'%{search}%') |
                Empresa.correo.ilike(f'%{search}%') |
                Empresa.rut_empresa.ilike(f'%{search}%')
            )
        
        # Filtro por estado
        if estado:
            query = query.filter_by(estado=estado)
        
        # Filtro por plan
        if plan_id:
            query = query.filter_by(plan_id=plan_id)
        
        # Paginación
        pagination = query.order_by(Empresa.fecha_creacion.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        # Agregar nombre del plan a cada empresa
        empresas_dict = []
        for empresa in pagination.items:
            empresa_dict = empresa.to_dict()
            empresa_dict['plan_nombre'] = empresa.plan.nombre if empresa.plan else None
            empresas_dict.append(empresa_dict)
        
        return {
            'empresas': empresas_dict,
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': page
        }
    
    @staticmethod
    def get_empresa_detalle(empresa_id):
        """
        Retorna detalle completo de una empresa
        """
        empresa = Empresa.query.get(empresa_id)
        if not empresa:
            return None
        
        # Contar recursos
        rubros_count = Rubro.query.filter_by(empresa_id=empresa_id).count()
        categorias_count = Categoria.query.filter_by(empresa_id=empresa_id).count()
        movimientos_count = Movimiento.query.filter_by(empresa_id=empresa_id).count()
        users_count = User.query.filter_by(empresa_id=empresa_id).count()
        
        # Movimientos últimos 30 días
        fecha_30_dias = datetime.utcnow() - timedelta(days=30)
        movimientos_30_dias = Movimiento.query.filter(
            Movimiento.empresa_id == empresa_id,
            Movimiento.fecha >= fecha_30_dias
        ).count()
        
        # Último acceso
        ultimo_acceso = empresa.ultimo_acceso
        
        # Calcular días restantes del plan
        dias_restantes = None
        esta_vencido = False
        if empresa.fecha_expiracion_plan:
            hoy = datetime.utcnow().date()
            fecha_expiracion = empresa.fecha_expiracion_plan.date()
            dias_restantes = (fecha_expiracion - hoy).days
            esta_vencido = dias_restantes < 0
        
        return {
            **empresa.to_dict(),
            'plan_nombre': empresa.plan.nombre if empresa.plan else None,
            'dias_restantes': dias_restantes,
            'esta_vencido': esta_vencido,
            'estadisticas': {
                'rubros_count': rubros_count,
                'categorias_count': categorias_count,
                'movimientos_total': movimientos_count,
                'movimientos_30_dias': movimientos_30_dias,
                'users_count': users_count,
                'ultimo_acceso': ultimo_acceso.isoformat() if ultimo_acceso else None
            }
        }
    
    @staticmethod
    def create_empresa(data):
        """
        Crea una nueva empresa
        """
        empresa = Empresa(
            nombre=data['nombre'],
            rut_empresa=data.get('rut_empresa'),
            correo=data.get('correo'),
            telefono=data.get('telefono'),
            direccion=data.get('direccion'),
            estado=data.get('estado', 'activa')
        )
        
        # Establecer PIN
        if 'pin' in data:
            empresa.set_pin(data['pin'])
        
        # Asignar plan
        if 'plan_id' in data:
            empresa.plan_id = data['plan_id']
        
        # Fechas del plan
        if 'fecha_inicio_plan' in data:
            empresa.fecha_inicio_plan = datetime.fromisoformat(data['fecha_inicio_plan'])
        if 'fecha_expiracion_plan' in data:
            empresa.fecha_expiracion_plan = datetime.fromisoformat(data['fecha_expiracion_plan'])
        
        db.session.add(empresa)
        db.session.commit()
        
        return empresa
    
    @staticmethod
    def update_empresa(empresa_id, data):
        """
        Actualiza una empresa existente
        """
        empresa = Empresa.query.get(empresa_id)
        if not empresa:
            return None
        
        # Campos actualizables
        if 'nombre' in data:
            empresa.nombre = data['nombre']
        if 'rut_empresa' in data:
            empresa.rut_empresa = data['rut_empresa']
        if 'correo' in data:
            empresa.correo = data['correo']
        if 'telefono' in data:
            empresa.telefono = data['telefono']
        if 'direccion' in data:
            empresa.direccion = data['direccion']
        if 'estado' in data:
            empresa.estado = data['estado']
        if 'plan_id' in data:
            empresa.plan_id = data['plan_id']
        
        # Actualizar PIN si se proporciona (no vacío)
        if 'pin' in data and data['pin']:
            empresa.set_pin(data['pin'])
        
        # Actualizar fechas del plan
        if 'fecha_inicio_plan' in data:
            empresa.fecha_inicio_plan = datetime.fromisoformat(data['fecha_inicio_plan'])
        if 'fecha_expiracion_plan' in data:
            empresa.fecha_expiracion_plan = datetime.fromisoformat(data['fecha_expiracion_plan'])
        
        db.session.commit()
        
        return empresa
    
    @staticmethod
    def deactivate_empresa(empresa_id):
        """
        Desactiva una empresa (soft delete)
        """
        empresa = Empresa.query.get(empresa_id)
        if not empresa:
            return None
        
        empresa.estado = 'inactiva'
        db.session.commit()
        
        return empresa
    
    @staticmethod
    def activate_empresa(empresa_id):
        """
        Activa una empresa
        """
        empresa = Empresa.query.get(empresa_id)
        if not empresa:
            return None
        
        empresa.estado = 'activa'
        db.session.commit()
        
        return empresa
    
    @staticmethod
    def get_planes_list():
        """
        Retorna lista de todos los planes (activos e inactivos)
        """
        planes = Plan.query.all()
        return [plan.to_dict() for plan in planes]
    
    @staticmethod
    def toggle_plan_status(plan_id):
        """
        Activa o desactiva un plan (toggle del estado activo)
        """
        from app.models.empresa import Empresa
        
        plan = Plan.query.get(plan_id)
        if not plan:
            return None
        
        # Si vamos a desactivar, verificar si hay empresas usando este plan
        if plan.activo:
            empresas_usando = Empresa.query.filter_by(plan_id=plan_id).count()
            if empresas_usando > 0:
                raise Exception(f"No se puede desactivar el plan porque está siendo usado por {empresas_usando} empresa(s)")
        
        # Toggle del estado activo
        plan.activo = not plan.activo
        db.session.commit()
        
        return plan
    
    @staticmethod
    def create_plan(data):
        """
        Crea un nuevo plan
        """
        plan = Plan(
            nombre=data['nombre'],
            descripcion=data.get('descripcion'),
            precio_mensual=data.get('precio_mensual', 0.0),
            max_rubros=data.get('max_rubros', 3),
            max_categorias=data.get('max_categorias', 10),
            max_usuarios=data.get('max_usuarios', 1),
            max_movimientos_mensuales=data.get('max_movimientos_mensuales', 100),
            acceso_reportes_avanzados=data.get('acceso_reportes_avanzados', False),
            acceso_export_pdf=data.get('acceso_export_pdf', False),
            activo=data.get('activo', True)
        )
        
        db.session.add(plan)
        db.session.commit()
        
        return plan
    
    @staticmethod
    def update_plan(plan_id, data):
        """
        Actualiza un plan existente
        """
        plan = Plan.query.get(plan_id)
        if not plan:
            return None
        
        if 'nombre' in data:
            plan.nombre = data['nombre']
        if 'descripcion' in data:
            plan.descripcion = data['descripcion']
        if 'precio_mensual' in data:
            plan.precio_mensual = data['precio_mensual']
        if 'max_rubros' in data:
            plan.max_rubros = data['max_rubros']
        if 'max_categorias' in data:
            plan.max_categorias = data['max_categorias']
        if 'max_usuarios' in data:
            plan.max_usuarios = data['max_usuarios']
        if 'max_movimientos_mensuales' in data:
            plan.max_movimientos_mensuales = data['max_movimientos_mensuales']
        if 'acceso_reportes_avanzados' in data:
            plan.acceso_reportes_avanzados = data['acceso_reportes_avanzados']
        if 'acceso_export_pdf' in data:
            plan.acceso_export_pdf = data['acceso_export_pdf']
        if 'activo' in data:
            plan.activo = data['activo']
        
        db.session.commit()
        
        return plan
        
    @staticmethod
    def reset_empresa_data(empresa_id):
        """
        Resetea todos los registros de movimientos, cortes, facturas,
        recordatorios, rubros y categorías de una empresa, dejándola vacía.
        Mantiene la empresa y sus usuarios intactos.
        """
        from app.models.corte_pos import CortePOS
        from app.models.factura_compra import FacturaCompra
        from app.models.ganancia_rubro import GananciaRubro
        from app.models.recordatorio import Recordatorio
        from app.models.importacion_venta import ImportacionVenta
        from app.models.notification import Notification
        from app.models.notification_preference import NotificationPreference
        
        try:
            # 1. Eliminar Movimientos
            Movimiento.query.filter_by(empresa_id=empresa_id).delete(synchronize_session=False)
            
            # 2. Eliminar Recordatorios (cascada elimina HistorialRecordatorio)
            recordatorios = Recordatorio.query.filter_by(empresa_id=empresa_id).all()
            for r in recordatorios:
                db.session.delete(r)
            
            # 3. Eliminar Cortes POS (cascada elimina DetalleCortePOS)
            cortes = CortePOS.query.filter_by(empresa_id=empresa_id).all()
            for c in cortes:
                db.session.delete(c)
            
            # 4. Eliminar Ganancia por Rubro
            GananciaRubro.query.filter_by(empresa_id=empresa_id).delete(synchronize_session=False)
            
            # 5. Eliminar Facturas de Compra (cascada elimina FacturaDetalle y FacturaRubro)
            facturas = FacturaCompra.query.filter_by(empresa_id=empresa_id).all()
            for f in facturas:
                db.session.delete(f)
            
            # 6. Eliminar Historial de Importación de Ventas
            ImportacionVenta.query.filter_by(empresa_id=empresa_id).delete(synchronize_session=False)
            
            # 7. Eliminar Notificaciones
            Notification.query.filter_by(empresa_id=empresa_id).delete(synchronize_session=False)
            
            # 8. Eliminar Preferencias de Notificaciones
            NotificationPreference.query.filter_by(empresa_id=empresa_id).delete(synchronize_session=False)
            
            # 9. Eliminar Rubros y Categorías
            Rubro.query.filter_by(empresa_id=empresa_id).delete(synchronize_session=False)
            Categoria.query.filter_by(empresa_id=empresa_id).delete(synchronize_session=False)
            
            # Hacer commit de todas las operaciones
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            raise e

