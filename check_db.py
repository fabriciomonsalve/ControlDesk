#!/usr/bin/env python3

from app import create_app, db
from app.models.movimiento import Movimiento
from app.models.rubro import Rubro
from app.models.categoria import Categoria

def check_database():
    app = create_app()
    with app.app_context():
        print("=== Estado de la Base de Datos ===")
        
        # Contar registros
        rubros_count = Rubro.query.count()
        categorias_count = Categoria.query.count()
        movimientos_count = Movimiento.query.count()
        
        print(f"Rubros: {rubros_count}")
        print(f"Categorías: {categorias_count}")
        print(f"Movimientos: {movimientos_count}")
        
        # Mostrar rubros
        if rubros_count > 0:
            print("\n--- Rubros ---")
            for rubro in Rubro.query.all():
                print(f"  {rubro.id}: {rubro.nombre}")
        
        # Mostrar movimientos
        if movimientos_count > 0:
            print("\n--- Movimientos ---")
            for mov in Movimiento.query.limit(5).all():
                print(f"  {mov.id}: {mov.tipo} - ${mov.monto:.2f} - {mov.rubro.nombre if mov.rubro else 'Sin rubro'}")
        
        # Calcular totales
        if movimientos_count > 0:
            total_ingresos = db.session.query(db.func.sum(Movimiento.monto)).filter(Movimiento.tipo == 'ingreso').scalar() or 0
            total_gastos = db.session.query(db.func.sum(Movimiento.monto)).filter(Movimiento.tipo == 'gasto').scalar() or 0
            print(f"\n--- Totales ---")
            print(f"Ingresos: ${total_ingresos:.2f}")
            print(f"Gastos: ${total_gastos:.2f}")
            print(f"Balance: ${total_ingresos - total_gastos:.2f}")

if __name__ == '__main__':
    check_database()
