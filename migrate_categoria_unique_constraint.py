"""
Migración para cambiar la restricción UNIQUE en la tabla categorias
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
        
        print("Iniciando migración de restricción UNIQUE en categorias...")
        
        # 1. Crear tabla nueva sin la restricción UNIQUE en nombre
        conn.execute(text("""
            CREATE TABLE categorias_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre VARCHAR(100) NOT NULL,
                descripcion TEXT,
                estado VARCHAR(20) NOT NULL DEFAULT 'activa',
                icono VARCHAR(50),
                color VARCHAR(7),
                empresa_id INTEGER,
                fecha_creacion DATETIME,
                fecha_actualizacion DATETIME,
                FOREIGN KEY(empresa_id) REFERENCES empresas(id)
            )
        """))
        
        # 2. Copiar datos de la tabla vieja a la nueva
        conn.execute(text("""
            INSERT INTO categorias_new (id, nombre, descripcion, estado, icono, color, empresa_id, fecha_creacion, fecha_actualizacion)
            SELECT id, nombre, descripcion, estado, icono, color, empresa_id, fecha_creacion, fecha_actualizacion FROM categorias
        """))
        
        # 3. Eliminar tabla vieja
        conn.execute(text("DROP TABLE categorias"))
        
        # 4. Renombrar tabla nueva
        conn.execute(text("ALTER TABLE categorias_new RENAME TO categorias"))
        
        # 5. Crear índice único compuesto (nombre, empresa_id)
        conn.execute(text("""
            CREATE UNIQUE INDEX idx_categoria_nombre_empresa ON categorias(nombre, empresa_id)
        """))
        
        # 6. Recrear índices
        conn.execute(text("""
            CREATE INDEX ix_categorias_empresa_id ON categorias(empresa_id)
        """))
        
        conn.commit()
        print("Migración completada exitosamente")
        print("La restricción UNIQUE ahora es compuesta: (nombre, empresa_id)")
        print("Esto permite que diferentes empresas tengan categorías con el mismo nombre")
        
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
