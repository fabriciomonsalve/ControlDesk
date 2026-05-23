import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'instance', 'controlpyme.db')

if not os.path.exists(db_path):
    print("La base de datos no existe.")
else:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Verificar tablas
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print("Tablas en la base de datos:")
    for table in tables:
        print(f"  - {table[0]}")
    
    # Verificar conteo de registros
    print("\nConteo de registros:")
    for table in tables:
        table_name = table[0]
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"  {table_name}: {count} registros")
        except:
            print(f"  {table_name}: Error al contar")
    
    conn.close()
