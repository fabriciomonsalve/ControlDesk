"""
Utilidades para formateo de datos
"""

def format_clp(amount):
    """
    Formatea un número como pesos chilenos
    
    Args:
        amount: Número a formatear
        
    Returns:
        String formateado como pesos chilenos (ej: 25000 -> "25.000")
    """
    if amount is None:
        return "0"
    
    try:
        # Convertir a número si no lo es
        if isinstance(amount, str):
            amount = float(amount)
        
        # Manejar valores NaN o infinitos
        if not isinstance(amount, (int, float)):
            return "0"
        
        # Verificar si es NaN (NaN no es igual a sí mismo)
        if amount != amount:
            return "0"
        
        # Verificar si es infinito
        if not (amount == amount):
            return "0"
        
        # Si es 0, retornar "0"
        if amount == 0:
            return "0"
        
        # Formatear con puntos como separadores de miles
        formatted = "{:,.0f}".format(amount).replace(",", ".")
        return formatted
    except (ValueError, TypeError):
        return "0"

def format_clp_with_symbol(amount, show_symbol=True):
    """
    Formatea un número como pesos chilenos con símbolo $
    
    Args:
        amount: Número a formatear
        show_symbol: Booleano para incluir o no el símbolo $
        
    Returns:
        String formateado como pesos chilenos (ej: 25000 -> "$25.000")
    """
    formatted = format_clp(amount)
    if show_symbol:
        return f"${formatted}"
    return formatted

def format_clp_for_chart(amount):
    """
    Formatea un número para gráficos Chart.js (sin símbolo, con puntos)
    
    Args:
        amount: Número a formatear
        
    Returns:
        String formateado para gráficos (ej: 25000 -> "25.000")
    """
    return format_clp(amount)

def parse_clp_input(value):
    """
    Parsea un input de usuario en formato CLP a número
    
    Args:
        value: String en formato CLP (ej: "25.000" o "$25.000")
        
    Returns:
        Número flotante
    """
    if value is None or value == "":
        return 0.0
    
    try:
        # Remover símbolo $ y espacios
        cleaned = str(value).replace("$", "").replace(" ", "").strip()
        
        # Reemplazar puntos por nada para convertir a número
        cleaned = cleaned.replace(".", "")
        
        return float(cleaned)
    except (ValueError, TypeError):
        return 0.0
