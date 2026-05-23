"""
Migración para crear la tabla notifications con todos los campos requeridos
"""
import sqlite3
import os

def migrate_notifications():
    """Crea la tabla notifications con índices optimizados"""
    
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
            WHERE type='table' AND name='notifications'
        """)
        
        if cursor.fetchone():
            print("La tabla notifications ya existe.")
            return
        
        # Crear la tabla notifications con todos los campos
        cursor.execute("""
            CREATE TABLE notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title VARCHAR(255) NOT NULL,
                message TEXT NOT NULL,
                type VARCHAR(20) NOT NULL DEFAULT 'info',
                priority VARCHAR(20) NOT NULL DEFAULT 'medium',
                category VARCHAR(50) NOT NULL DEFAULT 'system',
                user_id INTEGER,
                empresa_id INTEGER NOT NULL,
                is_read BOOLEAN NOT NULL DEFAULT 0,
                is_automatic BOOLEAN NOT NULL DEFAULT 0,
                insight_type VARCHAR(100),
                action_url VARCHAR(500),
                module VARCHAR(50),
                icon VARCHAR(50),
                meta_data JSON,
                analytics_reference VARCHAR(100),
                created_at DATETIME NOT NULL,
                read_at DATETIME,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (empresa_id) REFERENCES empresas (id)
            )
        """)
        
        # Crear índices para mejor rendimiento
        cursor.execute("""
            CREATE INDEX idx_notifications_empresa 
            ON notifications(empresa_id)
        """)
        
        cursor.execute("""
            CREATE INDEX idx_notifications_user 
            ON notifications(user_id)
        """)
        
        cursor.execute("""
            CREATE INDEX idx_notifications_priority 
            ON notifications(priority)
        """)
        
        cursor.execute("""
            CREATE INDEX idx_notifications_type 
            ON notifications(type)
        """)
        
        cursor.execute("""
            CREATE INDEX idx_notifications_is_read 
            ON notifications(is_read)
        """)
        
        cursor.execute("""
            CREATE INDEX idx_notifications_created_at 
            ON notifications(created_at DESC)
        """)
        
        cursor.execute("""
            CREATE INDEX idx_notifications_empresa_fecha 
            ON notifications(empresa_id, created_at DESC)
        """)
        
        cursor.execute("""
            CREATE INDEX idx_notifications_empresa_leidas 
            ON notifications(empresa_id, is_read)
        """)
        
        conn.commit()
        print("Tabla notifications creada exitosamente con todos los índices.")
        
    except Exception as e:
        conn.rollback()
        print(f"Error durante la migración: {str(e)}")
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    migrate_notifications()
