from app.models.movimiento import Movimiento
from app.models.rubro import Rubro
from app.models.notification import Notification
from app.services.notification_service import NotificationService
from datetime import datetime, timedelta
from sqlalchemy import func, and_


class FinancialInsightsService:
    """Servicio para generar insights financieros inteligentes"""
    
    @staticmethod
    def detectar_perdidas(empresa_id: int, dias: int = 7) -> dict:
        """
        Detecta pérdidas en un período determinado
        
        Args:
            empresa_id: ID de la empresa
            dias: Número de días a analizar
            
        Returns:
            Diccionario con información sobre pérdidas
        """
        fecha_inicio = datetime.utcnow() - timedelta(days=dias)
        
        # Obtener movimientos del período
        movimientos = Movimiento.query.filter(
            Movimiento.empresa_id == empresa_id,
            Movimiento.fecha >= fecha_inicio
        ).all()
        
        perdidas_dias = []
        total_perdidas = 0
        
        for i in range(dias):
            fecha = datetime.utcnow() - timedelta(days=i)
            movimientos_dia = [m for m in movimientos if m.fecha.date() == fecha.date()]
            
            ingresos_dia = sum(m.monto for m in movimientos_dia if m.tipo == 'ingreso')
            gastos_dia = sum(m.monto for m in movimientos_dia if m.tipo == 'gasto')
            
            if gastos_dia > ingresos_dia:
                perdida = gastos_dia - ingresos_dia
                perdidas_dias.append({
                    'fecha': fecha.date(),
                    'perdida': perdida
                })
                total_perdidas += perdida
        
        return {
            'tiene_perdidas': len(perdidas_dias) > 0,
            'dias_con_perdidas': len(perdidas_dias),
            'perdidas_detalles': perdidas_dias,
            'total_perdidas': total_perdidas
        }
    
    @staticmethod
    def detectar_crecimiento(empresa_id: int, dias: int = 7) -> dict:
        """
        Detecta crecimiento o decrecimiento comparando períodos
        
        Args:
            empresa_id: ID de la empresa
            dias: Número de días a analizar
            
        Returns:
            Diccionario con información sobre crecimiento
        """
        fecha_fin_actual = datetime.utcnow()
        fecha_inicio_actual = fecha_fin_actual - timedelta(days=dias)
        
        fecha_fin_anterior = fecha_inicio_actual - timedelta(days=1)
        fecha_inicio_anterior = fecha_fin_anterior - timedelta(days=dias)
        
        # Período actual
        movimientos_actual = Movimiento.query.filter(
            Movimiento.empresa_id == empresa_id,
            Movimiento.fecha >= fecha_inicio_actual,
            Movimiento.fecha <= fecha_fin_actual
        ).all()
        
        ingresos_actual = sum(m.monto for m in movimientos_actual if m.tipo == 'ingreso')
        gastos_actual = sum(m.monto for m in movimientos_actual if m.tipo == 'gasto')
        ganancia_actual = ingresos_actual - gastos_actual
        
        # Período anterior
        movimientos_anterior = Movimiento.query.filter(
            Movimiento.empresa_id == empresa_id,
            Movimiento.fecha >= fecha_inicio_anterior,
            Movimiento.fecha <= fecha_fin_anterior
        ).all()
        
        ingresos_anterior = sum(m.monto for m in movimientos_anterior if m.tipo == 'ingreso')
        gastos_anterior = sum(m.monto for m in movimientos_anterior if m.tipo == 'gasto')
        ganancia_anterior = ingresos_anterior - gastos_anterior
        
        # Cálculo de variaciones
        variacion_ingresos = ((ingresos_actual - ingresos_anterior) / ingresos_anterior * 100) if ingresos_anterior > 0 else 0
        variacion_gastos = ((gastos_actual - gastos_anterior) / gastos_anterior * 100) if gastos_anterior > 0 else 0
        variacion_ganancia = ((ganancia_actual - ganancia_anterior) / ganancia_anterior * 100) if ganancia_anterior != 0 else 0
        
        return {
            'ingresos_actual': ingresos_actual,
            'ingresos_anterior': ingresos_anterior,
            'variacion_ingresos': variacion_ingresos,
            'gastos_actual': gastos_actual,
            'gastos_anterior': gastos_anterior,
            'variacion_gastos': variacion_gastos,
            'ganancia_actual': ganancia_actual,
            'ganancia_anterior': ganancia_anterior,
            'variacion_ganancia': variacion_ganancia,
            'es_crecimiento': variacion_ganancia > 0
        }
    
    @staticmethod
    def obtener_rubro_top(empresa_id: int, dias: int = 7) -> dict:
        """
        Obtiene el rubro con mayores ingresos
        
        Args:
            empresa_id: ID de la empresa
            dias: Número de días a analizar
            
        Returns:
            Diccionario con información del rubro top
        """
        fecha_inicio = datetime.utcnow() - timedelta(days=dias)
        
        # Obtener movimientos de ingresos por rubro
        movimientos = Movimiento.query.filter(
            Movimiento.empresa_id == empresa_id,
            Movimiento.tipo == 'ingreso',
            Movimiento.fecha >= fecha_inicio
        ).all()
        
        # Agrupar por rubro
        rubros_ingresos = {}
        total_ingresos = 0
        
        for mov in movimientos:
            if mov.rubro_id:
                rubro_nombre = mov.rubro.nombre if mov.rubro else 'Sin rubro'
                rubros_ingresos[rubro_nombre] = rubros_ingresos.get(rubro_nombre, 0) + mov.monto
                total_ingresos += mov.monto
        
        if not rubros_ingresos:
            return {
                'rubro_nombre': None,
                'ingresos': 0,
                'porcentaje': 0
            }
        
        # Encontrar rubro top
        rubro_top_nombre = max(rubros_ingresos, key=rubros_ingresos.get)
        rubro_top_ingresos = rubros_ingresos[rubro_top_nombre]
        porcentaje = (rubro_top_ingresos / total_ingresos * 100) if total_ingresos > 0 else 0
        
        return {
            'rubro_nombre': rubro_top_nombre,
            'ingresos': rubro_top_ingresos,
            'porcentaje': porcentaje
        }
    
    @staticmethod
    def obtener_rubro_menos_rentable(empresa_id: int, dias: int = 7) -> dict:
        """
        Obtiene el rubro menos rentable
        
        Args:
            empresa_id: ID de la empresa
            dias: Número de días a analizar
            
        Returns:
            Diccionario con información del rubro menos rentable
        """
        fecha_inicio = datetime.utcnow() - timedelta(days=dias)
        
        movimientos = Movimiento.query.filter(
            Movimiento.empresa_id == empresa_id,
            Movimiento.fecha >= fecha_inicio
        ).all()
        
        # Calcular ganancia por rubro
        rubros_ganancia = {}
        
        for mov in movimientos:
            if mov.rubro_id:
                rubro_nombre = mov.rubro.nombre if mov.rubro else 'Sin rubro'
                
                if rubro_nombre not in rubros_ganancia:
                    rubros_ganancia[rubro_nombre] = {'ingresos': 0, 'gastos': 0}
                
                if mov.tipo == 'ingreso':
                    rubros_ganancia[rubro_nombre]['ingresos'] += mov.monto
                elif mov.tipo == 'gasto':
                    rubros_ganancia[rubro_nombre]['gastos'] += mov.monto
        
        # Calcular ganancia neta por rubro
        rubros_rentabilidad = {}
        for rubro, datos in rubros_ganancia.items():
            ganancia = datos['ingresos'] - datos['gastos']
            rubros_rentabilidad[rubro] = ganancia
        
        if not rubros_rentabilidad:
            return {
                'rubro_nombre': None,
                'ganancia': 0
            }
        
        rubro_menos_rentable = min(rubros_rentabilidad, key=rubros_rentabilidad.get)
        
        return {
            'rubro_nombre': rubro_menos_rentable,
            'ganancia': rubros_rentabilidad[rubro_menos_rentable]
        }
    
    @staticmethod
    def calcular_ticket_promedio(empresa_id: int, dias: int = 7) -> dict:
        """
        Calcula el ticket promedio
        
        Args:
            empresa_id: ID de la empresa
            dias: Número de días a analizar
            
        Returns:
            Diccionario con información del ticket promedio
        """
        fecha_inicio = datetime.utcnow() - timedelta(days=dias)
        fecha_fin_anterior = fecha_inicio - timedelta(days=1)
        fecha_inicio_anterior = fecha_fin_anterior - timedelta(days=dias)
        
        # Período actual
        movimientos_actual = Movimiento.query.filter(
            Movimiento.empresa_id == empresa_id,
            Movimiento.tipo == 'ingreso',
            Movimiento.fecha >= fecha_inicio
        ).all()
        
        ticket_promedio_actual = (sum(m.monto for m in movimientos_actual) / len(movimientos_actual)) if movimientos_actual else 0
        
        # Período anterior
        movimientos_anterior = Movimiento.query.filter(
            Movimiento.empresa_id == empresa_id,
            Movimiento.tipo == 'ingreso',
            Movimiento.fecha >= fecha_inicio_anterior,
            Movimiento.fecha <= fecha_fin_anterior
        ).all()
        
        ticket_promedio_anterior = (sum(m.monto for m in movimientos_anterior) / len(movimientos_anterior)) if movimientos_anterior else 0
        
        # Variación
        variacion = ((ticket_promedio_actual - ticket_promedio_anterior) / ticket_promedio_anterior * 100) if ticket_promedio_anterior > 0 else 0
        
        return {
            'ticket_promedio': ticket_promedio_actual,
            'ticket_promedio_anterior': ticket_promedio_anterior,
            'variacion_porcentaje': variacion,
            'num_ventas_actual': len(movimientos_actual),
            'num_ventas_anterior': len(movimientos_anterior)
        }
    
    @staticmethod
    def detectar_caida_ventas(empresa_id: int, dias: int = 7, umbral: float = 20.0) -> dict:
        """
        Detecta caídas significativas en ventas
        
        Args:
            empresa_id: ID de la empresa
            dias: Número de días a analizar
            umbral: Porcentaje de caída considerado significativo
            
        Returns:
            Diccionario con información sobre caídas de ventas
        """
        crecimiento = FinancialInsightsService.detectar_crecimiento(empresa_id, dias)
        
        tiene_caida = crecimiento['variacion_ingresos'] < -umbral
        
        return {
            'tiene_caida': tiene_caida,
            'variacion_porcentaje': crecimiento['variacion_ingresos'],
            'umbral': umbral,
            'ingresos_actual': crecimiento['ingresos_actual'],
            'ingresos_anterior': crecimiento['ingresos_anterior']
        }
    
    @staticmethod
    def analizar_por_rubro(empresa_id: int, dias: int = 7) -> list:
        """
        Realiza análisis detallado por rubro
        
        Args:
            empresa_id: ID de la empresa
            dias: Número de días a analizar
            
        Returns:
            Lista con análisis de cada rubro
        """
        fecha_inicio = datetime.utcnow() - timedelta(days=dias)
        
        movimientos = Movimiento.query.filter(
            Movimiento.empresa_id == empresa_id,
            Movimiento.fecha >= fecha_inicio
        ).all()
        
        # Agrupar datos por rubro
        rubros_datos = {}
        
        for mov in movimientos:
            if mov.rubro_id:
                rubro_nombre = mov.rubro.nombre if mov.rubro else 'Sin rubro'
                
                if rubro_nombre not in rubros_datos:
                    rubros_datos[rubro_nombre] = {
                        'ingresos': 0,
                        'gastos': 0,
                        'num_ventas': 0
                    }
                
                if mov.tipo == 'ingreso':
                    rubros_datos[rubro_nombre]['ingresos'] += mov.monto
                    rubros_datos[rubro_nombre]['num_ventas'] += 1
                elif mov.tipo == 'gasto':
                    rubros_datos[rubro_nombre]['gastos'] += mov.monto
        
        # Calcular métricas por rubro
        analisis = []
        total_ingresos = sum(datos['ingresos'] for datos in rubros_datos.values())
        
        for rubro, datos in rubros_datos.items():
            ganancia = datos['ingresos'] - datos['gastos']
            margen = (ganancia / datos['ingresos'] * 100) if datos['ingresos'] > 0 else 0
            porcentaje_ingresos = (datos['ingresos'] / total_ingresos * 100) if total_ingresos > 0 else 0
            ticket_promedio = (datos['ingresos'] / datos['num_ventas']) if datos['num_ventas'] > 0 else 0
            
            analisis.append({
                'rubro_nombre': rubro,
                'ingresos': datos['ingresos'],
                'gastos': datos['gastos'],
                'ganancia': ganancia,
                'margen_porcentaje': margen,
                'porcentaje_ingresos': porcentaje_ingresos,
                'num_ventas': datos['num_ventas'],
                'ticket_promedio': ticket_promedio
            })
        
        # Ordenar por ingresos
        analisis.sort(key=lambda x: x['ingresos'], reverse=True)
        
        return analisis
    
    @staticmethod
    def obtener_resumen_financiero(empresa_id: int, dias: int = 7) -> dict:
        """
        Obtiene un resumen financiero completo
        
        Args:
            empresa_id: ID de la empresa
            dias: Número de días a analizar
            
        Returns:
            Diccionario con resumen financiero completo
        """
        # Solo usar métodos esenciales para evitar errores
        try:
            crecimiento = FinancialInsightsService.detectar_crecimiento(empresa_id, dias)
        except Exception as e:
            print(f"Error en detectar_crecimiento: {e}")
            crecimiento = {
                'ganancia_actual': 0,
                'ingresos_actual': 0,
                'gastos_actual': 0,
                'variacion_ganancia': 0
            }
        
        try:
            rubro_top = FinancialInsightsService.obtener_rubro_top(empresa_id, dias)
        except Exception as e:
            print(f"Error en obtener_rubro_top: {e}")
            rubro_top = {}
        
        return {
            'crecimiento': crecimiento,
            'rubro_top': rubro_top,
            'ganancia_neta': crecimiento.get('ganancia_actual', 0),
            'total_ingresos': crecimiento.get('ingresos_actual', 0),
            'total_gastos': crecimiento.get('gastos_actual', 0)
        }
    
    @staticmethod
    def generar_insight_perdidas(empresa_id: int, dias: int = 7) -> Notification:
        """Genera notificación de pérdidas"""
        # Verificar preferencias antes de crear notificación
        if not NotificationService.should_create_notification(empresa_id, 'financieras'):
            return None
            
        perdidas = FinancialInsightsService.detectar_perdidas(empresa_id, dias)
        
        if perdidas['tiene_perdidas']:
            if perdidas['dias_con_perdidas'] >= 3:
                return Notification.create_notification(
                    empresa_id=empresa_id,
                    title="⚠️ Alerta de Pérdidas",
                    message=f"Se detectaron pérdidas durante {perdidas['dias_con_perdidas']} días consecutivos. Total de pérdidas: ${perdidas['total_perdidas']:,.0f}",
                    type='error',
                    priority='critical',
                    category='financial',
                    is_automatic=True,
                    insight_type='loss_alert',
                    meta_data={
                        'dias_con_perdidas': perdidas['dias_con_perdidas'],
                        'total_perdidas': perdidas['total_perdidas'],
                        'perdidas_detalles': perdidas['perdidas_detalles']
                    }
                )
            else:
                return Notification.create_notification(
                    empresa_id=empresa_id,
                    title="Pérdidas Detectadas",
                    message=f"Se detectaron pérdidas en {perdidas['dias_con_perdidas']} día(s). Total: ${perdidas['total_perdidas']:,.0f}",
                    type='warning',
                    priority='medium',
                    category='financial',
                    is_automatic=True,
                    insight_type='loss_alert',
                    meta_data={
                        'dias_con_perdidas': perdidas['dias_con_perdidas'],
                        'total_perdidas': perdidas['total_perdidas']
                    }
                )
        return None
    
    @staticmethod
    def generar_insight_crecimiento(empresa_id: int, dias: int = 7) -> Notification:
        """Genera notificación de crecimiento"""
        # Verificar preferencias antes de crear notificación
        if not NotificationService.should_create_notification(empresa_id, 'financieras'):
            return None
            
        crecimiento = FinancialInsightsService.detectar_crecimiento(empresa_id, dias)
        
        if crecimiento['es_crecimiento'] and abs(crecimiento['variacion_ganancia']) > 10:
            return Notification.create_notification(
                empresa_id=empresa_id,
                title="📈 Crecimiento Positivo",
                message=f"Las ganancias aumentaron un {crecimiento['variacion_ganancia']:.1f}% esta semana.",
                type='success',
                priority='medium',
                category='financial',
                is_automatic=True,
                insight_type='growth_alert',
                meta_data={
                    'variacion_porcentaje': crecimiento['variacion_ganancia'],
                    'ganancia_actual': crecimiento['ganancia_actual'],
                    'ganancia_anterior': crecimiento['ganancia_anterior']
                }
            )
        return None
    
    @staticmethod
    def generar_insight_rubro_top(empresa_id: int, dias: int = 7) -> Notification:
        """Genera notificación de rubro top"""
        # Verificar preferencias antes de crear notificación
        if not NotificationService.should_create_notification(empresa_id, 'financieras'):
            return None
            
        rubro_top = FinancialInsightsService.obtener_rubro_top(empresa_id, dias)
        
        if rubro_top['rubro_nombre']:
            return Notification.create_notification(
                empresa_id=empresa_id,
                title="🏆 Rubro Destacado",
                message=f"{rubro_top['rubro_nombre']} representa el {rubro_top['porcentaje']:.1f}% de los ingresos de los últimos {dias} días.",
                type='info',
                priority='low',
                category='financial',
                is_automatic=True,
                insight_type='rubro_top',
                meta_data={
                    'rubro_nombre': rubro_top['rubro_nombre'],
                    'ingresos': rubro_top['ingresos'],
                    'porcentaje': rubro_top['porcentaje']
                }
            )
        return None
    
    @staticmethod
    def generar_insight_ticket_promedio(empresa_id: int, dias: int = 7) -> Notification:
        """Genera notificación de ticket promedio"""
        # Verificar preferencias antes de crear notificación
        if not NotificationService.should_create_notification(empresa_id, 'financieras'):
            return None
            
        ticket_avg = FinancialInsightsService.calcular_ticket_promedio(empresa_id, dias)
        
        variacion = ticket_avg['variacion_porcentaje']
        
        if abs(variacion) > 5:
            if variacion > 0:
                return Notification.create_notification(
                    empresa_id=empresa_id,
                    title="💰 Ticket Promedio",
                    message=f"El ticket promedio aumentó un {variacion:.1f}% a ${ticket_avg['ticket_promedio']:,.0f}.",
                    type='success',
                    priority='low',
                    category='financial',
                    is_automatic=True,
                    insight_type='ticket_avg',
                    meta_data={
                        'ticket_promedio': ticket_avg['ticket_promedio'],
                        'variacion_porcentaje': variacion
                    }
                )
            else:
                return Notification.create_notification(
                    empresa_id=empresa_id,
                    title="Ticket Promedio",
                    message=f"El ticket promedio disminuyó un {abs(variacion):.1f}% a ${ticket_avg['ticket_promedio']:,.0f}.",
                    type='warning',
                    priority='low',
                    category='financial',
                    is_automatic=True,
                    insight_type='ticket_avg',
                    meta_data={
                        'ticket_promedio': ticket_avg['ticket_promedio'],
                        'variacion_porcentaje': variacion
                    }
                )
        return None
    
    @staticmethod
    def generar_insights_automaticos(empresa_id: int, dias: int = 7) -> list:
        """
        Genera todos los insights automáticos disponibles
        
        Args:
            empresa_id: ID de la empresa
            dias: Número de días a analizar
            
        Returns:
            Lista de notificaciones generadas
        """
        notificaciones = []
        
        # Generar insights
        insight_perdidas = FinancialInsightsService.generar_insight_perdidas(empresa_id, dias)
        if insight_perdidas:
            notificaciones.append(insight_perdidas)
        
        insight_crecimiento = FinancialInsightsService.generar_insight_crecimiento(empresa_id, dias)
        if insight_crecimiento:
            notificaciones.append(insight_crecimiento)
        
        insight_rubro_top = FinancialInsightsService.generar_insight_rubro_top(empresa_id, dias)
        if insight_rubro_top:
            notificaciones.append(insight_rubro_top)
        
        insight_ticket = FinancialInsightsService.generar_insight_ticket_promedio(empresa_id, dias)
        if insight_ticket:
            notificaciones.append(insight_ticket)
        
        return notificaciones
