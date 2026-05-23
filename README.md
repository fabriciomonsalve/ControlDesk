# ControlDesk

Plataforma web moderna para la gestión financiera de pequeñas y medianas empresas (PYMEs). ControlDesk permite administrar ingresos, gastos, movimientos financieros, generar reportes y controlar las finanzas de tu empresa de manera eficiente y profesional.

## 📋 Características Principales

- **Dashboard Interactivo**: Vista general con métricas clave, gráficos en tiempo real y resumen financiero
- **Gestión de Movimientos**: Registro y control de ingresos y gastos con filtros avanzados
- **Organización por Rubros**: Clasificación de actividades empresariales con colores personalizados
- **Categorías Flexibles**: Organización detallada de movimientos por categorías
- **Reportes Financieros**: Generación de reportes profesionales en PDF con análisis detallados
- **Estadísticas Avanzadas**: Análisis de tendencias, proyecciones y comportamiento histórico
- **Gestión Multiempresa**: Soporte para administrar múltiples empresas desde una sola plataforma
- **Sistema de Notificaciones**: Alertas personalizadas para movimientos importantes
- **Configuración Empresarial**: Personalización de nombre, PIN y preferencias del sistema
- **Seguridad**: Autenticación por PIN, gestión de sesiones y opciones de seguridad
- **Diseño Responsive**: Interfaz moderna adaptada para dispositivos móviles, tablets y desktop

## 🛠 Tecnologías Utilizadas

### Backend
- **Python 3.x**: Lenguaje de programación principal
- **Flask**: Framework web para aplicaciones Python
- **SQLAlchemy**: ORM para gestión de base de datos
- **SQLite**: Base de datos ligera y portable

### Frontend
- **HTML5**: Estructura de las páginas
- **Jinja2**: Motor de plantillas de Flask
- **Tailwind CSS**: Framework CSS para diseño moderno y responsive
- **JavaScript**: Interactividad y funcionalidades dinámicas
- **Chart.js**: Biblioteca para gráficos interactivos
- **Font Awesome**: Iconos vectoriales

## 📁 Estructura del Proyecto

```
ControlPyme/
├── app/
│   ├── __init__.py          # Inicialización de la aplicación Flask
│   ├── models/              # Modelos de base de datos
│   │   ├── empresa.py       # Modelo de empresa
│   │   ├── movimiento.py    # Modelo de movimientos
│   │   ├── rubro.py         # Modelo de rubros
│   │   ├── categoria.py     # Modelo de categorías
│   │   └── notificacion.py  # Modelo de notificaciones
│   ├── routes/              # Rutas y controladores
│   │   └── main.py          # Rutas principales de la aplicación
│   ├── services/            # Lógica de negocio
│   │   ├── auth_service.py  # Servicio de autenticación
│   │   ├── movimiento_service.py  # Servicio de movimientos
│   │   └── reportes_service.py    # Servicio de reportes
│   ├── templates/           # Plantillas HTML
│   │   ├── base.html        # Plantilla base con sidebar
│   │   ├── index.html       # Página de inicio
│   │   ├── login.html       # Página de login
│   │   ├── dashboard.html   # Dashboard principal
│   │   ├── movimientos.html # Gestión de movimientos
│   │   ├── rubros.html      # Gestión de rubros
│   │   ├── categorias.html  # Gestión de categorías
│   │   ├── reportes.html    # Reportes financieros
│   │   └── configuracion.html # Configuración del sistema
│   └── static/              # Archivos estáticos
├── instance/                # Base de datos SQLite (se crea automáticamente)
├── venv/                    # Entorno virtual de Python
├── config.py                # Configuración de la aplicación
├── run.py                   # Script para ejecutar la aplicación
└── requirements.txt         # Dependencias de Python
```

## 🚀 Instalación y Configuración

### Requisitos Previos

- Python 3.8 o superior
- pip (gestor de paquetes de Python)

### Pasos de Instalación

1. **Clonar o descargar el proyecto**
   ```bash
   cd C:\Users\56967\Desktop\ControlPyme
   ```

2. **Crear y activar el entorno virtual** (si no existe)
   ```bash
   python -m venv venv
   venv\Scripts\activate  # En Windows
   # En Linux/Mac: source venv/bin/activate
   ```

3. **Instalar las dependencias**
   ```bash
   pip install -r requirements.txt
   ```

4. **Verificar la base de datos**
   La base de datos SQLite se crea automáticamente en la carpeta `instance/` al ejecutar la aplicación por primera vez.

