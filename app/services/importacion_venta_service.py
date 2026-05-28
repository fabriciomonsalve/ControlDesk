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
        'monto': ['monto', 'total', 'total_neto', 'importe', 'subtotal', 'total_venta', 'precio', 'valor', 'amount'],
        'fecha': ['fecha', 'fecha venta', 'date', 'fecha_venta', 'fec_venta', 'fec'],
        'descripcion': ['descripcion', 'descripción', 'producto', 'detalle', 'item', 'concepto', 'nombre_producto', 'desc']
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
            'monto': None,
            'fecha': None,
            'descripcion': None
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
        # Solo el monto es obligatorio
        if 'monto' not in mapping or not mapping['monto']:
            return False, "Debe seleccionar la columna que contiene el monto"
        
        if mapping['monto'] not in available_columns:
            return False, "La columna seleccionada para 'monto' no existe en el archivo"
        
        # Validar campos opcionales si fueron proporcionados
        optional_fields = ['fecha', 'descripcion']
        for field in optional_fields:
            if field in mapping and mapping[field] and mapping[field] not in available_columns:
                return False, f"La columna seleccionada para '{field}' no existe en el archivo"
        
        return True, None
    
    @staticmethod
    def import_ventas(file_path: str, mapping: Dict[str, str], empresa_id: int,
                     usuario: str, tipo: str = 'ingreso', rubro_id: int = None,
                     categoria_id: int = None) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Importa los registros desde el archivo usando el mapeo de columnas.
        Todos los registros se crean como Movimientos del tipo, rubro y categoría seleccionados.
        
        Args:
            file_path: Ruta del archivo
            mapping: Diccionario con el mapeo de columnas ({'monto': 'col', 'fecha': 'col', 'descripcion': 'col'})
            empresa_id: ID de la empresa
            usuario: Nombre del usuario que realiza la importación
            tipo: 'ingreso' o 'gasto'
            rubro_id: ID del rubro a asignar a todos los movimientos
            categoria_id: ID de la categoría a asignar a todos los movimientos
            
        Returns:
            Tuple con (success, result_summary, error_message)
        """
        try:
            # Validar tipo
            if tipo not in ['ingreso', 'gasto']:
                return False, None, "El tipo debe ser 'ingreso' o 'gasto'"
            
            # Validar rubro y categoría (requeridos por el modelo Movimiento)
            if not rubro_id:
                return False, None, "Debe seleccionar un rubro"
            if not categoria_id:
                return False, None, "Debe seleccionar una categoría"
            
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
            total_acumulado = 0.0
            errores_detalle = []
            
            col_monto = mapping['monto']
            col_fecha = mapping.get('fecha') or None
            col_descripcion = mapping.get('descripcion') or None
            
            # Procesar cada fila
            for index, row in df.iterrows():
                try:
                    monto_raw = row.get(col_monto, None)
                    
                    # Validar monto
                    if pd.isna(monto_raw):
                        errores += 1
                        errores_detalle.append(f"Fila {index + 2}: Monto vacío")
                        continue
                    
                    # Limpiar monto (quitar símbolos de moneda, separadores de miles)
                    monto_str = str(monto_raw).strip()
                    monto_str = monto_str.replace('$', '').replace('CLP', '').replace(' ', '')
                    # Si tiene tanto . como , asumir formato es.CL: . miles , decimales
                    if ',' in monto_str and '.' in monto_str:
                        monto_str = monto_str.replace('.', '').replace(',', '.')
                    elif ',' in monto_str:
                        monto_str = monto_str.replace(',', '.')
                    
                    try:
                        monto = float(monto_str)
                    except (ValueError, TypeError):
                        errores += 1
                        errores_detalle.append(f"Fila {index + 2}: Monto no es numérico ({monto_raw})")
                        continue
                    
                    if monto <= 0:
                        errores += 1
                        errores_detalle.append(f"Fila {index + 2}: Monto debe ser mayor a 0")
                        continue
                    
                    # Procesar fecha
                    fecha = datetime.utcnow().date()
                    if col_fecha:
                        fecha_raw = row.get(col_fecha, None)
                        if not pd.isna(fecha_raw) and str(fecha_raw).strip() not in ('', 'nan', 'none', 'None'):
                            try:
                                parsed = pd.to_datetime(str(fecha_raw), errors='coerce', dayfirst=True)
                                if not pd.isna(parsed):
                                    fecha = parsed.date()
                            except Exception:
                                pass
                    
                    # Procesar descripción
                    descripcion = None
                    if col_descripcion:
                        desc_raw = row.get(col_descripcion, None)
                        if not pd.isna(desc_raw) and str(desc_raw).strip() not in ('', 'nan'):
                            descripcion = str(desc_raw).strip()[:500]
                    if not descripcion:
                        descripcion = f"Importación masiva - Fila {index + 2}"
                    
                    # Crear movimiento
                    movimiento = Movimiento(
                        descripcion=descripcion,
                        monto=monto,
                        tipo=tipo,
                        fecha=fecha,
                        categoria_id=categoria_id,
                        rubro_id=rubro_id,
                        empresa_id=empresa_id
                    )
                    
                    db.session.add(movimiento)
                    registros_importados += 1
                    total_acumulado += monto
                    
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
                errores_detalle='\n'.join(errores_detalle[:50]) if errores_detalle else None,
                empresa_id=empresa_id
            )
            
            db.session.add(importacion)
            db.session.commit()
            
            # Crear notificación automática de importación
            try:
                NotificationService.create_import_notification(
                    empresa_id=empresa_id,
                    registros=registros_importados,
                    errores=errores,
                    archivo=os.path.basename(file_path),
                    user_id=None
                )
            except Exception:
                pass
            
            # Resumen de la importación
            result = {
                'registros_importados': registros_importados,
                'errores': errores,
                'duplicados': duplicados,
                'total_acumulado': round(total_acumulado, 2),
                'tipo': tipo,
                'estado': importacion.estado,
                'importacion_id': importacion.id,
                'errores_detalle': errores_detalle[:20]
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
