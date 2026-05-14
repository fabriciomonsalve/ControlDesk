"""
Servicio para manejar datos del dashboard
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any
from flask import current_app
from app import db
from app.models.movimiento import Movimiento
from app.models.rubro import Rubro
from app.utils.formatters import format_clp

class DashboardService:
    
    @staticmethod
    def get_dashboard_data(mes_filter=None):
        """
        Obtiene datos reales del dashboard desde la base de datos
        Args:
            mes_filter: Opcional. Número del mes para filtrar (1-12)
        """
        try:
            # Obtener todos los rubros
            rubros = Rubro.query.all()
            
            if not rubros:
                print("No hay rubros en la base de datos")
                return DashboardService.get_simulated_data()
            
            # Calcular datos por rubro
            rubros_data = []
            total_ingresos = 0
            total_gastos = 0
            
            for rubro in rubros:
                # Usar consultas más seguras y específicas
                ingresos_query = db.session.query(db.func.sum(Movimiento.monto)).filter(
                    Movimiento.rubro_id == rubro.id,
                    Movimiento.tipo == 'ingreso'
                )
                
                gastos_query = db.session.query(db.func.sum(Movimiento.monto)).filter(
                    Movimiento.rubro_id == rubro.id,
                    Movimiento.tipo == 'gasto'
                )
                
                # Aplicar filtro de mes si se proporciona
                if mes_filter:
                    ingresos_query = ingresos_query.filter(db.extract('month', Movimiento.fecha) == mes_filter)
                    gastos_query = gastos_query.filter(db.extract('month', Movimiento.fecha) == mes_filter)
                
                ingresos = ingresos_query.scalar() or 0
                gastos = gastos_query.scalar() or 0
                
                ganancia = max(0, float(ingresos) - float(gastos))
                
                rubros_data.append({
                    'id': rubro.id,
                    'nombre': rubro.nombre,
                    'ingresos': float(ingresos),
                    'gastos': float(gastos),
                    'ganancia': ganancia
                })
                
                total_ingresos += float(ingresos)
                total_gastos += float(gastos)
            
            total_balance = total_ingresos - total_gastos
            
            # Datos para gráficos (pasar objetos rubro, no datos procesados)
            chart_data = DashboardService._get_chart_data(rubros_data)
            
            return {
                'rubros_data': rubros_data,
                'total_ingresos': total_ingresos,
                'total_gastos': total_gastos,
                'total_balance': total_balance,
                'chart_data': chart_data,
                'has_real_data': True
            }
            
        except Exception as e:
            print(f"Error obteniendo datos reales: {e}")
            import traceback
            traceback.print_exc()
            return DashboardService.get_simulated_data()
    
    @staticmethod
    def get_simulated_data():
        """
        Obtiene datos simulados para el dashboard
        """
        rubros_data = [
            {
                'id': 1,
                'nombre': 'Ferretería',
                'ingresos': 15000.00,
                'gastos': 8500.00,
                'ganancia': 6500.00
            },
            {
                'id': 2,
                'nombre': 'Apicultura',
                'ingresos': 8500.00,
                'gastos': 3200.00,
                'ganancia': 5300.00
            },
            {
                'id': 3,
                'nombre': 'Agricultura',
                'ingresos': 12000.00,
                'gastos': 7800.00,
                'ganancia': max(0, 4200.00)
            }
        ]
        
        total_ingresos = sum(rubro['ingresos'] for rubro in rubros_data)
        total_gastos = sum(rubro['gastos'] for rubro in rubros_data)
        total_balance = total_ingresos - total_gastos
        
        chart_data = DashboardService._get_chart_data(rubros_data)
        
        return {
            'rubros_data': rubros_data,
            'total_ingresos': total_ingresos,
            'total_gastos': total_gastos,
            'total_balance': total_balance,
            'chart_data': chart_data,
            'has_real_data': False
        }
    
    @staticmethod
    def _get_chart_data(rubros_data):
        """
        Genera datos para los gráficos Chart.js
        """
        # Datos para gráfico de ganancias por rubro (bar chart)
        ganancias_labels = [rubro['nombre'] for rubro in rubros_data]
        ganancias_data = [round(rubro['ganancia'], 2) for rubro in rubros_data]
        ganancias_formatted = [format_clp(rubro['ganancia']) for rubro in rubros_data]
        
        # Datos para gráfico de gastos (pie chart)
        gastos_labels = [rubro['nombre'] for rubro in rubros_data]
        gastos_data = [rubro['gastos'] for rubro in rubros_data]
        gastos_formatted = [format_clp(rubro['gastos']) for rubro in rubros_data]
        
        # Colores para los gráficos
        colors = [
            'rgba(59, 130, 246, 0.8)',   # Blue
            'rgba(16, 185, 129, 0.8)',   # Green
            'rgba(251, 146, 60, 0.8)',   # Orange
            'rgba(147, 51, 234, 0.8)',   # Purple
            'rgba(236, 72, 153, 0.8)',   # Pink
            'rgba(250, 204, 21, 0.8)',   # Yellow
        ]
        
        # Colores con bordes para el pie chart
        pie_colors = [
            'rgba(59, 130, 246, 0.8)',
            'rgba(16, 185, 129, 0.8)',
            'rgba(251, 146, 60, 0.8)',
        ]
        
        pie_border_colors = [
            'rgba(59, 130, 246, 1)',
            'rgba(16, 185, 129, 1)',
            'rgba(251, 146, 60, 1)',
        ]
        
        return {
            'ganancias_chart': {
                'labels': ganancias_labels,
                'datasets': [{
                    'label': 'Ganancias',
                    'data': ganancias_data,
                    'formatted_data': ganancias_formatted,
                    'backgroundColor': colors[:len(ganancias_labels)],
                    'borderColor': colors[:len(ganancias_labels)],
                    'borderWidth': 2,
                    'borderRadius': 8
                }]
            },
            'gastos_chart': {
                'labels': gastos_labels,
                'datasets': [{
                    'data': gastos_data,
                    'formatted_data': gastos_formatted,
                    'backgroundColor': pie_colors,
                    'borderColor': pie_border_colors,
                    'borderWidth': 2
                }]
            },
            'ingresos_vs_gastos_chart': {
                'labels': ganancias_labels,
                'datasets': [
                    {
                        'label': 'Ingresos',
                        'data': [rubro['ingresos'] for rubro in rubros_data],
                        'formatted_data': [format_clp(rubro['ingresos']) for rubro in rubros_data],
                        'backgroundColor': 'rgba(16, 185, 129, 0.8)',
                        'borderColor': 'rgba(16, 185, 129, 1)',
                        'borderWidth': 2,
                        'borderRadius': 8
                    },
                    {
                        'label': 'Gastos',
                        'data': gastos_data,
                        'formatted_data': gastos_formatted,
                        'backgroundColor': 'rgba(239, 68, 68, 0.8)',
                        'borderColor': 'rgba(239, 68, 68, 1)',
                        'borderWidth': 2,
                        'borderRadius': 8
                    }
                ]
            }
        }
    
    @staticmethod
    def get_movimientos_recientes(limit=5):
        """
        Obtiene los movimientos más recientes
        """
        try:
            movimientos = Movimiento.query.order_by(Movimiento.created_at.desc()).limit(limit).all()
            return [movimiento.to_dict() for movimiento in movimientos]
        except:
            return []
    
    @staticmethod
    def get_estadisticas_mensuales(meses=6):
        """
        Obtiene estadísticas de los últimos meses
        """
        # Implementación futura para datos históricos
        return []
    
    @staticmethod
    def get_weekly_insights():
        """
        Obtiene datos para insights semanales
        """
        try:
            # Calcular el rango de la semana actual (lunes a domingo)
            today = datetime.now()
            monday = today - timedelta(days=today.weekday())
            sunday = monday + timedelta(days=6)
            
            # Formatear fechas para mostrar
            week_start = monday.strftime('%d/%m')
            week_end = sunday.strftime('%d/%m')
            
            print(f"Rango de semana: {monday.date()} a {sunday.date()}")
            
            # Obtener movimientos de la semana actual
            movimientos_semana = Movimiento.query.filter(
                Movimiento.fecha >= monday.date(),
                Movimiento.fecha <= sunday.date()
            ).all()
            
            print(f"Movimientos encontrados en la semana: {len(movimientos_semana)}")
            
            # Calcular totales de la semana
            total_ingresos_semana = sum(
                m.monto for m in movimientos_semana if m.tipo == 'ingreso'
            )
            total_gastos_semana = sum(
                m.monto for m in movimientos_semana if m.tipo == 'gasto'
            )
            
            print(f"Total ingresos semana: {total_ingresos_semana}")
            print(f"Total gastos semana: {total_gastos_semana}")
            
            # Calcular rubro líder de la semana
            rubros_semana = {}
            for m in movimientos_semana:
                if m.rubro_id not in rubros_semana:
                    rubros_semana[m.rubro_id] = {'ingresos': 0, 'gastos': 0, 'nombre': m.rubro.nombre}
                if m.tipo == 'ingreso':
                    rubros_semana[m.rubro_id]['ingresos'] += m.monto
                else:
                    rubros_semana[m.rubro_id]['gastos'] += m.monto
            
            # Encontrar rubro con mayor ganancia
            top_rubro = None
            max_ganancia = 0
            for rubro_id, data in rubros_semana.items():
                ganancia = data['ingresos'] - data['gastos']
                if ganancia > max_ganancia:
                    max_ganancia = ganancia
                    top_rubro = data['nombre']
            
            # Obtener datos de la semana anterior para comparación
            last_monday = monday - timedelta(days=7)
            last_sunday = sunday - timedelta(days=7)
            
            movimientos_semana_pasada = Movimiento.query.filter(
                Movimiento.fecha >= last_monday.date(),
                Movimiento.fecha <= last_sunday.date()
            ).all()
            
            total_ingresos_semana_pasada = sum(
                m.monto for m in movimientos_semana_pasada if m.tipo == 'ingreso'
            )
            
            # Calcular cambio porcentual
            cambio_porcentual = 0
            if total_ingresos_semana_pasada > 0:
                cambio_porcentual = ((total_ingresos_semana - total_ingresos_semana_pasada) / total_ingresos_semana_pasada) * 100
            
            # Calcular balance neto
            balance_neto = total_ingresos_semana - total_gastos_semana
            
            return {
                'week_start': week_start,
                'week_end': week_end,
                'total_ingresos': total_ingresos_semana,
                'total_gastos': total_gastos_semana,
                'balance_neto': balance_neto,
                'top_rubro': top_rubro,
                'max_ganancia': max_ganancia,
                'cambio_porcentual': cambio_porcentual,
                'has_data': len(movimientos_semana) > 0
            }
        except Exception as e:
            print(f"Error obteniendo insights semanales: {e}")
            import traceback
            traceback.print_exc()
            return {
                'week_start': '',
                'week_end': '',
                'total_ingresos': 0,
                'total_gastos': 0,
                'balance_neto': 0,
                'top_rubro': None,
                'max_ganancia': 0,
                'cambio_porcentual': 0,
                'has_data': False
            }
