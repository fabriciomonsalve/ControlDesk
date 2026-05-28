from datetime import datetime, timedelta
from app.models.empresa import Empresa
from app.models.rubro import Rubro
from app.models.categoria import Categoria
from app.models.movimiento import Movimiento
from app import db

class PlanService:
    """Servicio para validación de límites de planes y control de acceso"""
    
    @staticmethod
    def validate_plan_expiration(empresa_id):
        """
        Valida si el plan de la empresa ha expirado
        Retorna: (is_expired, message)
        """
        empresa = Empresa.query.get(empresa_id)
        if not empresa:
            return True, "Empresa no encontrada"
        
        if empresa.is_plan_expired():
            return True, "Cuenta expirada. Contacte al administrador para renovar su plan."
        
        return False, None
    
    @staticmethod
    def can_create_rubro(empresa_id):
        """
        Valida si la empresa puede crear un nuevo rubro según su plan
        Retorna: (can_create, message)
        """
        empresa = Empresa.query.get(empresa_id)
        if not empresa:
            return False, "Empresa no encontrada"
        
        # Validar expiración del plan
        is_expired, message = PlanService.validate_plan_expiration(empresa_id)
        if is_expired:
            return False, message
        
        # Si no tiene plan asignado, permitir
        if not empresa.plan:
            return True, None
        
        # Contar rubros actuales
        rubro_count = Rubro.query.filter_by(empresa_id=empresa_id).count()
        
        if rubro_count >= empresa.plan.max_rubros:
            return False, f"Ha alcanzado el límite de rubros de su plan ({empresa.plan.max_rubros}). Actualice su plan para crear más."
        
        return True, None
    
    @staticmethod
    def can_create_categoria(empresa_id):
        """
        Valida si la empresa puede crear una nueva categoría según su plan
        Retorna: (can_create, message)
        """
        empresa = Empresa.query.get(empresa_id)
        if not empresa:
            return False, "Empresa no encontrada"
        
        # Validar expiración del plan
        is_expired, message = PlanService.validate_plan_expiration(empresa_id)
        if is_expired:
            return False, message
        
        # Si no tiene plan asignado, permitir
        if not empresa.plan:
            return True, None
        
        # Contar categorías actuales
        categoria_count = Categoria.query.filter_by(empresa_id=empresa_id).count()
        
        if categoria_count >= empresa.plan.max_categorias:
            return False, f"Ha alcanzado el límite de categorías de su plan ({empresa.plan.max_categorias}). Actualice su plan para crear más."
        
        return True, None
    
    @staticmethod
    def can_create_movimiento(empresa_id):
        """
        Valida si la empresa puede crear un nuevo movimiento según su plan
        Retorna: (can_create, message)
        """
        empresa = Empresa.query.get(empresa_id)
        if not empresa:
            return False, "Empresa no encontrada"
        
        # Validar expiración del plan
        is_expired, message = PlanService.validate_plan_expiration(empresa_id)
        if is_expired:
            return False, message
        
        # Si no tiene plan asignado, permitir
        if not empresa.plan:
            return True, None
        
        # Si el límite es -1, significa ilimitado
        if empresa.plan.max_movimientos_mensuales == -1:
            return True, None
        
        # Contar movimientos del mes actual
        current_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        movimiento_count = Movimiento.query.filter(
            Movimiento.empresa_id == empresa_id,
            Movimiento.fecha >= current_month
        ).count()
        
        if movimiento_count >= empresa.plan.max_movimientos_mensuales:
            return False, f"Ha alcanzado el límite mensual de movimientos de su plan ({empresa.plan.max_movimientos_mensuales}). Actualice su plan para continuar."
        
        return True, None
    
    @staticmethod
    def can_access_advanced_reports(empresa_id):
        """
        Valida si la empresa puede acceder a reportes avanzados
        Retorna: (can_access, message)
        """
        empresa = Empresa.query.get(empresa_id)
        if not empresa:
            return False, "Empresa no encontrada"
        
        # Validar expiración del plan
        is_expired, message = PlanService.validate_plan_expiration(empresa_id)
        if is_expired:
            return False, message
        
        # Si no tiene plan asignado, no permitir
        if not empresa.plan:
            return False, "No tiene un plan asignado que permita esta funcionalidad"
        
        if not empresa.plan.acceso_reportes_avanzados:
            return False, "Su plan no incluye acceso a reportes avanzados. Actualice su plan para acceder a esta funcionalidad."
        
        return True, None
    
    @staticmethod
    def can_export_pdf(empresa_id):
        """
        Valida si la empresa puede exportar a PDF
        Retorna: (can_export, message)
        """
        empresa = Empresa.query.get(empresa_id)
        if not empresa:
            return False, "Empresa no encontrada"
        
        # Validar expiración del plan
        is_expired, message = PlanService.validate_plan_expiration(empresa_id)
        if is_expired:
            return False, message
        
        # Si no tiene plan asignado, no permitir
        if not empresa.plan:
            return False, "No tiene un plan asignado que permita esta funcionalidad"
        
        if not empresa.plan.acceso_export_pdf:
            return False, "Su plan no incluye exportación a PDF. Actualice su plan para acceder a esta funcionalidad."
        
        return True, None
    
    @staticmethod
    def get_empresa_limits(empresa_id):
        """
        Retorna los límites y uso actual de la empresa
        """
        empresa = Empresa.query.get(empresa_id)
        if not empresa:
            return None
        
        # Contar recursos actuales
        rubro_count = Rubro.query.filter_by(empresa_id=empresa_id).count()
        categoria_count = Categoria.query.filter_by(empresa_id=empresa_id).count()
        
        # Movimientos del mes actual
        current_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        movimiento_count = Movimiento.query.filter(
            Movimiento.empresa_id == empresa_id,
            Movimiento.fecha >= current_month
        ).count()
        
        return {
            'empresa_id': empresa_id,
            'plan': empresa.plan.to_dict() if empresa.plan else None,
            'is_expired': empresa.is_plan_expired(),
            'limits': {
                'rubros': {
                    'max': empresa.plan.max_rubros if empresa.plan else None,
                    'current': rubro_count,
                    'remaining': (empresa.plan.max_rubros - rubro_count) if empresa.plan else None
                },
                'categorias': {
                    'max': empresa.plan.max_categorias if empresa.plan else None,
                    'current': categoria_count,
                    'remaining': (empresa.plan.max_categorias - categoria_count) if empresa.plan else None
                },
                'movimientos_mensuales': {
                    'max': empresa.plan.max_movimientos_mensuales if empresa.plan else None,
                    'current': movimiento_count,
                    'remaining': (empresa.plan.max_movimientos_mensuales - movimiento_count) if empresa.plan else None
                },
                'acceso_reportes_avanzados': empresa.plan.acceso_reportes_avanzados if empresa.plan else False,
                'acceso_export_pdf': empresa.plan.acceso_export_pdf if empresa.plan else False
            }
        }
