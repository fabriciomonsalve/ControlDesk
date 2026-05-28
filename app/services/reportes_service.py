"""
Servicio para generar reportes financieros
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from flask import current_app
from sqlalchemy import func, extract
from io import BytesIO
from base64 import b64decode
from app import db
from app.models.movimiento import Movimiento
from app.models.rubro import Rubro
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.lib.colors import HexColor


class ReportesService:
    """Servicio para generar reportes y análisis financieros"""
    
    @staticmethod
    def get_ganancias_por_rubro(fecha_desde: str = None, fecha_hasta: str = None, empresa_id: int = None) -> List[Dict[str, Any]]:
        """
        Calcula ganancias por rubro en un rango de fechas
        Args:
            fecha_desde: Fecha inicial (YYYY-MM-DD)
            fecha_hasta: Fecha final (YYYY-MM-DD)
            empresa_id: ID de la empresa para filtrar
        Returns:
            Lista de diccionarios con datos de ganancias por rubro
        """
        try:
            # Obtener rubros filtrados por empresa si se proporciona
            rubros_query = db.session.query(Rubro.id, Rubro.nombre)
            if empresa_id:
                rubros_query = rubros_query.filter(Rubro.empresa_id == empresa_id)
            todos_rubros = rubros_query.all()
            
            # Construir query base para ingresos con filtros de fecha y empresa
            ingresos_subquery = db.session.query(
                Movimiento.rubro_id,
                func.sum(Movimiento.monto).label('ingresos')
            ).filter(Movimiento.tipo == 'ingreso')
            
            # Aplicar filtro de empresa a ingresos
            if empresa_id:
                ingresos_subquery = ingresos_subquery.filter(Movimiento.empresa_id == empresa_id)
            
            # Aplicar filtros de fecha a ingresos
            if fecha_desde:
                fecha_desde_dt = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
                ingresos_subquery = ingresos_subquery.filter(Movimiento.fecha >= fecha_desde_dt)
            if fecha_hasta:
                fecha_hasta_dt = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
                ingresos_subquery = ingresos_subquery.filter(Movimiento.fecha <= fecha_hasta_dt)
            
            ingresos_subquery = ingresos_subquery.group_by(Movimiento.rubro_id).subquery()
            
            # Construir query base para gastos con filtros de fecha
            gastos_subquery = db.session.query(
                Movimiento.rubro_id,
                func.sum(Movimiento.monto).label('gastos')
            ).filter(Movimiento.tipo == 'gasto')
            
            # Aplicar filtros de fecha a gastos
            if fecha_desde:
                fecha_desde_dt = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
                gastos_subquery = gastos_subquery.filter(Movimiento.fecha >= fecha_desde_dt)
            if fecha_hasta:
                fecha_hasta_dt = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
                gastos_subquery = gastos_subquery.filter(Movimiento.fecha <= fecha_hasta_dt)
            
            gastos_subquery = gastos_subquery.group_by(Movimiento.rubro_id).subquery()
            
            # LEFT JOIN con subqueries
            ingresos_query = db.session.query(
                Rubro.id,
                func.coalesce(ingresos_subquery.c.ingresos, 0).label('ingresos')
            ).outerjoin(ingresos_subquery, Rubro.id == ingresos_subquery.c.rubro_id)
            
            gastos_query = db.session.query(
                Rubro.id,
                func.coalesce(gastos_subquery.c.gastos, 0).label('gastos')
            ).outerjoin(gastos_subquery, Rubro.id == gastos_subquery.c.rubro_id)
            
            # Ejecutar queries
            ingresos_data = {row.id: float(row.ingresos) for row in ingresos_query.all()}
            gastos_data = {row.id: float(row.gastos) for row in gastos_query.all()}
            
            # Combinar datos y calcular ganancias para TODOS los rubros
            resultados = []
            for rubro in todos_rubros:
                ingresos = ingresos_data.get(rubro.id, 0)
                gastos = gastos_data.get(rubro.id, 0)
                ganancia = max(0, ingresos - gastos)
                
                resultados.append({
                    'id': rubro.id,
                    'nombre': rubro.nombre,
                    'ingresos': ingresos,
                    'gastos': gastos,
                    'ganancia': ganancia
                })
            
            # Ordenar por ganancia descendente
            resultados.sort(key=lambda x: x['ganancia'], reverse=True)
            
            return resultados
            
        except Exception as e:
            current_app.logger.error(f"Error calculando ganancias por rubro: {str(e)}")
            return []
    
    @staticmethod
    def get_tendencia_mensual(meses: int = 12, empresa_id: int = None) -> List[Dict[str, Any]]:
        """
        Genera tendencia mensual de ingresos, gastos y ganancias
        Args:
            meses: Número de meses hacia atrás (default: 12)
            empresa_id: ID de la empresa para filtrar
        Returns:
            Lista de diccionarios con datos mensuales
        """
        try:
            # Calcular fecha de inicio
            fecha_fin = datetime.now()
            fecha_inicio = fecha_fin - timedelta(days=meses * 30)
            
            # Query para obtener datos mensuales
            datos_mensuales = db.session.query(
                extract('year', Movimiento.fecha).label('anio'),
                extract('month', Movimiento.fecha).label('mes'),
                Movimiento.tipo,
                func.sum(Movimiento.monto).label('total')
            ).filter(
                Movimiento.fecha >= fecha_inicio,
                Movimiento.fecha <= fecha_fin
            )
            
            # Aplicar filtro de empresa
            if empresa_id:
                datos_mensuales = datos_mensuales.filter(Movimiento.empresa_id == empresa_id).group_by(
                extract('year', Movimiento.fecha),
                extract('month', Movimiento.fecha),
                Movimiento.tipo
            ).order_by(
                extract('year', Movimiento.fecha),
                extract('month', Movimiento.fecha)
            ).all()
            
            # Organizar datos por mes
            datos_por_mes = {}
            for row in datos_mensuales:
                mes_key = f"{int(row.anio)}-{int(row.mes):02d}"
                if mes_key not in datos_por_mes:
                    datos_por_mes[mes_key] = {'ingresos': 0, 'gastos': 0}
                
                if row.tipo == 'ingreso':
                    datos_por_mes[mes_key]['ingresos'] = float(row.total)
                else:
                    datos_por_mes[mes_key]['gastos'] = float(row.total)
            
            # Generar lista completa de meses con datos
            resultados = []
            fecha_actual = fecha_inicio
            while fecha_actual <= fecha_fin:
                mes_key = f"{fecha_actual.year}-{fecha_actual.month:02d}"
                datos_mes = datos_por_mes.get(mes_key, {'ingresos': 0, 'gastos': 0})

                ingresos = datos_mes['ingresos']
                gastos = datos_mes['gastos']
                ganancia = max(0, ingresos - gastos)

                # Solo agregar mes si tiene datos (ingresos > 0 o gastos > 0)
                if ingresos > 0 or gastos > 0:
                    # Nombres de meses en español
                    meses_espanol = {
                        1: 'Ene', 2: 'Feb', 3: 'Mar', 4: 'Abr', 5: 'May', 6: 'Jun',
                        7: 'Jul', 8: 'Ago', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dic'
                    }
                    nombre_mes = f"{meses_espanol[fecha_actual.month]} {fecha_actual.year}"

                    resultados.append({
                        'mes': mes_key,
                        'nombre_mes': nombre_mes,
                        'ingresos': ingresos,
                        'gastos': gastos,
                        'ganancia': ganancia
                    })

                # Avanzar al siguiente mes
                if fecha_actual.month == 12:
                    fecha_actual = fecha_actual.replace(year=fecha_actual.year + 1, month=1)
                else:
                    fecha_actual = fecha_actual.replace(month=fecha_actual.month + 1)

            # Invertir orden para mostrar del mes actual hacia atrás
            return resultados[::-1]
            
        except Exception as e:
            current_app.logger.error(f"Error generando tendencia mensual: {str(e)}")
            return []
    
    @staticmethod
    def get_resumen_general(fecha_desde: str = None, fecha_hasta: str = None, empresa_id: int = None) -> Dict[str, Any]:
        """
        Genera resumen general de finanzas
        Args:
            fecha_desde: Fecha inicial (YYYY-MM-DD)
            fecha_hasta: Fecha final (YYYY-MM-DD)
            empresa_id: ID de la empresa para filtrar
        Returns:
            Diccionario con resumen financiero
        """
        try:
            # Query base para totales
            ingresos_query = db.session.query(func.coalesce(func.sum(Movimiento.monto), 0)).filter(
                Movimiento.tipo == 'ingreso'
            )
            
            gastos_query = db.session.query(func.coalesce(func.sum(Movimiento.monto), 0)).filter(
                Movimiento.tipo == 'gasto'
            )
            
            # Aplicar filtro de empresa
            if empresa_id:
                ingresos_query = ingresos_query.filter(Movimiento.empresa_id == empresa_id)
                gastos_query = gastos_query.filter(Movimiento.empresa_id == empresa_id)
            
            # Aplicar filtros de fecha
            if fecha_desde:
                fecha_desde_dt = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
                ingresos_query = ingresos_query.filter(Movimiento.fecha >= fecha_desde_dt)
                gastos_query = gastos_query.filter(Movimiento.fecha >= fecha_desde_dt)
            
            if fecha_hasta:
                fecha_hasta_dt = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
                ingresos_query = ingresos_query.filter(Movimiento.fecha <= fecha_hasta_dt)
                gastos_query = gastos_query.filter(Movimiento.fecha <= fecha_hasta_dt)
            
            # Ejecutar queries
            total_ingresos = float(ingresos_query.scalar() or 0)
            total_gastos = float(gastos_query.scalar() or 0)
            total_ganancia = max(0, total_ingresos - total_gastos)
            
            # Obtener número de transacciones
            transacciones_query = db.session.query(func.count(Movimiento.id))
            
            # Aplicar filtro de empresa
            if empresa_id:
                transacciones_query = transacciones_query.filter(Movimiento.empresa_id == empresa_id)
            
            if fecha_desde:
                transacciones_query = transacciones_query.filter(Movimiento.fecha >= fecha_desde_dt)
            if fecha_hasta:
                transacciones_query = transacciones_query.filter(Movimiento.fecha <= fecha_hasta_dt)
            
            total_transacciones = transacciones_query.scalar() or 0
            
            return {
                'total_ingresos': total_ingresos,
                'total_gastos': total_gastos,
                'total_ganancia': total_ganancia,
                'total_transacciones': total_transacciones,
                'promedio_transaccion': total_transacciones > 0 and (total_ingresos + total_gastos) / total_transacciones or 0
            }
            
        except Exception as e:
            current_app.logger.error(f"Error generando resumen general: {str(e)}")
            return {
                'total_ingresos': 0,
                'total_gastos': 0,
                'total_ganancia': 0,
                'total_transacciones': 0,
                'promedio_transaccion': 0
            }
    
    @staticmethod
    def generate_financial_report_pdf(
        resumen: Dict[str, Any],
        ganancias_por_rubro: List[Dict[str, Any]],
        tendencia_mensual: List[Dict[str, Any]],
        chart_images: Dict[str, str],
        fecha_desde: str = None,
        fecha_hasta: str = None,
        incluir_portada: bool = True
    ) -> BytesIO:
        """
        Genera un reporte financiero profesional en PDF
        
        Args:
            resumen: Diccionario con resumen financiero
            ganancias_por_rubro: Lista de ganancias por rubro
            tendencia_mensual: Lista de tendencia mensual
            chart_images: Diccionario con imágenes de gráficos en base64
            fecha_desde: Fecha inicial del filtro
            fecha_hasta: Fecha final del filtro
            incluir_portada: Si incluir portada opcional
            
        Returns:
            BytesIO con el PDF generado
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        # Estilos
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=HexColor('#1e40af'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=HexColor('#1e40af'),
            spaceAfter=12,
            spaceBefore=20
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=6
        )
        
        bold_style = ParagraphStyle(
            'CustomBold',
            parent=styles['Normal'],
            fontSize=10,
            fontName='Helvetica-Bold',
            spaceAfter=6
        )
        
        # Contenedor de elementos
        elements = []
        
        # Portada opcional
        if incluir_portada:
            elements.append(Spacer(1, 2*inch))
            elements.append(Paragraph("ControlDESK", title_style))
            elements.append(Spacer(1, 0.5*inch))
            elements.append(Paragraph("Reporte Financiero", ParagraphStyle(
                'Subtitle',
                parent=styles['Heading2'],
                fontSize=20,
                textColor=HexColor('#64748b'),
                alignment=TA_CENTER,
                spaceAfter=30
            )))
            elements.append(Spacer(1, 1*inch))
            
            # Fecha de generación
            fecha_generacion = datetime.now().strftime('%d/%m/%Y %H:%M')
            elements.append(Paragraph(f"<b>Fecha de generación:</b> {fecha_generacion}", ParagraphStyle(
                'CoverDate',
                parent=styles['Normal'],
                fontSize=12,
                alignment=TA_CENTER,
                spaceAfter=10
            )))
            
            # Rango de fechas
            if fecha_desde and fecha_hasta:
                elements.append(Paragraph(f"<b>Período:</b> {fecha_desde} a {fecha_hasta}", ParagraphStyle(
                    'CoverPeriod',
                    parent=styles['Normal'],
                    fontSize=12,
                    alignment=TA_CENTER,
                    spaceAfter=10
                )))
            elif fecha_desde:
                elements.append(Paragraph(f"<b>Desde:</b> {fecha_desde}", ParagraphStyle(
                    'CoverPeriod',
                    parent=styles['Normal'],
                    fontSize=12,
                    alignment=TA_CENTER,
                    spaceAfter=10
                )))
            elif fecha_hasta:
                elements.append(Paragraph(f"<b>Hasta:</b> {fecha_hasta}", ParagraphStyle(
                    'CoverPeriod',
                    parent=styles['Normal'],
                    fontSize=12,
                    alignment=TA_CENTER,
                    spaceAfter=10
                )))
            
            elements.append(Spacer(1, 2*inch))
            elements.append(PageBreak())
        
        # Encabezado del reporte
        elements.append(Paragraph("Reporte Financiero", title_style))
        
        # Información del reporte
        fecha_generacion = datetime.now().strftime('%d/%m/%Y %H:%M')
        elements.append(Paragraph(f"<b>Generado:</b> {fecha_generacion}", normal_style))
        
        if fecha_desde and fecha_hasta:
            elements.append(Paragraph(f"<b>Período:</b> {fecha_desde} a {fecha_hasta}", normal_style))
        elif fecha_desde:
            elements.append(Paragraph(f"<b>Desde:</b> {fecha_desde}", normal_style))
        elif fecha_hasta:
            elements.append(Paragraph(f"<b>Hasta:</b> {fecha_hasta}", normal_style))
        
        elements.append(Spacer(1, 0.3*inch))
        
        # Separador
        elements.append(Table([['']], colWidths=[6*inch], style=TableStyle([
            ('LINEABOVE', (0, 0), (0, 0), 2, HexColor('#3b82f6')),
        ])))
        elements.append(Spacer(1, 0.3*inch))
        
        # Resumen Financiero
        elements.append(Paragraph("Resumen Financiero", heading_style))
        
        # Crear cards de resumen
        resumen_data = [
            ['Métrica', 'Valor'],
            ['Total Ingresos', f"$ {resumen.get('total_ingresos', 0):,.0f}".replace(',', '.')],
            ['Total Gastos', f"$ {resumen.get('total_gastos', 0):,.0f}".replace(',', '.')],
            ['Ganancia Neta', f"$ {resumen.get('total_ganancia', 0):,.0f}".replace(',', '.')],
            ['Total Transacciones', f"{resumen.get('total_transacciones', 0):,}"],
            ['Promedio por Transacción', f"$ {resumen.get('promedio_transaccion', 0):,.0f}".replace(',', '.')],
        ]
        
        resumen_table = Table(resumen_data, colWidths=[2.5*inch, 3*inch])
        resumen_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (1, 0), HexColor('#3b82f6')),
            ('TEXTCOLOR', (0, 0), (1, 0), colors.white),
            ('FONTNAME', (0, 0), (1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (1, 0), 12),
            ('BACKGROUND', (0, 1), (0, -1), HexColor('#f1f5f9')),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, HexColor('#cbd5e1')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, HexColor('#f8fafc')]),
        ]))
        
        elements.append(resumen_table)
        elements.append(Spacer(1, 0.4*inch))
        
        # Insight destacado
        if ganancias_por_rubro:
            top_rubro = ganancias_por_rubro[0]
            if top_rubro['ganancia'] > 0:
                insight_text = f"<b>Insight destacado:</b> {top_rubro['nombre']} lidera las ganancias con $ {top_rubro['ganancia']:,.0f}".replace(',', '.')
                elements.append(Paragraph(insight_text, ParagraphStyle(
                    'Insight',
                    parent=styles['Normal'],
                    fontSize=11,
                    textColor=HexColor('#059669'),
                    spaceAfter=20
                )))
        
        # Gráfico de ganancias por rubro
        if chart_images.get('ganancias_chart'):
            elements.append(Paragraph("Ganancias por Rubro", heading_style))
            try:
                img_data = b64decode(chart_images['ganancias_chart'].split(',')[1])
                img = BytesIO(img_data)
                chart_img = Image(img, width=6*inch, height=3*inch)
                elements.append(chart_img)
                elements.append(Spacer(1, 0.3*inch))
            except Exception as e:
                current_app.logger.error(f"Error insertando gráfico de ganancias: {e}")
        
        # Tabla detallada por rubro
        if ganancias_por_rubro:
            elements.append(Paragraph("Detalle por Rubro", heading_style))
            
            rubro_data = [['Rubro', 'Ingresos', 'Gastos', 'Ganancia']]
            for rubro in ganancias_por_rubro:
                rubro_data.append([
                    rubro['nombre'],
                    f"$ {rubro['ingresos']:,.0f}".replace(',', '.'),
                    f"$ {rubro['gastos']:,.0f}".replace(',', '.'),
                    f"$ {rubro['ganancia']:,.0f}".replace(',', '.')
                ])
            
            rubro_table = Table(rubro_data, colWidths=[2*inch, 1.5*inch, 1.5*inch, 1.5*inch])
            rubro_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), HexColor('#3b82f6')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, HexColor('#cbd5e1')),
                ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, HexColor('#f8fafc')]),
            ]))
            
            elements.append(rubro_table)
            elements.append(Spacer(1, 0.4*inch))
        
        # Footer con fecha
        elements.append(Spacer(1, 0.5*inch))
        elements.append(Table([['']], colWidths=[6*inch], style=TableStyle([
            ('LINEABOVE', (0, 0), (0, 0), 1, HexColor('#cbd5e1')),
        ])))
        elements.append(Spacer(1, 0.1*inch))
        elements.append(Paragraph(f"Reporte generado por ControlDesk - {fecha_generacion}", ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=8,
            textColor=HexColor('#64748b'),
            alignment=TA_CENTER
        )))
        
        # Generar PDF
        doc.build(elements)
        buffer.seek(0)
        return buffer
