from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os

db = SQLAlchemy()
login_manager = LoginManager()

def format_clp_filter(amount):
    """Jinja2 filter for formatting Chilean pesos"""
    if amount is None:
        return "0"
    try:
        # Convertir a número si no lo es
        if isinstance(amount, str):
            amount = float(amount)
        
        # Formatear con puntos como separadores de miles
        formatted = "{:,.0f}".format(amount).replace(",", ".")
        return formatted
    except (ValueError, TypeError):
        return "0"

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL') or 'sqlite:///controlpyme.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'main.login'
    login_manager.login_message = 'Por favor inicia sesión para acceder a esta página.'
    
    # Configure user_loader for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        from app.models.user import User
        return User.query.get(int(user_id))
    
    # Import models to ensure they are registered with SQLAlchemy
    from app.models.rubro import Rubro
    from app.models.categoria import Categoria
    from app.models.movimiento import Movimiento
    from app.models.empresa import Empresa
    from app.models.user import User
    from app.models.plan import Plan
    from app.models.factura_compra import FacturaCompra
    from app.models.factura_detalle import FacturaDetalle
    from app.models.factura_rubro import FacturaRubro
    from app.models.recordatorio import Recordatorio
    from app.models.historial_recordatorio import HistorialRecordatorio
    
    # Register blueprints
    from app.routes.main import main_bp
    app.register_blueprint(main_bp)
    
    from app.routes.admin import admin_bp
    app.register_blueprint(admin_bp)
    
    from app.routes.facturas import facturas_bp
    app.register_blueprint(facturas_bp)
    
    from app.routes.recordatorios import recordatorios_bp
    app.register_blueprint(recordatorios_bp)
    
    # Register custom Jinja2 filters
    app.jinja_env.filters['format_clp'] = format_clp_filter
    
    return app
