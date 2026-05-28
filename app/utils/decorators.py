from functools import wraps
from flask import session, redirect, url_for, flash
from app.models.user import User

def admin_required(f):
    """
    Decorador para restringir acceso solo a usuarios con rol ADMIN
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Verificar si hay un usuario en sesión
        if 'user_id' not in session:
            flash('Debe iniciar sesión para acceder a esta página', 'error')
            return redirect(url_for('main.login'))
        
        # Obtener el usuario de la sesión
        user = User.query.get(session['user_id'])
        
        # Verificar que el usuario existe y es ADMIN
        if not user or not user.is_admin():
            flash('Acceso denegado. Se requiere rol de administrador', 'error')
            return redirect(url_for('main.dashboard'))
        
        return f(*args, **kwargs)
    
    return decorated_function

def login_required(f):
    """
    Decorador para requerir inicio de sesión
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Verificar si hay un usuario en sesión
        if 'user_id' not in session:
            flash('Debe iniciar sesión para acceder a esta página', 'error')
            return redirect(url_for('main.login'))
        
        return f(*args, **kwargs)
    
    return decorated_function

def empresa_required(f):
    """
    Decorador para restringir acceso solo a usuarios con rol EMPRESA
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Verificar si hay un usuario en sesión
        if 'user_id' not in session:
            flash('Debe iniciar sesión para acceder a esta página', 'error')
            return redirect(url_for('main.login'))
        
        # Obtener el usuario de la sesión
        user = User.query.get(session['user_id'])
        
        # Verificar que el usuario existe y es EMPRESA
        if not user or not user.is_empresa():
            flash('Acceso denegado. Esta funcionalidad es solo para empresas', 'error')
            return redirect(url_for('main.dashboard'))
        
        return f(*args, **kwargs)
    
    return decorated_function
