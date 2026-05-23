"""
Script para migrar la tabla categorías al nuevo esquema
Agrega campos: descripcion, estado, icono, color
Renombra: created_at -> fecha_creacion, updated_at -> fecha_actualizacion
"""
from app import create_app, db
from app.models.categoria import Categoria

def migrate_categorias():
    """Migra la tabla categorías al nuevo esquema"""
    app = create_app()
    
    with app.app_context():
        # Verificar si la tabla existe
        inspector = db.inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('categorias')]
        
        print(f"Columnas actuales en categorías: {columns}")
        
        # Agregar nuevas columnas si no existen
        with db.engine.connect() as conn:
            if 'descripcion' not in columns:
                conn.execute(db.text("ALTER TABLE categorias ADD COLUMN descripcion TEXT"))
                print("Columna 'descripcion' agregada")
            
            if 'estado' not in columns:
                conn.execute(db.text("ALTER TABLE categorias ADD COLUMN estado VARCHAR(20) DEFAULT 'activa'"))
                print("Columna 'estado' agregada")
            
            if 'icono' not in columns:
                conn.execute(db.text("ALTER TABLE categorias ADD COLUMN icono VARCHAR(50)"))
                print("Columna 'icono' agregada")
            
            if 'color' not in columns:
                conn.execute(db.text("ALTER TABLE categorias ADD COLUMN color VARCHAR(7)"))
                print("Columna 'color' agregada")
            
            # Renombrar columnas si es necesario (SQLite no soporta ALTER COLUMN directamente)
            # Para SQLite, necesitamos recrear la tabla
            if 'created_at' in columns or 'updated_at' in columns:
                print("Renombrando columnas created_at/updated_at...")
                # Crear tabla nueva con el esquema correcto
                conn.execute(db.text("""
                    CREATE TABLE categorias_new (
                        id INTEGER PRIMARY KEY,
                        nombre VARCHAR(100) NOT NULL UNIQUE,
                        descripcion TEXT,
                        estado VARCHAR(20) DEFAULT 'activa',
                        icono VARCHAR(50),
                        color VARCHAR(7),
                        empresa_id INTEGER,
                        fecha_creacion DATETIME,
                        fecha_actualizacion DATETIME,
                        FOREIGN KEY (empresa_id) REFERENCES empresas (id)
                    )
                """))
                
                # Migrar datos
                conn.execute(db.text("""
                    INSERT INTO categorias_new (id, nombre, empresa_id, fecha_creacion, fecha_actualizacion, estado)
                    SELECT id, nombre, empresa_id, created_at, updated_at, 'activa'
                    FROM categorias
                """))
                
                # Eliminar tabla vieja
                conn.execute(db.text("DROP TABLE categorias"))
                
                # Renombrar tabla nueva
                conn.execute(db.text("ALTER TABLE categorias_new RENAME TO categorias"))
                
                print("Tabla categorías migrada exitosamente")
            
            conn.commit()
        
        # Verificar migración
        print("\nVerificando migración...")
        categorias = Categoria.query.all()
        print(f"Total categorías: {len(categorias)}")
        for cat in categorias:
            print(f"- {cat.nombre}: estado={cat.estado}, movimientos={cat.get_movimientos_count()}")
        
        print("\nMigración completada exitosamente")

if __name__ == '__main__':
    migrate_categorias()
