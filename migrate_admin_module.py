"""
Script de migración para el módulo de administración global
Agrega tablas: users, planes
Agrega columnas a: empresas (rut_empresa, correo, telefono, direccion, ultimo_acceso, plan_id, fecha_inicio_plan, fecha_expiracion_plan)
"""

from app import create_app, db
from app.models.user import User
from app.models.plan import Plan
from app.models.empresa import Empresa
from datetime import datetime, timedelta

def migrate():
    """Ejecuta la migración del módulo de administración"""
    app = create_app()
    
    with app.app_context():
        print("Iniciando migración del módulo de administración...")
        
        # Crear todas las tablas (SQLAlchemy maneja tablas ya existentes)
        print("Creando tablas...")
        db.create_all()
        
        # Crear planes por defecto
        print("Creando planes por defecto...")
        planes_por_defecto = [
            {
                'nombre': 'FREE',
                'descripcion': 'Plan gratuito con funcionalidades básicas',
                'precio_mensual': 0.0,
                'max_rubros': 3,
                'max_categorias': 10,
                'max_usuarios': 1,
                'max_movimientos_mensuales': 100,
                'acceso_reportes_avanzados': False,
                'acceso_export_pdf': False,
                'activo': True
            },
            {
                'nombre': 'BASIC',
                'descripcion': 'Plan básico para pequeñas empresas',
                'precio_mensual': 9900.0,
                'max_rubros': 10,
                'max_categorias': 30,
                'max_usuarios': 2,
                'max_movimientos_mensuales': 500,
                'acceso_reportes_avanzados': True,
                'acceso_export_pdf': False,
                'activo': True
            },
            {
                'nombre': 'PRO',
                'descripcion': 'Plan profesional para empresas en crecimiento',
                'precio_mensual': 19900.0,
                'max_rubros': 20,
                'max_categorias': 50,
                'max_usuarios': 5,
                'max_movimientos_mensuales': 2000,
                'acceso_reportes_avanzados': True,
                'acceso_export_pdf': True,
                'activo': True
            },
            {
                'nombre': 'ENTERPRISE',
                'descripcion': 'Plan empresarial sin límites',
                'precio_mensual': 49900.0,
                'max_rubros': -1,  # -1 significa ilimitado
                'max_categorias': -1,
                'max_usuarios': -1,
                'max_movimientos_mensuales': -1,
                'acceso_reportes_avanzados': True,
                'acceso_export_pdf': True,
                'activo': True
            }
        ]
        
        for plan_data in planes_por_defecto:
            # Verificar si el plan ya existe
            plan_existente = Plan.query.filter_by(nombre=plan_data['nombre']).first()
            if not plan_existente:
                plan = Plan(**plan_data)
                db.session.add(plan)
                print(f"  - Plan {plan_data['nombre']} creado")
            else:
                print(f"  - Plan {plan_data['nombre']} ya existe, omitiendo")
        
        db.session.commit()
        
        # Crear usuario admin por defecto
        print("Creando usuario administrador por defecto...")
        admin_existente = User.query.filter_by(email='admin@controldesk.cl').first()
        if not admin_existente:
            admin = User(
                email='admin@controldesk.cl',
                nombre='Administrador',
                role='ADMIN',
                activo=True
            )
            admin.set_password('admin123')  # Contraseña por defecto (cambiar después)
            db.session.add(admin)
            print("  - Usuario admin creado (email: admin@controldesk.cl, password: admin123)")
        else:
            print("  - Usuario admin ya existe, omitiendo")
        
        db.session.commit()
        
        # Agregar nuevas columnas a la tabla empresas (si no existen)
        print("Verificando columnas nuevas en tabla 'empresas'...")
        try:
            # Intentar agregar las nuevas columnas
            inspector = db.inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('empresas')]
            
            new_columns = [
                ('rut_empresa', 'VARCHAR(20)'),
                ('correo', 'VARCHAR(120)'),
                ('telefono', 'VARCHAR(20)'),
                ('direccion', 'VARCHAR(200)'),
                ('ultimo_acceso', 'DATETIME'),
                ('plan_id', 'INTEGER'),
                ('fecha_inicio_plan', 'DATETIME'),
                ('fecha_expiracion_plan', 'DATETIME')
            ]
            
            for col_name, col_type in new_columns:
                if col_name not in columns:
                    print(f"  - Agregando columna '{col_name}' a tabla 'empresas'...")
                    with db.engine.connect() as conn:
                        conn.execute(db.text(f"ALTER TABLE empresas ADD COLUMN {col_name} {col_type}"))
                        conn.commit()
                else:
                    print(f"  - Columna '{col_name}' ya existe, omitiendo")
            
            # Agregar foreign key para plan_id
            if 'plan_id' in columns:
                print("  - Verificando foreign key para plan_id...")
                # SQLite no soporta agregar foreign keys directamente, se maneja a nivel de aplicación
            
        except Exception as e:
            print(f"  - Error al agregar columnas: {e}")
            print("  - Las columnas pueden ya existir o la base de datos puede necesitar migración manual")
        
        db.session.commit()
        
        print("\nMigración completada exitosamente!")
        print("\nResumen:")
        print("- Tablas creadas: users, planes")
        print("- Planes por defecto creados: FREE, BASIC, PRO, ENTERPRISE")
        print("- Usuario admin creado: admin@controldesk.cl / admin123")
        print("- Columnas agregadas a empresas: rut_empresa, correo, telefono, direccion, ultimo_acceso, plan_id, fecha_inicio_plan, fecha_expiracion_plan")
        print("\nIMPORTANTE: Cambie la contraseña del administrador después del primer login!")

if __name__ == '__main__':
    try:
        migrate()
    except Exception as e:
        print(f"Error durante la migración: {e}")
        import traceback
        traceback.print_exc()
