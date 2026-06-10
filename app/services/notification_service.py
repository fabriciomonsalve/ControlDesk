from app.models.notification import Notification
from app.models.notification_preference import NotificationPreference
from datetime import datetime, timedelta
from sqlalchemy import func


class NotificationService:
    """Servicio para gestión de notificaciones"""
    
    @staticmethod
    def should_create_notification(empresa_id: int, notification_type: str) -> bool:
        """
        Verifica si se debe crear una notificación según las preferencias de la empresa
        
        Args:
            empresa_id: ID de la empresa
            notification_type: Tipo de notificación ('ventas', 'gastos', 'financieras', 'resumen')
            
        Returns:
            True si se debe crear la notificación, False si está desactivada
        """
        try:
            pref = NotificationPreference.query.filter_by(empresa_id=empresa_id).first()
            
            if not pref:
                # Si no hay preferencias, por defecto se crean todas excepto resumen
                return notification_type != 'resumen'
            
            # Verificar según el tipo de notificación
            if notification_type == 'ventas':
                return pref.notif_ventas
            elif notification_type == 'gastos':
                return pref.notif_gastos
            elif notification_type == 'financieras':
                return pref.notif_financieras
            elif notification_type == 'resumen':
                return pref.notif_resumen
            
            return True  # Por defecto crear si no coincide con ningún tipo conocido
        except Exception:
            return True  # En caso de error, crear la notificación por seguridad
    
    @staticmethod
    def create_system_notification(empresa_id: int, title: str, message: str,
                                   event_type: str = 'info', user_id: int = None,
                                   module: str = None, action_url: str = None) -> Notification:
        """
        Crea una notificación de evento del sistema
        
        Args:
            empresa_id: ID de la empresa
            title: Título de la notificación
            message: Mensaje de la notificación
            event_type: Tipo de evento (success, warning, error, info)
            user_id: ID del usuario (opcional)
            module: Módulo del sistema
            action_url: URL para acción
            
        Returns:
            Instancia de Notification creada
        """
        icon_map = {
            'success': 'fa-check-circle',
            'warning': 'fa-exclamation-triangle',
            'error': 'fa-exclamation-circle',
            'info': 'fa-info-circle'
        }
        
        priority_map = {
            'error': 'high',
            'warning': 'medium',
            'success': 'low',
            'info': 'low'
        }
        
        return Notification.create_notification(
            empresa_id=empresa_id,
            title=title,
            message=message,
            type=event_type,
            priority=priority_map.get(event_type, 'low'),
            category='system',
            user_id=user_id,
            is_automatic=False,
            module=module,
            action_url=action_url,
            icon=icon_map.get(event_type)
        )
    
    @staticmethod
    def create_sale_notification(empresa_id: int, monto: float, rubro: str = None,
                                 user_id: int = None) -> Notification:
        """Crea notificación de venta registrada"""
        # Verificar preferencias antes de crear notificación
        if not NotificationService.should_create_notification(empresa_id, 'ventas'):
            return None
            
        title = "💰 Venta Registrada"
        message = f"Se registró una venta por ${monto:,.0f}"
        if rubro:
            message += f" en {rubro}"
        
        return Notification.create_notification(
            empresa_id=empresa_id,
            title=title,
            message=message,
            type='success',
            priority='low',
            category='sales',
            user_id=user_id,
            is_automatic=True,
            module='ventas',
            icon='fa-shopping-cart',
            meta_data={'monto': float(monto), 'rubro': rubro}
        )
    
    @staticmethod
    def create_expense_notification(empresa_id: int, monto: float, rubro: str = None,
                                    user_id: int = None) -> Notification:
        """Crea notificación de gasto registrado"""
        # Verificar preferencias antes de crear notificación
        if not NotificationService.should_create_notification(empresa_id, 'gastos'):
            return None
            
        title = "💸 Gasto Registrado"
        message = f"Se registró un gasto por ${monto:,.0f}"
        if rubro:
            message += f" en {rubro}"
        
        return Notification.create_notification(
            empresa_id=empresa_id,
            title=title,
            message=message,
            type='warning',
            priority='medium',
            category='financial',
            user_id=user_id,
            is_automatic=True,
            module='gastos',
            icon='fa-receipt',
            meta_data={'monto': float(monto), 'rubro': rubro}
        )
    
    @staticmethod
    def create_import_notification(empresa_id: int, registros: int, errores: int = 0,
                                   archivo: str = None, user_id: int = None) -> Notification:
        """Crea notificación de importación"""
        if errores > 0:
            title = "⚠️ Importación con Errores"
            message = f"Se importaron {registros} registros con {errores} errores."
            event_type = 'warning'
            priority = 'medium'
        else:
            title = "✅ Importación Exitosa"
            message = f"Se importaron {registros} registros exitosamente."
            event_type = 'success'
            priority = 'low'
        
        if archivo:
            message += f" Archivo: {archivo}"
        
        return Notification.create_notification(
            empresa_id=empresa_id,
            title=title,
            message=message,
            type=event_type,
            priority=priority,
            category='system',
            user_id=user_id,
            is_automatic=True,
            module='importar',
            icon='fa-file-import',
            meta_data={'registros': registros, 'errores': errores, 'archivo': archivo}
        )
    
    @staticmethod
    def create_user_notification(empresa_id: int, action: str, username: str,
                                 user_id: int = None) -> Notification:
        """Crea notificación de evento de usuario"""
        title = f"👤 Usuario {action}"
        message = f"El usuario {username} fue {action.lower()} exitosamente."
        
        return Notification.create_notification(
            empresa_id=empresa_id,
            title=title,
            message=message,
            type='info',
            priority='low',
            category='user',
            user_id=user_id,
            is_automatic=True,
            module='usuarios',
            icon='fa-user',
            meta_data={'action': action, 'username': username}
        )
    
    @staticmethod
    def create_low_stock_notification(empresa_id: int, producto: str, stock_actual: int,
                                      stock_minimo: int, user_id: int = None) -> Notification:
        """Crea notificación de stock bajo"""
        title = "📦 Stock Bajo"
        message = f"El producto {producto} tiene stock bajo ({stock_actual}/{stock_minimo})."
        
        return Notification.create_notification(
            empresa_id=empresa_id,
            title=title,
            message=message,
            type='warning',
            priority='medium',
            category='inventory',
            user_id=user_id,
            is_automatic=True,
            module='inventario',
            icon='fa-box',
            action_url='/inventario',
            meta_data={'producto': producto, 'stock_actual': stock_actual, 'stock_minimo': stock_minimo}
        )
    
    @staticmethod
    def create_backup_notification(empresa_id: int, exitoso: bool = True,
                                   user_id: int = None) -> Notification:
        """Crea notificación de backup"""
        if exitoso:
            title = "💾 Backup Exitoso"
            message = "El backup de la base de datos se realizó exitosamente."
            event_type = 'success'
        else:
            title = "❌ Error en Backup"
            message = "Ocurrió un error al realizar el backup de la base de datos."
            event_type = 'error'
        
        return Notification.create_notification(
            empresa_id=empresa_id,
            title=title,
            message=message,
            type=event_type,
            priority='high' if not exitoso else 'low',
            category='system',
            user_id=user_id,
            is_automatic=True,
            module='configuracion',
            icon='fa-database',
            meta_data={'exitoso': exitoso}
        )
    
    @staticmethod
    def create_report_notification(empresa_id: int, reporte: str,
                                   user_id: int = None) -> Notification:
        """Crea notificación de reporte generado"""
        title = "📊 Reporte Generado"
        message = f"El reporte {reporte} se generó exitosamente."
        
        return Notification.create_notification(
            empresa_id=empresa_id,
            title=title,
            message=message,
            type='success',
            priority='low',
            category='report',
            user_id=user_id,
            is_automatic=True,
            module='reportes',
            icon='fa-chart-bar',
            action_url='/reportes',
            meta_data={'reporte': reporte}
        )
    
    @staticmethod
    def get_notifications(empresa_id: int, user_id: int = None, limit: int = 50,
                          unread_only: bool = False, read_only: bool = False,
                          type_filter: str = None, priority_filter: str = None,
                          offset: int = 0, search_query: str = None) -> dict:
        """
        Obtiene notificaciones con filtros y paginación
        
        Args:
            empresa_id: ID de la empresa
            user_id: ID del usuario (opcional)
            limit: Límite de registros
            unread_only: Si solo retornar no leídas
            read_only: Si solo retornar leídas
            type_filter: Filtro por tipo
            priority_filter: Filtro por prioridad
            offset: Offset para paginación
            search_query: Búsqueda en título y mensaje
            
        Returns:
            Diccionario con notificaciones y metadatos
        """
        return Notification.get_notifications(
            empresa_id=empresa_id,
            user_id=user_id,
            limit=limit,
            unread_only=unread_only,
            read_only=read_only,
            type_filter=type_filter,
            priority_filter=priority_filter,
            offset=offset,
            search_query=search_query
        )
    
    @staticmethod
    def mark_as_read(notification_id: int, empresa_id: int, user_id: int = None) -> bool:
        """
        Marca una notificación como leída
        
        Args:
            notification_id: ID de la notificación
            empresa_id: ID de la empresa
            user_id: ID del usuario (opcional)
            
        Returns:
            True si se marcó como leída, False si no
        """
        notification = Notification.query.filter_by(
            id=notification_id,
            empresa_id=empresa_id
        ).first()
        
        if not notification:
            return False
        
        if user_id and notification.user_id != user_id:
            return False
        
        notification.mark_as_read()
        return True
    
    @staticmethod
    def mark_all_as_read(empresa_id: int, user_id: int = None) -> int:
        """
        Marca todas las notificaciones como leídas
        
        Args:
            empresa_id: ID de la empresa
            user_id: ID del usuario (opcional)
            
        Returns:
            Número de notificaciones marcadas
        """
        return Notification.mark_all_as_read(empresa_id, user_id)
    
    @staticmethod
    def delete_notification(notification_id: int, empresa_id: int, user_id: int = None) -> bool:
        """
        Elimina una notificación
        
        Args:
            notification_id: ID de la notificación
            empresa_id: ID de la empresa
            user_id: ID del usuario (opcional)
            
        Returns:
            True si se eliminó, False si no
        """
        notification = Notification.query.filter_by(
            id=notification_id,
            empresa_id=empresa_id
        ).first()
        
        if not notification:
            return False
        
        if user_id and notification.user_id != user_id:
            return False
        
        notification.delete_notification()
        return True
    
    @staticmethod
    def delete_read(empresa_id: int) -> int:
        """
        Elimina todas las notificaciones leídas
        
        Args:
            empresa_id: ID de la empresa
            
        Returns:
            Número de notificaciones eliminadas
        """
        notifications = Notification.query.filter_by(
            empresa_id=empresa_id,
            is_read=True
        ).all()
        
        count = len(notifications)
        for notification in notifications:
            notification.delete_notification()
        
        return count
    
    @staticmethod
    def get_notification_stats(empresa_id: int, user_id: int = None) -> dict:
        """
        Obtiene estadísticas de notificaciones
        
        Args:
            empresa_id: ID de la empresa
            user_id: ID del usuario (opcional)
            
        Returns:
            Diccionario con estadísticas
        """
        query = Notification.query.filter_by(empresa_id=empresa_id)
        
        if user_id:
            query = query.filter_by(user_id=user_id)
        
        total = query.count()
        unread = query.filter_by(is_read=False).count()
        
        # Por tipo
        tipos = {}
        for tipo in ['success', 'warning', 'error', 'info']:
            tipos[tipo] = query.filter_by(type=tipo).count()
        
        # Por prioridad
        prioridades = {}
        for prioridad in ['low', 'medium', 'high', 'critical']:
            prioridades[prioridad] = query.filter_by(priority=prioridad).count()
        
        # Últimas 24 horas
        fecha_24h = datetime.utcnow() - timedelta(hours=24)
        ultimas_24h = query.filter(Notification.created_at >= fecha_24h).count()
        
        # Últimos 7 días
        fecha_7d = datetime.utcnow() - timedelta(days=7)
        ultimas_7d = query.filter(Notification.created_at >= fecha_7d).count()
        
        return {
            'total': total,
            'unread': unread,
            'por_tipo': tipos,
            'por_prioridad': prioridades,
            'ultimas_24h': ultimas_24h,
            'ultimas_7d': ultimas_7d
        }
    
    @staticmethod
    def clean_old_notifications(empresa_id: int, dias: int = 30, 
                               keep_unread: bool = True) -> int:
        """
        Limpia notificaciones antiguas
        
        Args:
            empresa_id: ID de la empresa
            dias: Días de antigüedad para eliminar
            keep_unread: Si mantener las no leídas
            
        Returns:
            Número de notificaciones eliminadas
        """
        fecha_limite = datetime.utcnow() - timedelta(days=dias)
        
        query = Notification.query.filter(
            Notification.empresa_id == empresa_id,
            Notification.created_at < fecha_limite
        )
        
        if keep_unread:
            query = query.filter_by(is_read=True)
        
        notifications = query.all()
        count = len(notifications)
        
        for notification in notifications:
            notification.delete_notification()
        
        return count
    
    @staticmethod
    def create_purchase_notification(empresa_id: int, monto: float, rubro: str, 
                                     proveedor: str, numero_factura: str):
        """
        Crea una notificación de compra/factura
        Args:
            empresa_id: ID de la empresa
            monto: Monto de la compra
            rubro: Nombre del rubro
            proveedor: Nombre del proveedor
            numero_factura: Número de factura
        """
        try:
            from app import format_clp_filter
            
            notification = Notification(
                empresa_id=empresa_id,
                title=f"Compra Registrada - {rubro}",
                message=f"Factura de compra de {format_clp_filter(monto)} registrada con {proveedor} ({numero_factura})",
                notification_type='gastos',
                event_type='purchase',
                priority='medium',
                is_read=False
            )
            notification.save_notification()
        except Exception as e:
            print(f"Error creando notificación de compra: {e}")
