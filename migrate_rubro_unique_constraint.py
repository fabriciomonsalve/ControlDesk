"""
Migración para cambiar la restricción UNIQUE en la tabla rubros
- Eliminar restricción UNIQUE del campo nombre
- Agregar restricción UNIQUE compuesta (nombre, empresa_id)
"""

from app import db
from sqlalchemy import text

def migrate():
    """Ejecuta la migración"""
    try:
        # Conexión a la base de datos
        conn = db.engine.connect()
        
        # SQLite no soporta ALTER TABLE para eliminar restricciones directamente
        # Necesitamos recrear la tabla
        
        print("Iniciando migración de restricción UNIQUE en rubros...")
        
        # 1. Crear tabla nueva sin la restricción UNIQUE en nombre
        conn.execute(text("""
            CREATE TABLE rubros_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre VARCHAR(100) NOT NULL,
                color VARCHAR(7) NOT NULL DEFAULT '#2563eb',
                empresa_id INTEGER,
                created_at DATETIME,
                updated_at DATETIME,
                FOREIGN KEY(empresa_id) REFERENCES empresas(id)
            )
        """))
        
        # 2. Copiar datos de la tabla vieja a la nueva
        conn.execute(text("""
            INSERT INTO rubros_new (id, nombre, color, empresa_id, created_at, updated_at)
            SELECT id, nombre, color, empresa_id, created_at, updated_at FROM rubros
        """))
        
        # 3. Eliminar tabla vieja
        conn.execute(text("DROP TABLE rubros"))
        
        # 4. Renombrar tabla nueva
        conn.execute(text("ALTER TABLE rubros_new RENAME TO rubros"))
        
        # 5. Crear índice único compuesto (nombre, empresa_id)
        conn.execute(text("""
            CREATE UNIQUE INDEX idx_rubro_nombre_empresa ON rubros(nombre, empresa_id)
        """))
        
        # 6. Recrear índices y relaciones
        conn.execute(text("""
            CREATE INDEX ix_rubros_empresa_id ON rubros(empresa_id)
        """))
        
        conn.commit()
        print("Migración completada exitosamente")
        print("La restricción UNIQUE ahora es compuesta: (nombre, empresa_id)")
        print("Esto permite que diferentes empresas tengan rubros con el mismo nombre")
        
    except Exception as e:
        print(f"Error durante la migración: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    from app import create_app
    app = create_app()
    with app.app_context():
        migrate()
