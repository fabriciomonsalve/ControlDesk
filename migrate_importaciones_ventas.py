"""
Script de migración para crear la tabla importaciones_ventas
"""
import sqlite3
import os
from datetime import datetime

def migrate_importaciones_ventas():
    """Crea la tabla importaciones_ventas si no existe"""
    
    # Ruta de la base de datos
    db_path = os.path.join(os.path.dirname(__file__), 'instance', 'controlpyme.db')
    
    if not os.path.exists(db_path):
        print("La base de datos no existe. Primero ejecuta la aplicación.")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Verificar si la tabla ya existe
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='importaciones_ventas'
        """)
        
        if cursor.fetchone():
            print("La tabla importaciones_ventas ya existe.")
            return
        
        # Crear la tabla importaciones_ventas
        cursor.execute("""
            CREATE TABLE importaciones_ventas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                archivo VARCHAR(255) NOT NULL,
                fecha DATETIME NOT NULL,
                registros_importados INTEGER NOT NULL DEFAULT 0,
                errores INTEGER NOT NULL DEFAULT 0,
                duplicados INTEGER NOT NULL DEFAULT 0,
                usuario VARCHAR(100) NOT NULL,
                estado VARCHAR(50) NOT NULL DEFAULT 'completado',
                errores_detalle TEXT,
                empresa_id INTEGER NOT NULL,
                fecha_creacion DATETIME NOT NULL,
                fecha_actualizacion DATETIME NOT NULL,
                FOREIGN KEY (empresa_id) REFERENCES empresas (id)
            )
        """)
        
        # Crear índices para mejor rendimiento
        cursor.execute("""
            CREATE INDEX idx_importaciones_ventas_empresa 
            ON importaciones_ventas(empresa_id)
        """)
        
        cursor.execute("""
            CREATE INDEX idx_importaciones_ventas_fecha 
            ON importaciones_ventas(fecha DESC)
        """)
        
        conn.commit()
        print("Migración completada exitosamente.")
        print("Tabla importaciones_ventas creada.")
        
    except Exception as e:
        conn.rollback()
        print(f"Error durante la migración: {str(e)}")
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    migrate_importaciones_ventas()
