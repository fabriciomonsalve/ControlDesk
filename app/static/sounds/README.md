# Archivos de Sonido para Alertas de Recordatorios

Esta carpeta debe contener los archivos de audio para las alertas de recordatorios.

## Archivos Requeridos

1. **alert.mp3** - Sonido de alerta para notificaciones de recordatorios
   - Formato: MP3
   - Duración recomendada: 1-3 segundos
   - Volumen: Medio

## Cómo Agregar Archivos de Sonido

1. Coloca tus archivos de sonido en esta carpeta
2. Los nombres deben coincidir con los especificados arriba
3. Los sonidos se reproducirán automáticamente cuando haya nuevas alertas

## Sonidos Sugeridos

- Sonido de campana suave
- Sonido de notificación tipo "ding"
- Sonido de alarma corta

## Configuración

El volumen se puede ajustar en el archivo `base.html` en la función `playAlertSound()`:

```javascript
audio.volume = 0.5; // Ajusta entre 0.0 y 1.0
```

## Frecuencia de Verificación

Las alertas se verifican automáticamente cada 2 minutos (120,000 ms).
Este intervalo se puede ajustar en `base.html`:

```javascript
setInterval(loadAlertas, 120000); // Cambiar 120000 por los milisegundos deseados
```
