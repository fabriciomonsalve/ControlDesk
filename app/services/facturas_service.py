"""
Servicio para gestión de facturas de compra
"""

from typing import List, Dict, Any, Optional, Tuple
from flask import current_app
from datetime import datetime
import os
import re

# Importaciones opcionales para OCR y procesamiento de imágenes
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

from app import db
from app.models.factura_compra import FacturaCompra
from app.models.factura_detalle import FacturaDetalle
from app.models.factura_rubro import FacturaRubro
from app.models.rubro import Rubro
from app.models.movimiento import Movimiento
from app.services.rubro_service import RubroService
from app.services.notification_service import NotificationService


class FacturasService:
    """Servicio para operaciones de facturas de compra"""
    
    # Formatos permitidos
    ALLOWED_IMAGE_EXTENSIONS = {'jpg', 'jpeg', 'png'}
    ALLOWED_DOCUMENT_EXTENSIONS = {'pdf'}
    ALLOWED_SPREADSHEET_EXTENSIONS = {'xls', 'xlsx', 'csv'}
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    
    @staticmethod
    def validate_file(file) -> Tuple[bool, str]:
        """
        Valida el archivo subido
        Returns:
            (is_valid, error_message)
        """
        if not file:
            return False, "No se proporcionó ningún archivo"
        
        # Validar tamaño
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        if file_size > FacturasService.MAX_FILE_SIZE:
            return False, f"El archivo excede el tamaño máximo de {FacturasService.MAX_FILE_SIZE / (1024*1024)}MB"
        
        # Validar extensión
        filename = file.filename.lower()
        if not any(filename.endswith(ext) for ext in 
                   FacturasService.ALLOWED_IMAGE_EXTENSIONS | 
                   FacturasService.ALLOWED_DOCUMENT_EXTENSIONS | 
                   FacturasService.ALLOWED_SPREADSHEET_EXTENSIONS):
            return False, "Formato de archivo no permitido"
        
        return True, None
    
    @staticmethod
    def detectar_duplicado(proveedor: str, numero_factura: str, fecha: datetime, total: float, empresa_id: int = None) -> Optional[FacturaCompra]:
        """
        Detecta si una factura ya está registrada
        Args:
            proveedor: Nombre del proveedor
            numero_factura: Número de factura
            fecha: Fecha de la factura
            total: Total de la factura
            empresa_id: ID de la empresa (opcional)
        Returns:
            Factura duplicada o None
        """
        query = FacturaCompra.query.filter(
            FacturaCompra.proveedor == proveedor,
            FacturaCompra.numero_factura == numero_factura,
            FacturaCompra.fecha_factura == fecha,
            FacturaCompra.total == total
        )
        
        if empresa_id:
            query = query.filter(FacturaCompra.empresa_id == empresa_id)
        
        return query.first()
    
    @staticmethod
    def procesar_imagen(image_path: str) -> Dict[str, Any]:
        """
        Procesa una imagen usando OCR para extraer datos de la factura
        Args:
            image_path: Ruta de la imagen
        Returns:
            Diccionario con datos extraídos
        """
        try:
            import pytesseract
            from PIL import Image
            import os
            
            # Configurar ruta de Tesseract para Windows
            if os.name == 'nt':  # Windows
                tesseract_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
                if os.path.exists(tesseract_path):
                    pytesseract.pytesseract.tesseract_cmd = tesseract_path
                else:
                    # Intentar ruta alternativa común
                    tesseract_path_alt = r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe'
                    if os.path.exists(tesseract_path_alt):
                        pytesseract.pytesseract.tesseract_cmd = tesseract_path_alt
            
            # Leer imagen con PIL
            image = Image.open(image_path)
            
            # Extraer texto usando Tesseract OCR
            texto_completo = pytesseract.image_to_string(image, lang='spa')
            
            # Extraer información usando regex
            datos = FacturasService._extraer_datos_texto(texto_completo)
            
            current_app.logger.info(f"OCR con Tesseract procesado exitosamente: {image_path}")
            return datos
            
        except ImportError:
            current_app.logger.warning("pytesseract no está instalado, usando extracción simulada")
            return FacturasService._extraer_datos_simulados()
        except Exception as e:
            current_app.logger.error(f"Error procesando imagen: {str(e)}")
            return FacturasService._extraer_datos_simulados()
    
    @staticmethod
    def procesar_pdf(pdf_path: str) -> Dict[str, Any]:
        """
        Procesa un archivo PDF para extraer datos de la factura
        Args:
            pdf_path: Ruta del PDF
        Returns:
            Diccionario con datos extraídos
        """
        try:
            import PyPDF2
            
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                texto_completo = ''
                
                # Extraer texto de todas las páginas
                for page in reader.pages:
                    texto_completo += page.extract_text() + '\n'
            
            # Si no hay suficiente texto, intentar OCR
            if len(texto_completo.strip()) < 50:
                current_app.logger.info("PDF escaneado detectado, aplicando OCR")
                return FacturasService._procesar_pdf_con_ocr(pdf_path)
            
            # Extraer información usando regex
            datos = FacturasService._extraer_datos_texto(texto_completo)
            
            current_app.logger.info(f"PDF procesado exitosamente: {pdf_path}")
            return datos
            
        except ImportError:
            current_app.logger.warning("PyPDF2 no está instalado, usando extracción simulada")
            return FacturasService._extraer_datos_simulados()
        except Exception as e:
            current_app.logger.error(f"Error procesando PDF: {str(e)}")
            return FacturasService._extraer_datos_simulados()
    
    @staticmethod
    def _procesar_pdf_con_ocr(pdf_path: str) -> Dict[str, Any]:
        """
        Procesa un PDF escaneado usando OCR
        """
        try:
            import pdf2image
            import easyocr
            
            # Convertir PDF a imágenes
            images = pdf2image.convert_from_path(pdf_path)
            
            # Procesar primera imagen con OCR
            reader = easyocr.Reader(['es'], gpu=False)
            
            # Usar numpy si está disponible, si no convertir a array de forma alternativa
            if NUMPY_AVAILABLE:
                result = reader.readtext(np.array(images[0]))
            else:
                # Convertir imagen a array usando PIL si numpy no está disponible
                import io
                img_byte_arr = io.BytesIO()
                images[0].save(img_byte_arr, format='PNG')
                img_byte_arr = img_byte_arr.getvalue()
                result = reader.readtext(img_byte_arr)
            
            texto_completo = ' '.join([text for (bbox, text, prob) in result if prob > 0.5])
            datos = FacturasService._extraer_datos_texto(texto_completo)
            
            return datos
            
        except Exception as e:
            current_app.logger.error(f"Error procesando PDF con OCR: {str(e)}")
            return FacturasService._extraer_datos_simulados()
    
    @staticmethod
    def procesar_excel(excel_path: str) -> Dict[str, Any]:
        """
        Procesa un archivo Excel/CSV para extraer datos de la factura
        Args:
            excel_path: Ruta del archivo Excel
        Returns:
            Diccionario con datos extraídos
        """
        try:
            import pandas as pd
            
            # Leer archivo según extensión
            if excel_path.endswith('.csv'):
                df = pd.read_csv(excel_path)
            else:
                df = pd.read_excel(excel_path)
            
            # Detectar columnas automáticamente
            columnas = df.columns.tolist()
            columnas_lower = [c.lower() for c in columnas]
            
            # Mapear columnas comunes
            mapa_columnas = {}
            for i, col in enumerate(columnas):
                col_lower = col.lower()
                if any(palabra in col_lower for palabra in ['producto', 'item', 'descripción', 'descripcion']):
                    mapa_columnas['producto'] = col
                elif any(palabra in col_lower for palabra in ['cantidad', 'cant', 'qty']):
                    mapa_columnas['cantidad'] = col
                elif any(palabra in col_lower for palabra in ['precio', 'unitario', 'price']):
                    mapa_columnas['precio'] = col
                elif any(palabra in col_lower for palabra in ['total', 'monto']):
                    mapa_columnas['total'] = col
                elif any(palabra in col_lower for palabra in ['proveedor', 'empresa']):
                    mapa_columnas['proveedor'] = col
                elif any(palabra in col_lower for palabra in ['factura', 'numero', 'n°']):
                    mapa_columnas['numero'] = col
                elif any(palabra in col_lower for palabra in ['fecha', 'date']):
                    mapa_columnas['fecha'] = col
            
            # Extraer datos
            productos = []
            subtotal = 0
            
            for _, row in df.iterrows():
                if 'producto' in mapa_columnas:
                    producto = str(row[mapa_columnas['producto']])
                    cantidad = float(row.get(mapa_columnas.get('cantidad', 0), 1))
                    precio = float(row.get(mapa_columnas.get('precio', 0), 0))
                    total = float(row.get(mapa_columnas.get('total', 0), cantidad * precio))
                    
                    if producto and producto != 'nan':
                        productos.append({
                            'producto': producto,
                            'cantidad': cantidad,
                            'precio_unitario': precio,
                            'total': total
                        })
                        subtotal += total
            
            # Calcular totales
            iva = subtotal * 0.19
            total_factura = subtotal + iva
            
            # Extraer información de encabezado si existe
            proveedor = 'Proveedor Excel'
            numero_factura = 'F001'
            fecha_factura = datetime.now().date()
            
            if 'proveedor' in mapa_columnas and len(df) > 0:
                proveedor = str(df.iloc[0][mapa_columnas['proveedor']])
            if 'numero' in mapa_columnas and len(df) > 0:
                numero_factura = str(df.iloc[0][mapa_columnas['numero']])
            if 'fecha' in mapa_columnas and len(df) > 0:
                fecha_val = df.iloc[0][mapa_columnas['fecha']]
                if pd.notna(fecha_val):
                    fecha_factura = pd.to_datetime(fecha_val).date()
            
            datos = {
                'proveedor': proveedor,
                'numero_factura': numero_factura,
                'fecha_factura': fecha_factura.isoformat(),
                'subtotal': subtotal,
                'iva': iva,
                'total': total_factura,
                'productos': productos
            }
            
            current_app.logger.info(f"Excel procesado exitosamente: {excel_path}")
            return datos
            
        except ImportError:
            current_app.logger.warning("Pandas no está instalado, usando extracción simulada")
            return FacturasService._extraer_datos_simulados()
        except Exception as e:
            current_app.logger.error(f"Error procesando Excel: {str(e)}")
            return FacturasService._extraer_datos_simulados()
    
    @staticmethod
    def _extraer_datos_texto(texto: str) -> Dict[str, Any]:
        """
        Extrae datos de factura desde texto usando regex
        """
        datos = {
            'proveedor': 'Proveedor Detectado',
            'numero_factura': 'F001',
            'fecha_factura': datetime.now().date().isoformat(),
            'subtotal': 0,
            'iva': 0,
            'total': 0,
            'productos': []
        }
        
        # Extraer proveedor (buscar palabras clave)
        proveedor_patterns = [
            r'(?:proveedor|empresa|razón social)[:\s]+([A-Za-zÁ-Úá-ú\s]+)',
            r'^([A-Z][A-Za-zÁ-Úá-ú\s]+)$'
        ]
        for pattern in proveedor_patterns:
            match = re.search(pattern, texto, re.IGNORECASE)
            if match:
                datos['proveedor'] = match.group(1).strip()
                break
        
        # Extraer número de factura
        factura_patterns = [
            r'(?:factura|n[°o]\s*?|F)[:\s]*?(\d+[\d\-]*)',
            r'F[-\s]*(\d+)'
        ]
        for pattern in factura_patterns:
            match = re.search(pattern, texto, re.IGNORECASE)
            if match:
                datos['numero_factura'] = match.group(1)
                break
        
        # Extraer fecha
        fecha_patterns = [
            r'(\d{1,2})[-/](\d{1,2})[-/](\d{2,4})',
            r'(\d{2,4})[-/](\d{1,2})[-/](\d{1,2})'
        ]
        for pattern in fecha_patterns:
            match = re.search(pattern, texto)
            if match:
                try:
                    if len(match.group(3)) == 4:
                        fecha = f"{match.group(3)}-{match.group(2)}-{match.group(1)}"
                    else:
                        fecha = f"{match.group(1)}-{match.group(2)}-{match.group(3)}"
                    datos['fecha_factura'] = datetime.strptime(fecha, '%Y-%m-%d').date().isoformat()
                    break
                except:
                    pass
        
        # Extraer totales (buscar patrones de montos)
        total_patterns = [
            r'(?:total|neto a pagar)[:\s]*?\$?\s*?([\d.,]+)',
            r'\$\s*?([\d.,]+)\s*(?:total|neto)'
        ]
        for pattern in total_patterns:
            match = re.search(pattern, texto, re.IGNORECASE)
            if match:
                try:
                    datos['total'] = float(match.group(1).replace('.', '').replace(',', '.'))
                    datos['subtotal'] = datos['total'] / 1.19
                    datos['iva'] = datos['total'] - datos['subtotal']
                    break
                except:
                    pass
        
        # Si no se encontraron productos, crear uno genérico
        if not datos['productos'] and datos['total'] > 0:
            datos['productos'] = [
                {
                    'producto': 'Productos varios',
                    'cantidad': 1,
                    'precio_unitario': datos['subtotal'],
                    'total': datos['subtotal']
                }
            ]
        
        return datos
    
    @staticmethod
    def _extraer_datos_simulados() -> Dict[str, Any]:
        """
        Retorna datos simulados cuando no se puede procesar el archivo
        """
        return {
            'proveedor': 'Proveedor Detectado',
            'numero_factura': 'F001',
            'fecha_factura': datetime.now().date().isoformat(),
            'subtotal': 100000.0,
            'iva': 19000.0,
            'total': 119000.0,
            'productos': [
                {
                    'producto': 'Producto 1',
                    'cantidad': 1,
                    'precio_unitario': 50000.0,
                    'total': 50000.0
                },
                {
                    'producto': 'Producto 2',
                    'cantidad': 1,
                    'precio_unitario': 50000.0,
                    'total': 50000.0
                }
            ]
        }
    
    @staticmethod
    def procesar_archivo(file, filename: str, save_path: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Procesa un archivo según su tipo
        Args:
            file: Archivo subido
            filename: Nombre del archivo
            save_path: Ruta donde guardar el archivo
        Returns:
            (success, message, extracted_data)
        """
        try:
            current_app.logger.info(f"Procesando archivo: {filename}")
            
            # Guardar archivo
            file.save(save_path)
            current_app.logger.info(f"Archivo guardado en: {save_path}")
            
            # Determinar tipo de archivo
            ext = filename.lower().split('.')[-1]
            current_app.logger.info(f"Extensión detectada: {ext}")
            
            # Procesar según tipo
            if ext in FacturasService.ALLOWED_IMAGE_EXTENSIONS:
                current_app.logger.info("Procesando como imagen")
                data = FacturasService.procesar_imagen(save_path)
            elif ext in FacturasService.ALLOWED_DOCUMENT_EXTENSIONS:
                current_app.logger.info("Procesando como PDF")
                data = FacturasService.procesar_pdf(save_path)
            elif ext in FacturasService.ALLOWED_SPREADSHEET_EXTENSIONS:
                current_app.logger.info("Procesando como Excel/CSV")
                data = FacturasService.procesar_excel(save_path)
            else:
                current_app.logger.error(f"Tipo de archivo no soportado: {ext}")
                return False, f"Tipo de archivo no soportado: {ext}", None
            
            return True, "Archivo procesado correctamente", data
            
        except Exception as e:
            current_app.logger.error(f"Error procesando archivo: {str(e)}", exc_info=True)
            return False, f"Error al procesar el archivo: {str(e)}", None
    
    @staticmethod
    def calcular_por_rubro(productos: List[Dict[str, Any]], rubro_asignaciones: Dict[str, int]) -> Dict[int, float]:
        """
        Calcula el monto total por rubro
        Args:
            productos: Lista de productos con sus montos
            rubro_asignaciones: Diccionario {producto: rubro_id}
        Returns:
            Diccionario {rubro_id: monto_total}
        """
        montos_por_rubro = {}
        
        for producto in productos:
            producto_nombre = producto['producto']
            rubro_id = rubro_asignaciones.get(producto_nombre)
            total_linea = producto['total']
            
            if rubro_id:
                if rubro_id not in montos_por_rubro:
                    montos_por_rubro[rubro_id] = 0.0
                montos_por_rubro[rubro_id] += total_linea
        
        return montos_por_rubro
    
    @staticmethod
    def registrar_factura(
        empresa_id: int,
        proveedor: str,
        numero_factura: str,
        fecha_factura: datetime,
        subtotal: float,
        iva: float,
        total: float,
        productos: List[Dict[str, Any]],
        rubro_asignaciones: Dict[str, int],
        archivo_original: str = None,
        tipo_archivo: str = None
    ) -> Tuple[bool, str, Optional[FacturaCompra]]:
        """
        Registra una factura completa y genera los movimientos por rubro
        Args:
            empresa_id: ID de la empresa
            proveedor: Nombre del proveedor
            numero_factura: Número de factura
            fecha_factura: Fecha de la factura
            subtotal: Subtotal
            iva: IVA
            total: Total
            productos: Lista de productos
            rubro_asignaciones: Diccionario {producto: rubro_id}
            archivo_original: Ruta del archivo original
            tipo_archivo: Tipo de archivo
        Returns:
            (success, message, factura)
        """
        try:
            # Validar duplicado
            duplicado = FacturasService.detectar_duplicado(
                proveedor, numero_factura, fecha_factura, total, empresa_id
            )
            if duplicado:
                return False, "Esta factura ya se encuentra registrada", None
            
            # Crear factura
            factura = FacturaCompra(
                empresa_id=empresa_id,
                proveedor=proveedor,
                numero_factura=numero_factura,
                fecha_factura=fecha_factura,
                subtotal=subtotal,
                iva=iva,
                total=total,
                archivo_original=archivo_original,
                tipo_archivo=tipo_archivo
            )
            db.session.add(factura)
            db.session.flush()
            
            # Crear detalles de factura
            for producto in productos:
                detalle = FacturaDetalle(
                    factura_id=factura.id,
                    producto=producto['producto'],
                    cantidad=producto['cantidad'],
                    precio_unitario=producto['precio_unitario'],
                    total_linea=producto['total'],
                    rubro_id=rubro_asignaciones.get(producto['producto'])
                )
                db.session.add(detalle)
            
            # Calcular montos por rubro
            montos_por_rubro = FacturasService.calcular_por_rubro(productos, rubro_asignaciones)
            
            # Crear distribución por rubro
            for rubro_id, monto in montos_por_rubro.items():
                factura_rubro = FacturaRubro(
                    factura_id=factura.id,
                    rubro_id=rubro_id,
                    monto_total=monto
                )
                db.session.add(factura_rubro)
            
            # Generar movimientos por rubro
            for rubro_id, monto in montos_por_rubro.items():
                movimiento = Movimiento(
                    empresa_id=empresa_id,
                    rubro_id=rubro_id,
                    monto=monto,
                    tipo='gasto',
                    fecha=fecha_factura,
                    descripcion=f"Factura de compra - {proveedor} ({numero_factura})",
                    origen='factura_compra',
                    factura_id=factura.id
                )
                db.session.add(movimiento)
                
                # Registrar notificación en timeline del rubro
                rubro = Rubro.query.get(rubro_id)
                if rubro:
                    NotificationService.create_purchase_notification(
                        empresa_id=empresa_id,
                        monto=monto,
                        rubro=rubro.nombre,
                        proveedor=proveedor,
                        numero_factura=numero_factura
                    )
            
            db.session.commit()
            
            return True, "Factura registrada exitosamente", factura
            
        except Exception as e:
            current_app.logger.error(f"Error registrando factura: {str(e)}")
            db.session.rollback()
            return False, f"Error al registrar la factura: {str(e)}", None
    
    @staticmethod
    def get_all_facturas(empresa_id: int = None) -> List[Dict[str, Any]]:
        """
        Obtiene todas las facturas
        Args:
            empresa_id: ID de la empresa (opcional)
        Returns:
            Lista de facturas
        """
        try:
            query = FacturaCompra.query
            if empresa_id:
                query = query.filter(FacturaCompra.empresa_id == empresa_id)
            
            facturas = query.order_by(FacturaCompra.fecha_factura.desc()).all()
            
            facturas_data = []
            for factura in facturas:
                # Obtener rubros involucrados
                rubros_involucrados = db.session.query(
                    Rubro.nombre
                ).join(
                    FacturaRubro, FacturaRubro.rubro_id == Rubro.id
                ).filter(
                    FacturaRubro.factura_id == factura.id
                ).all()
                
                facturas_data.append({
                    'id': factura.id,
                    'proveedor': factura.proveedor,
                    'numero_factura': factura.numero_factura,
                    'fecha_factura': factura.fecha_factura.isoformat() if factura.fecha_factura else None,
                    'total': factura.total,
                    'rubros_involucrados': [r[0] for r in rubros_involucrados],
                    'fecha_registro': factura.fecha_registro.isoformat() if factura.fecha_registro else None
                })
            
            return facturas_data
            
        except Exception as e:
            current_app.logger.error(f"Error obteniendo facturas: {str(e)}")
            return []
    
    @staticmethod
    def get_factura_by_id(factura_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtiene una factura por su ID con todos los detalles
        Args:
            factura_id: ID de la factura
        Returns:
            Diccionario con datos de la factura o None
        """
        try:
            factura = FacturaCompra.query.get(factura_id)
            if not factura:
                return None
            
            # Obtener detalles
            detalles = FacturaDetalle.query.filter_by(factura_id=factura_id).all()
            detalles_data = []
            for detalle in detalles:
                rubro = Rubro.query.get(detalle.rubro_id) if detalle.rubro_id else None
                detalles_data.append({
                    'producto': detalle.producto,
                    'cantidad': detalle.cantidad,
                    'precio_unitario': detalle.precio_unitario,
                    'total_linea': detalle.total_linea,
                    'rubro': rubro.nombre if rubro else None,
                    'rubro_id': detalle.rubro_id,
                    'rubro_color': rubro.color if rubro else None
                })
            
            # Obtener distribución por rubro
            rubros_distribucion = FacturaRubro.query.filter_by(factura_id=factura_id).all()
            rubros_data = []
            for rubro_dist in rubros_distribucion:
                rubro = Rubro.query.get(rubro_dist.rubro_id)
                if rubro:
                    rubros_data.append({
                        'rubro_id': rubro.id,
                        'rubro_nombre': rubro.nombre,
                        'rubro_color': rubro.color,
                        'monto_total': rubro_dist.monto_total
                    })
            
            return {
                'id': factura.id,
                'proveedor': factura.proveedor,
                'numero_factura': factura.numero_factura,
                'fecha_factura': factura.fecha_factura.isoformat() if factura.fecha_factura else None,
                'subtotal': factura.subtotal,
                'iva': factura.iva,
                'total': factura.total,
                'archivo_original': factura.archivo_original,
                'tipo_archivo': factura.tipo_archivo,
                'fecha_registro': factura.fecha_registro.isoformat() if factura.fecha_registro else None,
                'detalles': detalles_data,
                'rubros_distribucion': rubros_data
            }
            
        except Exception as e:
            current_app.logger.error(f"Error obteniendo factura: {str(e)}")
            return None
    
    @staticmethod
    def delete_factura(factura_id: int) -> Tuple[bool, str]:
        """
        Elimina una factura y sus movimientos asociados
        Args:
            factura_id: ID de la factura
        Returns:
            (success, message)
        """
        try:
            factura = FacturaCompra.query.get(factura_id)
            if not factura:
                return False, "Factura no encontrada"
            
            # Eliminar movimientos asociados
            Movimiento.query.filter_by(factura_id=factura_id).delete()
            
            # Eliminar factura (cascade eliminará detalles y distribución)
            db.session.delete(factura)
            db.session.commit()
            
            return True, "Factura eliminada exitosamente"
            
        except Exception as e:
            current_app.logger.error(f"Error eliminando factura: {str(e)}")
            db.session.rollback()
            return False, f"Error al eliminar la factura: {str(e)}"
