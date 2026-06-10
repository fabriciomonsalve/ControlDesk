from typing import List, Dict, Any, Optional, Tuple
from flask import current_app
from datetime import datetime, timedelta
from app import db
from app.models.recordatorio import Recordatorio
from app.models.historial_recordatorio import HistorialRecordatorio
from app.models.rubro import Rubro
from app.models.movimiento import Movimiento
from app.services.notification_service import NotificationService


class RecordatoriosService:
    """Servicio para gestión de recordatorios y vencimientos"""
    
    # Prioridades
    PRIORIDADES = ['baja', 'media', 'alta', 'critica']
    
    # Estados
    ESTADOS = ['pendiente', 'proximo', 'vencido', 'completado', 'cancelado']
    
    # Tipos
    TIPOS = ['general', 'pago', 'tarea', 'renovacion', 'mantenimiento', 'reunion']
    
    # Frecuencias de recurrencia
    FRECUENCIAS = ['diario', 'semanal', 'mensual', 'trimestral', 'semestral', 'anual']
    
    # Días de aviso predefinidos
    DIAS_AVISO = [1, 2, 3, 5, 7, 10, 15, 30]
    
    @staticmethod
    def crear_recordatorio(
        empresa_id: int,
        titulo: str,
        fecha_vencimiento: datetime,
        tipo: str = 'general',
        prioridad: str = 'media',
        descripcion: str = None,
        rubro_id: int = None,
        monto: float = None,
        dias_aviso: int = 3,
        recurrente: bool = False,
        frecuencia: str = None,
        sonido: str = 'default'
    ) -> Tuple[bool, str, Optional[Recordatorio]]:
        """
        Crea un nuevo recordatorio
        """
        try:
            # Validaciones
            if tipo not in RecordatoriosService.TIPOS:
                return False, "Tipo de recordatorio no válido", None
            
            if prioridad not in RecordatoriosService.PRIORIDADES:
                return False, "Prioridad no válida", None
            
            if recurrente and frecuencia not in RecordatoriosService.FRECUENCIAS:
                return False, "Frecuencia no válida para recordatorios recurrentes", None
            
            if monto is not None and monto < 0:
                return False, "El monto no puede ser negativo", None
            
            # Validar que el rubro pertenezca a la empresa
            if rubro_id:
                rubro = Rubro.query.get(rubro_id)
                if not rubro:
                    return False, "Rubro no encontrado", None
                if rubro.empresa_id != empresa_id:
                    return False, "El rubro no pertenece a esta empresa", None
            
            # Calcular fecha de aviso
            fecha_aviso = RecordatoriosService.calcular_fecha_aviso(fecha_vencimiento, dias_aviso)
            
            # Determinar estado inicial
            estado = RecordatoriosService.determinar_estado(fecha_vencimiento, fecha_aviso)
            
            # Crear recordatorio
            recordatorio = Recordatorio(
                empresa_id=empresa_id,
                titulo=titulo,
                descripcion=descripcion,
                tipo=tipo,
                prioridad=prioridad,
                rubro_id=rubro_id,
                fecha_vencimiento=fecha_vencimiento,
                fecha_aviso=fecha_aviso,
                dias_aviso=dias_aviso,
                monto=monto,
                estado=estado,
                recurrente=recurrente,
                frecuencia=frecuencia,
                sonido=sonido
            )
            
            db.session.add(recordatorio)
            db.session.flush()
            
            # Registrar en historial
            RecordatoriosService.registrar_historial(
                recordatorio_id=recordatorio.id,
                accion='creado',
                observacion=f"Recordatorio creado con estado: {estado}"
            )
            
            db.session.commit()
            
            return True, "Recordatorio creado exitosamente", recordatorio
            
        except Exception as e:
            current_app.logger.error(f"Error creando recordatorio: {str(e)}")
            db.session.rollback()
            return False, f"Error al crear recordatorio: {str(e)}", None
    
    @staticmethod
    def actualizar_estado(recordatorio_id: int, nuevo_estado: str, usuario: str = None) -> Tuple[bool, str]:
        """
        Actualiza el estado de un recordatorio
        """
        try:
            if nuevo_estado not in RecordatoriosService.ESTADOS:
                return False, "Estado no válido"
            
            recordatorio = Recordatorio.query.get(recordatorio_id)
            if not recordatorio:
                return False, "Recordatorio no encontrado"
            
            estado_anterior = recordatorio.estado
            
            # Actualizar estado y fechas
            recordatorio.estado = nuevo_estado
            recordatorio.fecha_actualizacion = datetime.utcnow()
            
            if nuevo_estado == 'completado':
                recordatorio.fecha_completado = datetime.utcnow()
            elif nuevo_estado == 'cancelado':
                recordatorio.fecha_cancelado = datetime.utcnow()
            
            # Registrar en historial
            RecordatoriosService.registrar_historial(
                recordatorio_id=recordatorio.id,
                accion='actualizado',
                usuario=usuario,
                estado_anterior=estado_anterior,
                estado_nuevo=nuevo_estado,
                observacion=f"Estado cambiado de {estado_anterior} a {nuevo_estado}"
            )
            
            db.session.commit()
            
            # Si es recurrente y se completó, generar siguiente
            if nuevo_estado == 'completado' and recordatorio.recurrente:
                RecordatoriosService.generar_siguiente_recurrente(recordatorio)
            
            return True, "Estado actualizado exitosamente"
            
        except Exception as e:
            current_app.logger.error(f"Error actualizando estado: {str(e)}")
            db.session.rollback()
            return False, f"Error al actualizar estado: {str(e)}"
    
    @staticmethod
    def obtener_pendientes(empresa_id: int, page: int = 1, per_page: int = 5) -> Tuple[List[Recordatorio], int, int]:
        """
        Obtiene recordatorios pendientes (no vencidos ni próximos a vencer)
        con paginación
        """
        now = datetime.utcnow()
        query = Recordatorio.query.filter(
            Recordatorio.empresa_id == empresa_id,
            Recordatorio.estado == 'pendiente',
            Recordatorio.fecha_aviso > now
        ).order_by(Recordatorio.fecha_vencimiento.asc())
        
        total = query.count()
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return pagination.items, pagination.pages, total
    
    @staticmethod
    def obtener_proximos(empresa_id: int) -> List[Recordatorio]:
        """
        Obtiene recordatorios próximos a vencer (dentro del período de alerta)
        Solo incluye recordatorios que están dentro del período de aviso configurado
        """
        now = datetime.utcnow()
        return Recordatorio.query.filter(
            Recordatorio.empresa_id == empresa_id,
            Recordatorio.estado == 'proximo',
            Recordatorio.fecha_aviso <= now
        ).order_by(Recordatorio.fecha_vencimiento.asc()).all()
    
    @staticmethod
    def obtener_vencidos(empresa_id: int) -> List[Recordatorio]:
        """
        Obtiene recordatorios vencidos
        """
        now = datetime.utcnow()
        return Recordatorio.query.filter(
            Recordatorio.empresa_id == empresa_id,
            Recordatorio.estado == 'vencido'
        ).order_by(Recordatorio.fecha_vencimiento.asc()).all()
    
    @staticmethod
    def obtener_todos(empresa_id: int, page: int = 1, per_page: int = 7) -> Tuple[List[Recordatorio], int, int]:
        """
        Obtiene todos los recordatorios de una empresa con paginación
        """
        query = Recordatorio.query.filter(
            Recordatorio.empresa_id == empresa_id
        ).order_by(Recordatorio.fecha_vencimiento.desc())
        
        total = query.count()
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return pagination.items, pagination.pages, total

    @staticmethod
    def calcular_proximo_pago(recordatorio: Recordatorio) -> Optional[datetime]:
        """
        Calcula la fecha del próximo pago para un recordatorio
        Si el recordatorio es recurrente y está completado, calcula la fecha del siguiente período
        Si es recurrente y no está completado, muestra la fecha de vencimiento actual
        Si no es recurrente, muestra la fecha de vencimiento actual
        """
        if recordatorio.recurrente and recordatorio.estado == 'completado' and recordatorio.frecuencia:
            # Usar la función calcular_siguiente_fecha que maneja edge cases correctamente
            return RecordatoriosService.calcular_siguiente_fecha(
                recordatorio.fecha_vencimiento,
                recordatorio.frecuencia
            )
        
        # Para no recurrentes o recurrentes no completados, mostrar fecha de vencimiento actual
        return recordatorio.fecha_vencimiento

    @staticmethod
    def obtener_completados(empresa_id: int, page: int = 1, per_page: int = 5) -> Tuple[List[Recordatorio], int, int]:
        """
        Obtiene los últimos recordatorios completados con paginación
        """
        query = Recordatorio.query.filter(
            Recordatorio.empresa_id == empresa_id,
            Recordatorio.estado == 'completado'
        ).order_by(Recordatorio.fecha_completado.desc())
        
        total = query.count()
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return pagination.items, pagination.pages, total
    
    @staticmethod
    def calcular_fecha_aviso(fecha_vencimiento: datetime, dias_aviso: int) -> datetime:
        """
        Calcula la fecha de aviso basada en la fecha de vencimiento
        """
        return fecha_vencimiento - timedelta(days=dias_aviso)
    
    @staticmethod
    def determinar_estado(fecha_vencimiento: datetime, fecha_aviso: datetime) -> str:
        """
        Determina el estado de un recordatorio basado en las fechas
        """
        now = datetime.utcnow()
        
        if now > fecha_vencimiento:
            return 'vencido'
        elif now >= fecha_aviso:
            return 'proximo'
        else:
            return 'pendiente'
    
    @staticmethod
    def actualizar_estados_automaticos(empresa_id: int) -> int:
        """
        Actualiza automáticamente los estados de todos los recordatorios
        Retorna la cantidad de recordatorios actualizados
        """
        try:
            now = datetime.utcnow()
            actualizados = 0
            
            # Solo actualizar recordatorios que no están completados o cancelados
            # Actualizar pendientes a próximos
            pendientes = Recordatorio.query.filter(
                Recordatorio.empresa_id == empresa_id,
                Recordatorio.estado == 'pendiente',
                Recordatorio.fecha_aviso <= now
            ).all()
            
            for r in pendientes:
                r.estado = 'proximo'
                r.fecha_actualizacion = now
                actualizados += 1
            
            # Actualizar próximos a vencidos (excluyendo completados y cancelados)
            proximos = Recordatorio.query.filter(
                Recordatorio.empresa_id == empresa_id,
                Recordatorio.estado == 'proximo',
                Recordatorio.fecha_vencimiento <= now
            ).all()
            
            for r in proximos:
                r.estado = 'vencido'
                r.fecha_actualizacion = now
                actualizados += 1
            
            db.session.commit()
            return actualizados
            
        except Exception as e:
            current_app.logger.error(f"Error actualizando estados: {str(e)}")
            db.session.rollback()
            return 0
    
    @staticmethod
    def calcular_siguiente_fecha(fecha_actual: datetime, frecuencia: str) -> datetime:
        """
        Calcula la siguiente fecha basada en la frecuencia, manejando edge cases
        como el día 31 en meses que no tienen 31 días
        """
        try:
            if frecuencia == 'diario':
                return fecha_actual + timedelta(days=1)
            elif frecuencia == 'semanal':
                return fecha_actual + timedelta(weeks=1)
            elif frecuencia == 'quincenal':
                return fecha_actual + timedelta(days=15)
            elif frecuencia == 'mensual':
                # Mismo día del siguiente mes, ajustando si no existe (ej: 31 en abril)
                year = fecha_actual.year
                month = fecha_actual.month + 1
                if month > 12:
                    month = 1
                    year += 1
                
                # Intentar usar el mismo día
                day = fecha_actual.day
                
                # Obtener el último día del mes
                import calendar
                last_day_of_month = calendar.monthrange(year, month)[1]
                
                # Si el día original es mayor que el último día del mes, usar el último día
                if day > last_day_of_month:
                    day = last_day_of_month
                
                return datetime(year, month, day, fecha_actual.hour, fecha_actual.minute)
            elif frecuencia == 'trimestral':
                # Mismo día 3 meses después, ajustando si no existe
                year = fecha_actual.year
                month = fecha_actual.month + 3
                while month > 12:
                    month -= 12
                    year += 1
                
                day = fecha_actual.day
                import calendar
                last_day_of_month = calendar.monthrange(year, month)[1]
                
                if day > last_day_of_month:
                    day = last_day_of_month
                
                return datetime(year, month, day, fecha_actual.hour, fecha_actual.minute)
            elif frecuencia == 'semestral':
                # Mismo día 6 meses después, ajustando si no existe
                year = fecha_actual.year
                month = fecha_actual.month + 6
                while month > 12:
                    month -= 12
                    year += 1
                
                day = fecha_actual.day
                import calendar
                last_day_of_month = calendar.monthrange(year, month)[1]
                
                if day > last_day_of_month:
                    day = last_day_of_month
                
                return datetime(year, month, day, fecha_actual.hour, fecha_actual.minute)
            elif frecuencia == 'anual':
                # Mismo día del siguiente año, ajustando si no existe (ej: 29 feb en año no bisiesto)
                year = fecha_actual.year + 1
                month = fecha_actual.month
                day = fecha_actual.day
                
                import calendar
                last_day_of_month = calendar.monthrange(year, month)[1]
                
                if day > last_day_of_month:
                    day = last_day_of_month
                
                return datetime(year, month, day, fecha_actual.hour, fecha_actual.minute)
            else:
                return fecha_actual
        except Exception as e:
            current_app.logger.error(f"Error calculando siguiente fecha: {str(e)}")
            # Fallback a cálculo simple
            if frecuencia == 'mensual':
                return fecha_actual + timedelta(days=30)
            elif frecuencia == 'trimestral':
                return fecha_actual + timedelta(days=90)
            elif frecuencia == 'semestral':
                return fecha_actual + timedelta(days=180)
            elif frecuencia == 'anual':
                return fecha_actual + timedelta(days=365)
            else:
                return fecha_actual

    @staticmethod
    def generar_siguiente_recurrente(recordatorio: Recordatorio) -> Optional[Recordatorio]:
        """
        Genera el siguiente recordatorio para uno recurrente
        """
        try:
            # Calcular nueva fecha de vencimiento según frecuencia (con manejo de edge cases)
            # Usamos siempre la fecha_vencimiento original como base, no la fecha actual
            nueva_fecha = RecordatoriosService.calcular_siguiente_fecha(
                recordatorio.fecha_vencimiento, 
                recordatorio.frecuencia
            )
            
            # Calcular nueva fecha de aviso
            nueva_fecha_aviso = RecordatoriosService.calcular_fecha_aviso(nueva_fecha, recordatorio.dias_aviso)
            
            # Determinar estado
            estado = RecordatoriosService.determinar_estado(nueva_fecha, nueva_fecha_aviso)
            
            # Crear nuevo recordatorio
            nuevo_recordatorio = Recordatorio(
                empresa_id=recordatorio.empresa_id,
                titulo=recordatorio.titulo,
                descripcion=recordatorio.descripcion,
                tipo=recordatorio.tipo,
                prioridad=recordatorio.prioridad,
                rubro_id=recordatorio.rubro_id,
                fecha_vencimiento=nueva_fecha,
                fecha_aviso=nueva_fecha_aviso,
                dias_aviso=recordatorio.dias_aviso,
                monto=recordatorio.monto,
                estado=estado,
                recurrente=recordatorio.recurrente,
                frecuencia=recordatorio.frecuencia,
                sonido=recordatorio.sonido,
                sonido_activo=recordatorio.sonido_activo
            )
            
            db.session.add(nuevo_recordatorio)
            db.session.flush()
            
            # Registrar en historial del nuevo recordatorio
            RecordatoriosService.registrar_historial(
                recordatorio_id=nuevo_recordatorio.id,
                accion='recurrente_generado',
                observacion=f"Generado desde recordatorio recurrente #{recordatorio.id}"
            )
            
            # Registrar en historial del recordatorio original
            RecordatoriosService.registrar_historial(
                recordatorio_id=recordatorio.id,
                accion='recurrente_generado',
                observacion=f"Generó nuevo recordatorio #{nuevo_recordatorio.id}"
            )
            
            db.session.commit()
            
            return nuevo_recordatorio
            
        except Exception as e:
            current_app.logger.error(f"Error generando recurrente: {str(e)}")
            db.session.rollback()
            return None
    
    @staticmethod
    def registrar_gasto(recordatorio_id: int, usuario: str = None) -> Tuple[bool, str, Optional[Movimiento]]:
        """
        Registra un gasto financiero basado en un recordatorio completado
        """
        try:
            from app.models.categoria import Categoria
            
            recordatorio = Recordatorio.query.get(recordatorio_id)
            if not recordatorio:
                return False, "Recordatorio no encontrado", None
            
            if recordatorio.monto is None or recordatorio.monto <= 0:
                return False, "El recordatorio no tiene monto asociado", None
            
            # Buscar o usar una categoría por defecto para gastos de recordatorios
            # Usar "Servicios" (ID 3) o crear una categoría específica si no existe
            categoria_por_defecto = Categoria.query.filter(
                Categoria.empresa_id == recordatorio.empresa_id,
                Categoria.nombre == 'Servicios'
            ).first()
            
            if not categoria_por_defecto:
                # Si no existe Servicios, usar la primera categoría de la empresa
                categoria_por_defecto = Categoria.query.filter(
                    Categoria.empresa_id == recordatorio.empresa_id
                ).first()
            
            categoria_id = categoria_por_defecto.id if categoria_por_defecto else None
            
            # Crear movimiento
            movimiento = Movimiento(
                empresa_id=recordatorio.empresa_id,
                rubro_id=recordatorio.rubro_id,
                categoria_id=categoria_id,
                monto=recordatorio.monto,
                tipo='gasto',
                fecha=datetime.utcnow(),
                descripcion=f"Pago: {recordatorio.titulo}",
                origen='recordatorio'
            )
            
            db.session.add(movimiento)
            
            # Registrar en historial
            RecordatoriosService.registrar_historial(
                recordatorio_id=recordatorio.id,
                accion='gasto_registrado',
                usuario=usuario,
                observacion=f"Gasto de ${recordatorio.monto} registrado automáticamente"
            )
            
            db.session.commit()
            
            return True, "Gasto registrado exitosamente", movimiento
            
        except Exception as e:
            current_app.logger.error(f"Error registrando gasto: {str(e)}")
            db.session.rollback()
            return False, f"Error al registrar gasto: {str(e)}", None
    
    @staticmethod
    def registrar_historial(
        recordatorio_id: int,
        accion: str,
        usuario: str = None,
        observacion: str = None,
        estado_anterior: str = None,
        estado_nuevo: str = None
    ):
        """
        Registra una acción en el historial del recordatorio
        """
        try:
            historial = HistorialRecordatorio(
                recordatorio_id=recordatorio_id,
                accion=accion,
                usuario=usuario,
                observacion=observacion,
                estado_anterior=estado_anterior,
                estado_nuevo=estado_nuevo
            )
            db.session.add(historial)
        except Exception as e:
            current_app.logger.error(f"Error registrando historial: {str(e)}")
    
    @staticmethod
    def generar_notificaciones(empresa_id: int) -> int:
        """
        Genera notificaciones para recordatorios próximos y vencidos
        Retorna la cantidad de notificaciones generadas
        """
        try:
            notificaciones = 0
            
            # Obtener próximos y vencidos
            proximos = RecordatoriosService.obtener_proximos(empresa_id)
            vencidos = RecordatoriosService.obtener_vencidos(empresa_id)
            
            # Generar notificaciones para próximos
            for r in proximos:
                dias_restantes = (r.fecha_vencimiento - datetime.utcnow()).days
                if dias_restantes >= 0:
                    NotificationService.create_purchase_notification(
                        empresa_id=empresa_id,
                        monto=r.monto or 0,
                        rubro=r.rubro.nombre if r.rubro else 'General',
                        proveedor=r.titulo,
                        numero_factura=f"Vence en {dias_restantes} días"
                    )
                    notificaciones += 1
            
            # Generar notificaciones para vencidos
            for r in vencidos:
                dias_vencido = (datetime.utcnow() - r.fecha_vencimiento).days
                NotificationService.create_purchase_notification(
                    empresa_id=empresa_id,
                    monto=r.monto or 0,
                    rubro=r.rubro.nombre if r.rubro else 'General',
                    proveedor=r.titulo,
                    numero_factura=f"Vencido hace {dias_vencido} días"
                )
                notificaciones += 1
            
            return notificaciones
            
        except Exception as e:
            current_app.logger.error(f"Error generando notificaciones: {str(e)}")
            return 0
    
    @staticmethod
    def obtener_resumen(empresa_id: int) -> Dict[str, int]:
        """
        Obtiene un resumen de la cantidad de recordatorios por estado
        """
        try:
            pendientes, _, _ = RecordatoriosService.obtener_pendientes(empresa_id)
            proximos = RecordatoriosService.obtener_proximos(empresa_id)
            vencidos = RecordatoriosService.obtener_vencidos(empresa_id)
            
            # Completados este mes
            mes_actual = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            completados_mes = Recordatorio.query.filter(
                Recordatorio.empresa_id == empresa_id,
                Recordatorio.estado == 'completado',
                Recordatorio.fecha_completado >= mes_actual
            ).count()
            
            return {
                'pendientes': len(pendientes),
                'proximos': len(proximos),
                'vencidos': len(vencidos),
                'completados_mes': completados_mes
            }
            
        except Exception as e:
            current_app.logger.error(f"Error obteniendo resumen: {str(e)}")
            return {
                'pendientes': 0,
                'proximos': 0,
                'vencidos': 0,
                'completados_mes': 0
            }
    
    @staticmethod
    def eliminar_recordatorio(recordatorio_id: int) -> Tuple[bool, str]:
        """
        Elimina un recordatorio y su historial
        """
        try:
            recordatorio = Recordatorio.query.get(recordatorio_id)
            if not recordatorio:
                return False, "Recordatorio no encontrado"
            
            # Eliminar historial asociado
            HistorialRecordatorio.query.filter_by(recordatorio_id=recordatorio_id).delete()
            
            # Eliminar el recordatorio
            db.session.delete(recordatorio)
            db.session.commit()
            
            return True, "Recordatorio eliminado exitosamente"
            
        except Exception as e:
            current_app.logger.error(f"Error eliminando recordatorio: {str(e)}")
            db.session.rollback()
            return False, f"Error al eliminar recordatorio: {str(e)}"
