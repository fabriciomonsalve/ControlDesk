import pandas as pd
import os
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import current_app
from app import db
from app.models.importacion_venta import ImportacionVenta
from app.models.movimiento import Movimiento
from app.services.notification_service import NotificationService


class ImportacionVentaService:
    """Servicio para manejar la importación de ventas desde archivos Excel/CSV"""
    
    # Extensiones permitidas
    ALLOWED_EXTENSIONS = {'xlsx', 'xls', 'csv'}
    
    # Mapeo de columnas estándar (para detección automática)
    COLUMN_MAPPINGS = {
        'fecha': ['fecha', 'fecha venta', 'date', 'fecha_venta', 'fec_venta', 'fec'],
        'producto': ['producto', 'producto_nombre', 'nombre_producto', 'item', 'descripcion', 'desc'],
        'cantidad': ['cantidad', 'qty', 'quantity', 'cant', 'unidades'],
        'total': ['total', 'total_neto', 'monto', 'importe', 'subtotal', 'total_venta'],
        'metodo_pago': ['metodo_pago', 'método_pago', 'metodo', 'payment_method', 'forma_pago'],
        'categoria': ['categoria', 'categoría', 'rubro', 'category']
    }
    
    @staticmethod
    def allowed_file(filename: str) -> bool:
        """Verifica si el archivo tiene una extensión permitida"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in ImportacionVentaService.ALLOWED_EXTENSIONS
    
    @staticmethod
    def read_file(file_path: str) -> Tuple[bool, Optional[pd.DataFrame], Optional[str]]:
        """
        Lee un archivo Excel o CSV y retorna el DataFrame
        
        Args:
            file_path: Ruta del archivo
            
        Returns:
            Tuple con (success, dataframe, error_message)
        """
        try:
            file_ext = file_path.rsplit('.', 1)[1].lower()
            
            if file_ext in ['xlsx', 'xls']:
                df = pd.read_excel(file_path, engine='openpyxl')
            elif file_ext == 'csv':
                # Intentar detectar encoding automáticamente
                try:
                    df = pd.read_csv(file_path, encoding='utf-8')
                except UnicodeDecodeError:
                    try:
                        df = pd.read_csv(file_path, encoding='latin-1')
                    except UnicodeDecodeError:
                        df = pd.read_csv(file_path, encoding='cp1252')
            else:
                return False, None, f"Formato de archivo no soportado: {file_ext}"
            
            # Limpiar nombres de columnas (quitar espacios y convertir a minúsculas)
            df.columns = df.columns.str.strip().str.lower()
            
            return True, df, None
            
        except Exception as e:
            return False, None, f"Error al leer el archivo: {str(e)}"
    
    @staticmethod
    def detect_columns(df: pd.DataFrame) -> Dict[str, Optional[str]]:
        """
        Detecta automáticamente las columnas del archivo basándose en nombres similares
        
        Args:
            df: DataFrame de pandas
            
        Returns:
            Diccionario con el mapeo de columnas detectadas
        """
        detected = {
            'fecha': None,
            'producto': None,
            'cantidad': None,
            'total': None,
            'metodo_pago': None,
            'categoria': None
        }
        
        columns = df.columns.tolist()
        
        for field, possible_names in ImportacionVentaService.COLUMN_MAPPINGS.items():
            for possible_name in possible_names:
                # Búsqueda exacta
                if possible_name in columns:
                    detected[field] = possible_name
                    break
                
                # Búsqueda aproximada (contiene)
                for col in columns:
                    if possible_name in col or col in possible_name:
                        detected[field] = col
                        break
                
                if detected[field]:
                    break
        
        return detected
    
    @staticmethod
    def get_file_preview(file_path: str, rows: int = 10) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Obtiene una vista previa del archivo con columnas detectadas
        
        Args:
            file_path: Ruta del archivo
            rows: Número de filas a mostrar en la vista previa
            
        Returns:
            Tuple con (success, preview_data, error_message)
        """
        success, df, error = ImportacionVentaService.read_file(file_path)
        
        if not success:
            return False, None, error
        
        # Detectar columnas
        detected_columns = ImportacionVentaService.detect_columns(df)
        
        # Obtener vista previa de datos
        preview_df = df.head(rows)
        preview_data = {
            'columns': df.columns.tolist(),
            'detected_columns': detected_columns,
            'preview': preview_df.to_dict('records'),
            'total_rows': len(df)
        }
        
        return True, preview_data, None
    
    @staticmethod
    def validate_mapping(mapping: Dict[str, str], available_columns: List[str]) -> Tuple[bool, Optional[str]]:
        """
        Valida que el mapeo de columnas sea correcto
        
        Args:
            mapping: Diccionario con el mapeo seleccionado por el usuario
            available_columns: Lista de columnas disponibles en el archivo
            
        Returns:
            Tuple con (is_valid, error_message)
        """
        required_fields = ['fecha', 'producto', 'cantidad', 'total']
        
        for field in required_fields:
            if field not in mapping or not mapping[field]:
                return False, f"El campo '{field}' es obligatorio"
            
            if mapping[field] not in available_columns:
                return False, f"La columna seleccionada para '{field}' no existe en el archivo"
        
        # Validar campos opcionales si fueron proporcionados
        optional_fields = ['metodo_pago', 'categoria']
        for field in optional_fields:
            if field in mapping and mapping[field] and mapping[field] not in available_columns:
                return False, f"La columna seleccionada para '{field}' no existe en el archivo"
        
        return True, None
    
    @staticmethod
    def import_ventas(file_path: str, mapping: Dict[str, str], empresa_id: int, 
                     usuario: str) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Importa las ventas desde el archivo usando el mapeo de columnas
        
        Args:
            file_path: Ruta del archivo
            mapping: Diccionario con el mapeo de columnas
            empresa_id: ID de la empresa
            usuario: Nombre del usuario que realiza la importación
            
        Returns:
            Tuple con (success, result_summary, error_message)
        """
        try:
            # Leer archivo
            success, df, error = ImportacionVentaService.read_file(file_path)
            if not success:
                return False, None, error
            
            # Validar mapeo
            is_valid, validation_error = ImportacionVentaService.validate_mapping(mapping, df.columns.tolist())
            if not is_valid:
                return False, None, validation_error
            
            # Variables para estadísticas
            registros_importados = 0
            errores = 0
            duplicados = 0
            errores_detalle = []
            
            # Procesar cada fila
            for index, row in df.iterrows():
                try:
                    # Extraer valores según el mapeo
                    fecha_str = row.get(mapping['fecha'], '')
                    producto = row.get(mapping['producto'], '')
                    cantidad = row.get(mapping['cantidad'], 0)
                    total = row.get(mapping['total'], 0)
                    
                    # Validar campos obligatorios
                    if pd.isna(cantidad) or pd.isna(total):
                        errores += 1
                        errores_detalle.append(f"Fila {index + 2}: Cantidad o total inválido o vacío")
                        continue
                    
                    # Convertir a float y validar
                    try:
                        cantidad = float(cantidad)
                        total = float(total)
                    except (ValueError, TypeError):
                        errores += 1
                        errores_detalle.append(f"Fila {index + 2}: Cantidad o total no es numérico (Cant: {cantidad}, Total: {total})")
                        continue
                    
                    if cantidad <= 0 or total <= 0:
                        errores += 1
                        errores_detalle.append(f"Fila {index + 2}: Cantidad o total debe ser mayor a 0")
                        continue
                    
                    # Convertir fecha
                    try:
                        if pd.isna(fecha_str) or str(fecha_str).strip() == '' or str(fecha_str).lower() in ['nan', 'none']:
                            fecha = datetime.utcnow()
                        else:
                            # Intentar diferentes formatos de fecha (formato chileno día-mes-año)
                            fecha = pd.to_datetime(str(fecha_str), errors='coerce', dayfirst=True)
                            if pd.isna(fecha):
                                fecha = datetime.utcnow()
                    except Exception as e:
                        fecha = datetime.utcnow()
                    
                    # Obtener valores opcionales
                    metodo_pago = row.get(mapping.get('metodo_pago', ''), 'Efectivo')
                    categoria = row.get(mapping.get('categoria', ''), 'General')
                    
                    if pd.isna(metodo_pago) or str(metodo_pago).strip() == '':
                        metodo_pago = 'Efectivo'
                    if pd.isna(categoria) or str(categoria).strip() == '':
                        categoria = 'General'
                    
                    # Crear movimiento (gasto por venta)
                    movimiento = Movimiento(
                        descripcion=f"Venta: {str(producto)}",
                        monto=total,
                        tipo='gasto',
                        fecha=fecha,
                        categoria_id=None,  # Se puede asignar después si existe lógica de categorías
                        empresa_id=empresa_id,
                        metodo_pago=str(metodo_pago),
                        rubro_id=None  # Se puede asignar después si existe lógica de rubros
                    )
                    
                    db.session.add(movimiento)
                    registros_importados += 1
                    
                except Exception as e:
                    errores += 1
                    errores_detalle.append(f"Fila {index + 2}: Error inesperado - {str(e)}")
                    continue
            
            # Crear registro de importación
            importacion = ImportacionVenta(
                archivo=os.path.basename(file_path),
                fecha=datetime.utcnow(),
                registros_importados=registros_importados,
                errores=errores,
                duplicados=duplicados,
                usuario=usuario,
                estado='completado' if errores == 0 else 'parcial',
                errores_detalle='\n'.join(errores_detalle[:50]) if errores_detalle else None,  # Limitar a 50 errores
                empresa_id=empresa_id
            )
            
            db.session.add(importacion)
            db.session.commit()
            
            # Crear notificación automática de importación
            NotificationService.create_import_notification(
                empresa_id=empresa_id,
                registros=registros_importados,
                errores=errores,
                archivo=os.path.basename(file_path),
                user_id=None
            )
            
            # Resumen de la importación
            result = {
                'registros_importados': registros_importados,
                'errores': errores,
                'duplicados': duplicados,
                'estado': importacion.estado,
                'importacion_id': importacion.id
            }
            
            return True, result, None
            
        except Exception as e:
            db.session.rollback()
            return False, None, f"Error durante la importación: {str(e)}"
    
    @staticmethod
    def get_import_history(empresa_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Obtiene el historial de importaciones de una empresa
        
        Args:
            empresa_id: ID de la empresa
            limit: Límite de registros a retornar
            
        Returns:
            Lista de diccionarios con el historial de importaciones
        """
        importaciones = ImportacionVenta.query.filter_by(
            empresa_id=empresa_id
        ).order_by(
            ImportacionVenta.fecha.desc()
        ).limit(limit).all()
        
        return [imp.to_dict() for imp in importaciones]
    
    @staticmethod
    def get_import_by_id(importacion_id: int, empresa_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtiene una importación específica por ID
        
        Args:
            importacion_id: ID de la importación
            empresa_id: ID de la empresa (para validación)
            
        Returns:
            Diccionario con los datos de la importación o None si no existe
        """
        importacion = ImportacionVenta.query.filter_by(
            id=importacion_id,
            empresa_id=empresa_id
        ).first()
        
        return importacion.to_dict() if importacion else None
