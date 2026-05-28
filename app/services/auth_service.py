from flask import session
from app.models.empresa import Empresa
from app.models.user import User
from app.services.plan_service import PlanService
from app import db

class AuthService:
    """Servicio de autenticación para login multiempresa con PIN y login de ADMIN"""
    
    @staticmethod
    def validate_pin(empresa_id: int, pin: str) -> dict:
        """
        Valida el PIN de una empresa
        Args:
            empresa_id: ID de la empresa
            pin: PIN de 4 dígitos
        Returns:
            Dict con success y mensaje de error si falla
        """
        try:
            empresa = Empresa.query.get(empresa_id)
            
            if not empresa:
                return {
                    'success': False,
                    'error': 'Empresa no encontrada'
                }
            
            if empresa.estado != 'activa':
                return {
                    'success': False,
                    'error': 'Empresa no está activa'
                }
            
            if not empresa.verify_pin(pin):
                return {
                    'success': False,
                    'error': 'PIN incorrecto'
                }
            
            # Validar expiración del plan
            is_expired, expiration_message = PlanService.validate_plan_expiration(empresa_id)
            if is_expired:
                return {
                    'success': False,
                    'error': expiration_message
                }
            
            return {
                'success': True,
                'empresa': empresa.to_dict()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Error al validar PIN: {str(e)}'
            }
    
    @staticmethod
    def validate_admin_login(email: str, password: str) -> dict:
        """
        Valida el login de un usuario ADMIN por email y contraseña
        Args:
            email: Email del usuario
            password: Contraseña
        Returns:
            Dict con success, user y mensaje de error si falla
        """
        try:
            user = User.query.filter_by(email=email).first()
            
            if not user:
                return {
                    'success': False,
                    'error': 'Usuario no encontrado'
                }
            
            if not user.activo:
                return {
                    'success': False,
                    'error': 'Usuario no está activo'
                }
            
            if not user.is_admin():
                return {
                    'success': False,
                    'error': 'Acceso denegado. Se requiere rol de administrador'
                }
            
            if not user.verify_password(password):
                return {
                    'success': False,
                    'error': 'Contraseña incorrecta'
                }
            
            return {
                'success': True,
                'user': user.to_dict()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Error al validar login: {str(e)}'
            }
    
    @staticmethod
    def login(empresa_id: int, pin: str) -> dict:
        """
        Inicia sesión de una empresa (login por PIN)
        Args:
            empresa_id: ID de la empresa
            pin: PIN de 4 dígitos
        Returns:
            Dict con success, empresa y mensaje de error si falla
        """
        try:
            validation = AuthService.validate_pin(empresa_id, pin)
            
            if not validation['success']:
                return validation
            
            # Guardar en sesión
            session['empresa_id'] = empresa_id
            session['empresa_nombre'] = validation['empresa']['nombre']
            session['logged_in'] = True
            session['user_role'] = 'EMPRESA'
            
            return {
                'success': True,
                'empresa': validation['empresa']
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Error al iniciar sesión: {str(e)}'
            }
    
    @staticmethod
    def login_admin(email: str, password: str) -> dict:
        """
        Inicia sesión de un usuario ADMIN
        Args:
            email: Email del usuario
            password: Contraseña
        Returns:
            Dict con success, user y mensaje de error si falla
        """
        try:
            validation = AuthService.validate_admin_login(email, password)
            
            if not validation['success']:
                return validation
            
            # Guardar en sesión
            session['user_id'] = validation['user']['id']
            session['user_email'] = validation['user']['email']
            session['user_role'] = 'ADMIN'
            session['logged_in'] = True
            
            return {
                'success': True,
                'user': validation['user']
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Error al iniciar sesión: {str(e)}'
            }
    
    @staticmethod
    def logout():
        """Cierra la sesión actual"""
        session.clear()
    
    @staticmethod
    def is_logged_in() -> bool:
        """Verifica si hay una sesión activa"""
        return session.get('logged_in', False)
    
    @staticmethod
    def get_current_empresa() -> dict:
        """
        Obtiene la empresa de la sesión actual
        Returns:
            Dict con datos de la empresa o None si no hay sesión
        """
        if not AuthService.is_logged_in():
            return None
        
        return {
            'id': session.get('empresa_id'),
            'nombre': session.get('empresa_nombre')
        }
    
    @staticmethod
    def get_empresa_by_id(empresa_id: int) -> dict:
        """
        Obtiene una empresa por ID
        Args:
            empresa_id: ID de la empresa
        Returns:
            Dict con datos de la empresa o None si no existe
        """
        try:
            empresa = Empresa.query.get(empresa_id)
            if empresa:
                return empresa.to_dict()
            return None
        except Exception as e:
            return None
    
    @staticmethod
    def get_all_empresas() -> list:
        """
        Obtiene todas las empresas activas
        Returns:
            Lista de diccionarios con datos de empresas
        """
        try:
            empresas = Empresa.query.filter_by(estado='activa').all()
            return [empresa.to_dict() for empresa in empresas]
        except Exception as e:
            return []
    
    @staticmethod
    def change_pin(empresa_id: int, current_pin: str, new_pin: str) -> dict:
        """
        Cambia el PIN de una empresa
        Args:
            empresa_id: ID de la empresa
            current_pin: PIN actual
            new_pin: Nuevo PIN
        Returns:
            Dict con success y mensaje de error si falla
        """
        try:
            empresa = Empresa.query.get(empresa_id)
            
            if not empresa:
                return {
                    'success': False,
                    'error': 'Empresa no encontrada'
                }
            
            if not empresa.verify_pin(current_pin):
                return {
                    'success': False,
                    'error': 'PIN actual incorrecto'
                }
            
            # Validar que el nuevo PIN tenga 4 dígitos
            if not new_pin.isdigit() or len(new_pin) != 4:
                return {
                    'success': False,
                    'error': 'El nuevo PIN debe tener 4 dígitos numéricos'
                }
            
            empresa.set_pin(new_pin)
            db.session.commit()
            
            return {
                'success': True,
                'message': 'PIN actualizado correctamente'
            }
            
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'error': f'Error al cambiar PIN: {str(e)}'
            }
