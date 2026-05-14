#!/usr/bin/env python3
"""
Script para crear datos de prueba para el dashboard
"""

from datetime import datetime, timedelta
import random
from app import create_app, db
from app.models.rubro import Rubro
from app.models.categoria import Categoria
from app.models.movimiento import Movimiento

def create_test_movements():
    """Crear 10 movimientos por rubro para testing"""
    app = create_app()
    
    with app.app_context():
        # Obtener rubros existentes
        rubros = Rubro.query.all()
        
        if not rubros:
            print("No hay rubros en la base de datos. Ejecuta primero el script de inicialización.")
            return
        
        # Datos de prueba para movimientos
        ingresos_descriptions = [
            "Venta de productos", "Servicios profesionales", "Consultoría", "Desarrollo web",
            "Mantenimiento", "Soporte técnico", "Capacitación", "Licencias",
            "Proyectos especiales", "Honorarios", "Comisiones", "Facturación mensual"
        ]
        
        gastos_descriptions = [
            "Alquiler oficina", "Servicios básicos", "Suministros", "Material de oficina",
            "Software", "Hardware", "Marketing", "Publicidad", "Transporte",
            "Comidas", "Seguros", "Impuestos", "Mantenimiento equipo"
        ]
        
        print(f"Creando movimientos para {len(rubros)} rubros...")
        
        total_created = 0
        
        for rubro in rubros:
            print(f"\nProcesando rubro: {rubro.nombre}")
            
            # Obtener todas las categorías disponibles
            categorias = Categoria.query.all()
            
            if not categorias:
                print(f"  - No hay categorías en la base de datos")
                continue
            
            # Crear 5 ingresos y 5 gastos por rubro
            for i in range(10):
                # Determinar tipo (5 ingresos, 5 gastos)
                tipo = 'ingreso' if i < 5 else 'gasto'
                
                # Seleccionar descripción aleatoria
                if tipo == 'ingreso':
                    descripcion = random.choice(ingresos_descriptions)
                    monto = random.randint(50000, 500000)  # $50.000 - $500.000
                else:
                    descripcion = random.choice(gastos_descriptions)
                    monto = random.randint(10000, 200000)  # $10.000 - $200.000
                
                # Seleccionar categoría aleatoria
                categoria = random.choice(categorias)
                
                # Fecha aleatoria en los últimos 90 días
                dias_aleatorios = random.randint(0, 90)
                fecha = datetime.now() - timedelta(days=dias_aleatorios)
                
                # Crear movimiento
                movimiento = Movimiento(
                    tipo=tipo,
                    monto=monto,
                    descripcion=descripcion,
                    fecha=fecha,
                    rubro_id=rubro.id,
                    categoria_id=categoria.id
                )
                
                db.session.add(movimiento)
                total_created += 1
                
                print(f"  - {tipo.title()}: ${monto:,} - {descripcion}")
        
        # Guardar todos los movimientos
        try:
            db.session.commit()
            print(f"\n✅ Se crearon {total_created} movimientos exitosamente")
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Error al crear movimientos: {e}")
        
        # Mostrar resumen
        print("\n📊 Resumen de datos creados:")
        for rubro in rubros:
            ingresos = db.session.query(db.func.sum(Movimiento.monto)).filter(
                Movimiento.rubro_id == rubro.id,
                Movimiento.tipo == 'ingreso'
            ).scalar() or 0
            
            gastos = db.session.query(db.func.sum(Movimiento.monto)).filter(
                Movimiento.rubro_id == rubro.id,
                Movimiento.tipo == 'gasto'
            ).scalar() or 0
            
            print(f"  {rubro.nombre}:")
            print(f"    Ingresos: ${ingresos:,.0f}")
            print(f"    Gastos: ${gastos:,.0f}")
            print(f"    Balance: ${(ingresos - gastos):,.0f}")

if __name__ == "__main__":
    create_test_movements()
