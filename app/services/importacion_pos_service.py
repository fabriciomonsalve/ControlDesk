import pandas as pd
from datetime import datetime, date
from io import BytesIO
from werkzeug.utils import secure_filename
import os
from app import db
from app.models.corte_pos import CortePOS, DetalleCortePOS
from app.models.ganancia_rubro import GananciaRubro
from app.models.movimiento import Movimiento
from app.models.rubro import Rubro
from app.models.categoria import Categoria
from app.models.empresa import Empresa


class ImportacionPOSService:
    """Servicio para importar cortes del sistema POS Abarrotes"""
    
    ALLOWED_EXTENSIONS = {'xls'}
    REQUIRED_COLUMNS = ['Codigo', 'Descripcion', 'Cantidad', 'Precio Usado', 'Precio Costo', 'Departamento']
    
    @staticmethod
    def allowed_file(filename):
        """Verifica si el archivo tiene la extensión permitida"""
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ImportacionPOSService.ALLOWED_EXTENSIONS
    
    @staticmethod
    def leer_archivo_pos(file_content):
        """
        Lee el archivo exportado por Abarrotes POS
        El archivo es TSV (tab-separated) con extensión .xls
        """
        try:
            # Leer como CSV con separador de tabulación
            df = pd.read_csv(BytesIO(file_content), sep='\t', encoding='latin1')
            
            # Validar columnas requeridas
            columnas_requeridas = ['Codigo', 'Descripcion', 'Cantidad', 'Precio Usado', 'Precio Costo', 'Departamento']
            columnas_faltantes = [col for col in columnas_requeridas if col not in df.columns]
            
            if columnas_faltantes:
                raise ValueError(f"Columnas faltantes: {', '.join(columnas_faltantes)}")
            
            # Limpiar datos
            df = ImportacionPOSService._limpiar_datos(df)
            
            return df
            
        except Exception as e:
            raise ValueError(f"Error al leer el archivo: {str(e)}")
    
    @staticmethod
    def _limpiar_datos(df):
        """Limpia y normaliza los datos del archivo"""
        # Eliminar filas vacías
        df = df.dropna(how='all')
        
        # Limpiar símbolos de moneda y comas de las columnas numéricas
        columnas_numericas = ['Precio Usado', 'Precio Costo', 'Cantidad']
        for col in columnas_numericas:
            if col in df.columns:
                df[col] = df[col].astype(str).str.replace('$', '', regex=False)
                df[col] = df[col].astype(str).str.replace(',', '', regex=False)
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        return df
    
    @staticmethod
    def calcular_totales(df):
        """
        Calcula los totales del corte
        """
        # Calcular ventas totales
        df['venta_total'] = df['Precio Usado'] * df['Cantidad']
        ventas_totales = float(df['venta_total'].sum())
        
        # Calcular costo total
        df['costo_total'] = df['Precio Costo'] * df['Cantidad']
        costos_totales = float(df['costo_total'].sum())
        
        # Calcular ganancia por producto
        df['ganancia'] = df['venta_total'] - df['costo_total']
        ganancias_totales = float(df['ganancia'].sum())
        
        # Calcular cantidad total de productos
        cantidad_productos = int(df['Cantidad'].sum())
        
        # Obtener departamentos únicos
        departamentos = df['Departamento'].unique().tolist()
        
        return {
            'ventas_totales': ventas_totales,
            'costos_totales': costos_totales,
            'ganancias_totales': ganancias_totales,
            'cantidad_productos': cantidad_productos,
            'departamentos': departamentos,
            'df': df
        }
    
    @staticmethod
    def validar_archivo_duplicado(empresa_id, fecha):
        """
        Verifica si ya existe un corte para la misma fecha y empresa
        """
        corte_existente = CortePOS.query.filter_by(
            empresa_id=empresa_id,
            fecha=fecha
        ).first()
        
        return corte_existente is not None
    
    @staticmethod
    def guardar_corte_pos(empresa_id, fecha, totales, df, nombre_archivo):
        """
        Guarda el corte POS y sus detalles en la base de datos
        """
        try:
            # Crear el corte POS
            corte = CortePOS(
                empresa_id=empresa_id,
                fecha=fecha,
                ventas_totales=totales['ventas_totales'],
                costos_totales=totales['costos_totales'],
                ganancias_totales=totales['ganancias_totales'],
                archivo_original=nombre_archivo
            )
            
            db.session.add(corte)
            db.session.flush()  # Para obtener el ID del corte
            
            # Guardar detalles del corte
            for _, row in df.iterrows():
                detalle = DetalleCortePOS(
                    corte_id=corte.id,
                    producto=row['Descripcion'],
                    cantidad=int(row['Cantidad']),
                    precio_venta=row['Precio Usado'],
                    precio_costo=row['Precio Costo'],
                    ganancia=row['ganancia'],
                    departamento=row['Departamento']
                )
                db.session.add(detalle)
            
            db.session.commit()
            return corte
            
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Error al guardar el corte: {str(e)}")
    
    @staticmethod
    def registrar_movimiento_financiero(empresa_id, fecha, ventas_totales, rubro_id, categoria_id):
        """
        Registra el movimiento financiero automático
        """
        try:
            movimiento = Movimiento(
                tipo='ingreso',
                monto=ventas_totales,
                fecha=fecha,
                descripcion='Ventas importadas desde Abarrotes',
                rubro_id=rubro_id,
                categoria_id=categoria_id,
                empresa_id=empresa_id
            )
            
            db.session.add(movimiento)
            db.session.commit()
            return movimiento
            
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Error al registrar movimiento: {str(e)}")
    
    @staticmethod
    def registrar_ganancia_rubro(empresa_id, rubro_id, fecha, ventas, costos, ganancias):
        """
        Registra las ganancias del rubro
        """
        try:
            ganancia_rubro = GananciaRubro(
                rubro_id=rubro_id,
                fecha=fecha,
                ventas=ventas,
                costos=costos,
                ganancias=ganancias,
                origen='Abarrotes POS',
                empresa_id=empresa_id
            )
            
            db.session.add(ganancia_rubro)
            db.session.commit()
            return ganancia_rubro
            
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Error al registrar ganancia: {str(e)}")
    
    @staticmethod
    def obtener_rubro_ferreteria(empresa_id):
        """
        Obtiene o crea el rubro "Ferretería" para la empresa
        """
        rubro = Rubro.query.filter_by(
            nombre='Ferretería',
            empresa_id=empresa_id
        ).first()
        
        if not rubro:
            rubro = Rubro(
                nombre='Ferretería',
                color='#2563eb',
                empresa_id=empresa_id
            )
            db.session.add(rubro)
            db.session.commit()
        
        return rubro
    
    @staticmethod
    def obtener_categoria_ventas_pos(empresa_id):
        """
        Obtiene o crea la categoría "Ventas POS" para la empresa
        """
        categoria = Categoria.query.filter_by(
            nombre='Ventas POS',
            empresa_id=empresa_id
        ).first()
        
        if not categoria:
            categoria = Categoria(
                nombre='Ventas POS',
                descripcion='Ventas importadas desde sistema POS',
                estado='activa',
                icono='fa-cash-register',
                color='#10b981',
                empresa_id=empresa_id
            )
            db.session.add(categoria)
            db.session.commit()
        
        return categoria
    
    @staticmethod
    def procesar_importacion_completa(empresa_id, fecha, file_content, nombre_archivo):
        """
        Procesa la importación completa del archivo POS
        """
        try:
            # Paso 1: Leer el archivo
            df = ImportacionPOSService.leer_archivo_pos(file_content)
            
            # Paso 2: Calcular totales
            totales = ImportacionPOSService.calcular_totales(df)
            
            # Paso 3: Obtener o crear rubro y categoría
            rubro = ImportacionPOSService.obtener_rubro_ferreteria(empresa_id)
            categoria = ImportacionPOSService.obtener_categoria_ventas_pos(empresa_id)
            
            # Paso 4: Validar duplicados y actualizar o registrar nuevo corte
            corte_existente = CortePOS.query.filter_by(
                empresa_id=empresa_id,
                fecha=fecha
            ).first()
            
            if corte_existente:
                # Actualizar corte POS existente
                corte_existente.ventas_totales = totales['ventas_totales']
                corte_existente.costos_totales = totales['costos_totales']
                corte_existente.ganancias_totales = totales['ganancias_totales']
                corte_existente.archivo_original = nombre_archivo
                corte_existente.fecha_importacion = datetime.utcnow()
                
                # Limpiar detalles anteriores (delete-orphan de SQLAlchemy los elimina físicamente)
                corte_existente.detalles.clear()
                
                # Guardar nuevos detalles asociados al corte
                for _, row in df.iterrows():
                    detalle = DetalleCortePOS(
                        producto=row['Descripcion'],
                        cantidad=int(row['Cantidad']),
                        precio_venta=row['Precio Usado'],
                        precio_costo=row['Precio Costo'],
                        ganancia=row['ganancia'],
                        departamento=row['Departamento']
                    )
                    corte_existente.detalles.append(detalle)
                
                # Buscar y actualizar o crear movimiento financiero
                movimiento = Movimiento.query.filter_by(
                    empresa_id=empresa_id,
                    fecha=fecha,
                    descripcion='Ventas importadas desde Abarrotes',
                    tipo='ingreso'
                ).first()
                
                if movimiento:
                    movimiento.monto = totales['ventas_totales']
                    movimiento.rubro_id = rubro.id
                    movimiento.categoria_id = categoria.id
                else:
                    movimiento = Movimiento(
                        tipo='ingreso',
                        monto=totales['ventas_totales'],
                        fecha=fecha,
                        descripcion='Ventas importadas desde Abarrotes',
                        rubro_id=rubro.id,
                        categoria_id=categoria.id,
                        empresa_id=empresa_id
                    )
                    db.session.add(movimiento)
                
                # Buscar y actualizar o crear ganancia_rubro
                ganancia = GananciaRubro.query.filter_by(
                    empresa_id=empresa_id,
                    rubro_id=rubro.id,
                    fecha=fecha,
                    origen='Abarrotes POS'
                ).first()
                
                if ganancia:
                    ganancia.ventas = totales['ventas_totales']
                    ganancia.costos = totales['costos_totales']
                    ganancia.ganancias = totales['ganancias_totales']
                else:
                    ganancia = GananciaRubro(
                        rubro_id=rubro.id,
                        fecha=fecha,
                        ventas=totales['ventas_totales'],
                        costos=totales['costos_totales'],
                        ganancias=totales['ganancias_totales'],
                        origen='Abarrotes POS',
                        empresa_id=empresa_id
                    )
                    db.session.add(ganancia)
                
                db.session.commit()
                corte = corte_existente
            else:
                # Guardar corte POS nuevo
                corte = ImportacionPOSService.guardar_corte_pos(
                    empresa_id, fecha, totales, df, nombre_archivo
                )
                
                # Registrar movimiento financiero nuevo
                movimiento = ImportacionPOSService.registrar_movimiento_financiero(
                    empresa_id, fecha, totales['ventas_totales'], rubro.id, categoria.id
                )
                
                # Registrar ganancias del rubro nuevas
                ganancia = ImportacionPOSService.registrar_ganancia_rubro(
                    empresa_id, rubro.id, fecha,
                    totales['ventas_totales'],
                    totales['costos_totales'],
                    totales['ganancias_totales']
                )
            
            return {
                'success': True,
                'corte': corte.to_dict(),
                'movimiento': movimiento.to_dict(),
                'ganancia': ganancia.to_dict(),
                'totales': {
                    'ventas_totales': totales['ventas_totales'],
                    'costos_totales': totales['costos_totales'],
                    'ganancias_totales': totales['ganancias_totales'],
                    'cantidad_productos': totales['cantidad_productos'],
                    'departamentos': totales['departamentos']
                }
            }
            
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def obtener_historial_cortes(empresa_id, limit=50):
        """
        Obtiene el historial de cortes POS de una empresa
        """
        cortes = CortePOS.query.filter_by(
            empresa_id=empresa_id
        ).order_by(CortePOS.fecha.desc()).limit(limit).all()
        
        return [corte.to_dict() for corte in cortes]
    
    @staticmethod
    def obtener_detalle_corte(corte_id, empresa_id):
        """
        Obtiene los detalles de un corte específico
        """
        corte = CortePOS.query.filter_by(
            id=corte_id,
            empresa_id=empresa_id
        ).first()
        
        if not corte:
            return None
        
        detalles = DetalleCortePOS.query.filter_by(
            corte_id=corte_id
        ).all()
        
        return {
            'corte': corte.to_dict(),
            'detalles': [detalle.to_dict() for detalle in detalles]
        }
    
    @staticmethod
    def obtener_ganancias_acumuladas(rubro_id, empresa_id, fecha_inicio=None, fecha_fin=None):
        """
        Obtiene las ganancias acumuladas de un rubro
        """
        query = GananciaRubro.query.filter_by(
            rubro_id=rubro_id,
            empresa_id=empresa_id
        )
        
        if fecha_inicio:
            query = query.filter(GananciaRubro.fecha >= fecha_inicio)
        
        if fecha_fin:
            query = query.filter(GananciaRubro.fecha <= fecha_fin)
        
        ganancias = query.order_by(GananciaRubro.fecha.desc()).all()
        
        return [ganancia.to_dict() for ganancia in ganancias]
    
    @staticmethod
    def obtener_resumen_ganancias(rubro_id, empresa_id):
        """
        Obtiene un resumen de ganancias acumuladas
        """
        ganancias = ImportacionPOSService.obtener_ganancias_acumuladas(rubro_id, empresa_id)
        
        ventas_total = sum(g['ventas'] for g in ganancias)
        costos_total = sum(g['costos'] for g in ganancias)
        ganancias_total = sum(g['ganancias'] for g in ganancias)
        
        return {
            'ventas_total': ventas_total,
            'costos_total': costos_total,
            'ganancias_total': ganancias_total,
            'cantidad_cortes': len(ganancias),
            'ganancias': ganancias
        }
    
    @staticmethod
    def obtener_datos_acumulados(empresa_id, fecha_inicio=None, fecha_fin=None, departamento=None):
        """
        Obtiene datos acumulados de todas las importaciones POS con filtros
        Args:
            empresa_id: ID de la empresa
            fecha_inicio: Fecha inicial (YYYY-MM-DD) opcional
            fecha_fin: Fecha final (YYYY-MM-DD) opcional
            departamento: Filtro por departamento opcional
        Returns:
            Diccionario con datos acumulados y lista de cortes
        """
        try:
            # Query base para cortes
            query = CortePOS.query.filter_by(empresa_id=empresa_id)
            
            # Aplicar filtro de fechas
            if fecha_inicio:
                fecha_inicio_dt = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
                query = query.filter(CortePOS.fecha >= fecha_inicio_dt)
            if fecha_fin:
                fecha_fin_dt = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
                query = query.filter(CortePOS.fecha <= fecha_fin_dt)
            
            cortes = query.order_by(CortePOS.fecha.desc()).all()
            
            if not cortes:
                return {
                    'ventas_totales': 0,
                    'costos_totales': 0,
                    'ganancias_totales': 0,
                    'cantidad_productos': 0,
                    'cantidad_cortes': 0,
                    'departamentos': [],
                    'cortes': []
                }
            
            # Obtener detalles de todos los cortes
            detalles_totales = []
            departamentos_set = set()
            
            for corte in cortes:
                detalles_query = DetalleCortePOS.query.filter_by(corte_id=corte.id)
                
                # Aplicar filtro por departamento si se proporciona
                if departamento:
                    detalles_query = detalles_query.filter(
                        DetalleCortePOS.departamento == departamento
                    )
                
                detalles = detalles_query.all()
                
                for detalle in detalles:
                    detalles_totales.append({
                        'producto': detalle.producto,
                        'cantidad': detalle.cantidad,
                        'precio_venta': float(detalle.precio_venta),
                        'precio_costo': float(detalle.precio_costo),
                        'ganancia': float(detalle.ganancia),
                        'departamento': detalle.departamento,
                        'fecha_corte': corte.fecha.isoformat()
                    })
                    
                    if detalle.departamento:
                        departamentos_set.add(detalle.departamento)
            
            # Calcular totales acumulados
            ventas_totales = sum(d['precio_venta'] * d['cantidad'] for d in detalles_totales)
            costos_totales = sum(d['precio_costo'] * d['cantidad'] for d in detalles_totales)
            ganancias_totales = sum(d['ganancia'] for d in detalles_totales)
            cantidad_productos = sum(d['cantidad'] for d in detalles_totales)
            
            # Obtener departamentos únicos ordenados
            departamentos = sorted(list(departamentos_set))
            
            return {
                'ventas_totales': ventas_totales,
                'costos_totales': costos_totales,
                'ganancias_totales': ganancias_totales,
                'cantidad_productos': cantidad_productos,
                'cantidad_cortes': len(cortes),
                'departamentos': departamentos,
                'cortes': [corte.to_dict() for corte in cortes],
                'detalles': detalles_totales[:10]  # Primeros 10 detalles
            }
            
        except Exception as e:
            raise Exception(f"Error obteniendo datos acumulados: {str(e)}")