## 💻 Cómo Levantar la Aplicación

### Opción 1: Usando el script run.py

```bash
python run.py
```

La aplicación estará disponible en: `http://localhost:5000`

### Opción 2: Usando Flask directamente

```bash
python -m flask run
```

### Opción 3: Especificando host y puerto

```bash
python -m flask run --host=0.0.0.0 --port=5000
```

## 📖 Uso del Sistema

### 1. Primer Ingreso

1. Accede a `http://localhost:5000` en tu navegador
2. Selecciona la empresa deseada de la lista
3. Ingresa el PIN de 4 dígitos configurado para esa empresa
4. Serás redirigido al Dashboard principal

### 2. Crear una Nueva Empresa

1. Accede a la sección de **Configuración**
2. En la pestaña **Perfil de Empresa**, puedes cambiar el nombre y el PIN

### 3. Registrar Movimientos

1. Ve a la sección **Movimientos** o usa el botón **Nuevo Movimiento**
2. Selecciona el tipo: Ingreso o Gasto
3. Ingresa el monto
4. Selecciona el rubro y categoría correspondientes
5. Ingresa la fecha y una descripción opcional
6. Guarda el movimiento

### 4. Gestionar Rubros y Categorías

- **Rubros**: Organiza tus actividades por áreas (Ferretería, Agricultura, etc.)
- **Categorías**: Clasifica detalladamente cada movimiento dentro de un rubro

### 5. Generar Reportes

1. Ve a la sección **Reportes**
2. Filtra por fecha si es necesario
3. Visualiza los gráficos de tendencias y ganancias por rubro
4. Revisa las tablas de resumen mensual
5. Exporta reportes en PDF

### 6. Configurar Preferencias

1. Ve a **Configuración**
2. **Perfil de Empresa**: Cambia nombre, PIN o desactivar empresa
3. **Notificaciones**: Activa/desactiva alertas por tipo de movimiento
4. **Seguridad**: Configura duración de sesión y auto-logout

## 🎨 Módulos del Sistema

### Dashboard
- Métricas clave en tiempo real
- Gráficos interactivos
- Resumen financiero rápido

### Movimientos
- Lista completa de ingresos y gastos
- Filtros por fecha, tipo, rubro, categoría
- Paginación para grandes volúmenes de datos
- Edición y eliminación de movimientos

### Rubros
- Creación y gestión de rubros empresariales
- Asignación de colores personalizados
- Métricas por rubro

### Categorías
- Organización detallada por categorías
- Asociación con rubros
- Control de movimientos por categoría

### Importar Ventas
- Importación masiva de ventas
- Procesamiento de archivos
- Validación de datos

### Reportes
- Análisis de tendencias mensuales
- Ganancias por rubro
- Gráficos interactivos
- Exportación a PDF
- Tablas detalladas

### Configuración
- Perfil de empresa
- Preferencias de notificaciones
- Configuración de seguridad
- Gestión de sesión

## 🔒 Seguridad

- **Autenticación por PIN**: Sistema seguro de acceso de 4 dígitos
- **Gestión de Sesiones**: Control de tiempo de sesión activa
- **Auto-Logout**: Cierre automático después de inactividad
- **Datos Separados**: Información de cada empresa completamente aislada

## 📱 Responsividad

El sistema está diseñado para funcionar perfectamente en:
- **Dispositivos Móviles**: Diseño optimizado para pantallas pequeñas
- **Tablets**: Interfaz adaptable para pantallas medianas
- **Desktop**: Experiencia completa en pantallas grandes

## 🐛 Solución de Problemas

### La aplicación no inicia

1. Verifica que Python esté instalado: `python --version`
2. Asegúrate de estar en el entorno virtual: `venv\Scripts\activate`
3. Instala las dependencias: `pip install -r requirements.txt`
4. Verifica que el puerto 5000 no esté en uso

### Error de base de datos

1. Elimina la carpeta `instance/`
2. Reinicia la aplicación (se creará una nueva base de datos)

### Los gráficos no se muestran

1. Verifica la conexión a internet (Chart.js se carga desde CDN)
2. Revisa la consola del navegador para errores de JavaScript

## 📄 Licencia

Todos los derechos reservados © 2026

## 👨‍💻 Soporte

Para soporte técnico o consultas, contacta al equipo de desarrollo de KODESK.

---

**ControlDesk - Gestión Financiera Profesional para PYMEs**
