"""
Utilitários para processamento de dados geográficos.
"""

def parse_coordinates(latitude_str, longitude_str):
    """
    Converte strings de latitude e longitude para valores float.
    
    Args:
        latitude_str: String contendo a latitude
        longitude_str: String contendo a longitude
        
    Returns:
        Tupla (latitude, longitude) com valores float ou None
    """
    latitude = None
    longitude = None
    
    # Processar latitude
    try:
        if latitude_str and latitude_str != 'Buscando...':
            latitude = float(latitude_str)
            # Validar se está dentro dos limites (-90 a 90)
            if not (-90 <= latitude <= 90):
                print(f"Latitude fora dos limites válidos: {latitude}")
                latitude = None
    except (ValueError, TypeError) as e:
        print(f"Erro ao converter latitude '{latitude_str}': {e}")
        latitude = None
        
    # Processar longitude
    try:
        if longitude_str and longitude_str != 'Buscando...':
            longitude = float(longitude_str)
            # Validar se está dentro dos limites (-180 a 180)
            if not (-180 <= longitude <= 180):
                print(f"Longitude fora dos limites válidos: {longitude}")
                longitude = None
    except (ValueError, TypeError) as e:
        print(f"Erro ao converter longitude '{longitude_str}': {e}")
        longitude = None
        
    return latitude, longitude
