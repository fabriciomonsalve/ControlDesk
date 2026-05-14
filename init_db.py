"""
Script para inicializar la base de datos de ControlPyme
Crea las tablas y datos iniciales necesarios
"""

from app import create_app, db
from app.models.rubro import Rubro
from app.models.categoria import Categoria

def init_database():
    """Inicializa la base de datos con tablas y datos iniciales"""
    app = create_app()
    
    with app.app_context():
        # Crear todas las tablas
        print("Creando tablas en la base de datos...")
        db.create_all()
        print("Tablas creadas exitosamente.")
        
        # Verificar si ya existen datos
        if Rubro.query.first() or Categoria.query.first():
            print("La base de datos ya contiene datos. Omitiendo creación de datos iniciales.")
            return
        
        # Crear rubros iniciales
        print("Creando rubros iniciales...")
        rubros_iniciales = [
            Rubro(nombre='Ferretería'),
            Rubro(nombre='Apicultura'),
            Rubro(nombre='Agricultura')
        ]
        
        for rubro in rubros_iniciales:
            db.session.add(rubro)
        
        # Crear categorías iniciales
        print("Creando categorías iniciales...")
        categorias_iniciales = [
            # Categorías de gastos
            Categoria(nombre='Compras'),
            Categoria(nombre='Insumos'),
            Categoria(nombre='Servicios'),
            Categoria(nombre='Mantenimiento'),
            Categoria(nombre='Impuestos'),
            Categoria(nombre='Alquiler'),
            Categoria(nombre='Sueldos'),
            Categoria(nombre='Marketing'),
            # Categorías de ingresos
            Categoria(nombre='Ventas'),
            Categoria(nombre='Servicios Profesionales'),
            Categoria(nombre='Alquileres'),
            Categoria(nombre='Intereses'),
            Categoria(nombre='Otros Ingresos')
        ]
        
        for categoria in categorias_iniciales:
            db.session.add(categoria)
        
        # Confirmar cambios
        db.session.commit()
        print("Datos iniciales creados exitosamente.")
        
        # Mostrar resumen
        print("\n=== Resumen de la inicialización ===")
        print(f"Rubros creados: {Rubro.query.count()}")
        print(f"Categorías creadas: {Categoria.query.count()}")
        print("\nRubros disponibles:")
        for rubro in Rubro.query.all():
            print(f"  - {rubro.nombre}")
        print("\nCategorías disponibles:")
        for categoria in Categoria.query.all():
            print(f"  - {categoria.nombre}")

def reset_database():
    """Elimina y recrea la base de datos (útil para desarrollo)"""
    app = create_app()
    
    with app.app_context():
        print("Eliminando tablas existentes...")
        db.drop_all()
        print("Tablas eliminadas.")
        
        init_database()

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--reset':
        reset_database()
    else:
        init_database()
