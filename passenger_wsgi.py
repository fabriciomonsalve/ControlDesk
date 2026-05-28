# Passenger WSGI Configuration for ControlDesk
# Coloca este archivo en el directorio raíz de tu hosting cPanel
# (generalmente en public_html o un subdominio)

import sys
import os

# Configurar el PYTHONPATH para incluir el directorio del proyecto
# Reemplaza '/home/usuario/ControlPyme' con la ruta absoluta de tu proyecto en cPanel
# Puedes encontrar la ruta absoluta ejecutando: pwd en la terminal de cPanel
PROJECT_PATH = '/home/tu_usuario/public_html/ControlPyme'

if PROJECT_PATH not in sys.path:
    sys.path.insert(0, PROJECT_PATH)

# Cambiar al directorio del proyecto
os.chdir(PROJECT_PATH)

# Importar la aplicación Flask
from app import create_app

# Crear la aplicación
application = create_app()

# Configuración adicional para producción
if not os.environ.get('FLASK_DEBUG'):
    application.config['DEBUG'] = False

# Para Passenger, la aplicación debe estar en la variable 'application'
# No uses 'app' como nombre de variable, Passenger busca específicamente 'application'
