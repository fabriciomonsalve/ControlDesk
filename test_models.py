"""
Script de prueba para verificar los modelos y relaciones de la base de datos
"""

from app import create_app, db
from app.models.rubro import Rubro
from app.models.categoria import Categoria
from app.models.movimiento import Movimiento
from datetime import datetime, date

def test_models():
    """Prueba los modelos y sus relaciones"""
    app = create_app()
    
    with app.app_context():
        print("=== Prueba de Modelos SQLAlchemy ===\n")
        
        # 1. Verificar que los modelos se importaron correctamente
        print("1. Verificación de modelos:")
        print(f"   - Modelo Rubro: {Rubro.__name__}")
        print(f"   - Modelo Categoria: {Categoria.__name__}")
        print(f"   - Modelo Movimiento: {Movimiento.__name__}")
        
        # 2. Verificar relaciones
        print("\n2. Prueba de relaciones:")
        
        # Obtener un rubro existente
        rubro = Rubro.query.first()
        if rubro:
            print(f"   - Rubro encontrado: {rubro.nombre}")
            print(f"   - ID del rubro: {rubro.id}")
        else:
            print("   - No se encontraron rubros")
            return
        
        # Obtener una categoría existente
        categoria = Categoria.query.first()
        if categoria:
            print(f"   - Categoría encontrada: {categoria.nombre}")
            print(f"   - ID de la categoría: {categoria.id}")
        else:
            print("   - No se encontraron categorías")
            return
        
        # 3. Crear un movimiento de prueba
        print("\n3. Creación de movimiento de prueba:")
        try:
            movimiento = Movimiento(
                tipo='gasto',
                monto=150.50,
                fecha=date.today(),
                descripcion='Compra de herramientas para ferretería',
                rubro_id=rubro.id,
                categoria_id=categoria.id
            )
            
            db.session.add(movimiento)
            db.session.commit()
            
            print(f"   - Movimiento creado: ID {movimiento.id}")
            print(f"   - Tipo: {movimiento.tipo}")
            print(f"   - Monto: ${movimiento.monto}")
            print(f"   - Descripción: {movimiento.descripcion}")
            
        except Exception as e:
            print(f"   - Error al crear movimiento: {e}")
            db.session.rollback()
            return
        
        # 4. Verificar relaciones inversas
        print("\n4. Verificación de relaciones inversas:")
        print(f"   - Movimientos del rubro '{rubro.nombre}': {len(rubro.movimientos)}")
        print(f"   - Movimientos de la categoría '{categoria.nombre}': {len(categoria.movimientos)}")
        
        # 5. Probar método to_dict
        print("\n5. Prueba de serialización:")
        movimiento_dict = movimiento.to_dict()
        print("   - Movimiento serializado:")
        for key, value in movimiento_dict.items():
            print(f"     {key}: {value}")
        
        # 6. Probar validación de tipo
        print("\n6. Prueba de validación de tipo:")
        try:
            movimiento_ingreso = Movimiento(
                tipo='ingreso',
                monto=500.00,
                fecha=date.today(),
                descripcion='Venta de productos',
                rubro_id=rubro.id,
                categoria_id=categoria.id
            )
            db.session.add(movimiento_ingreso)
            db.session.commit()
            print("   - Movimiento de tipo 'ingreso' creado exitosamente")
        except Exception as e:
            print(f"   - Error: {e}")
        
        # 7. Intentar crear movimiento con tipo inválido
        print("\n7. Prueba de validación de tipo inválido:")
        try:
            movimiento_invalido = Movimiento(
                tipo='invalido',
                monto=100.00,
                fecha=date.today(),
                descripcion='Movimiento inválido',
                rubro_id=rubro.id,
                categoria_id=categoria.id
            )
            db.session.add(movimiento_invalido)
            db.session.commit()
            print("   - ERROR: Se permitió un tipo inválido")
        except Exception as e:
            print(f"   - Validación funcionó correctamente: {e}")
            db.session.rollback()
        
        # 8. Resumen final
        print("\n8. Resumen final de la base de datos:")
        print(f"   - Total de rubros: {Rubro.query.count()}")
        print(f"   - Total de categorías: {Categoria.query.count()}")
        print(f"   - Total de movimientos: {Movimiento.query.count()}")
        
        print("\n=== Prueba completada exitosamente ===")

if __name__ == '__main__':
    test_models()
