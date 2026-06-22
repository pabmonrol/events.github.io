from urllib import parse
from typing import NamedTuple, List
from datetime import datetime, date, time
import json

def location_url(location: str) -> str:
    base_url = "https://www.google.com/maps/search/?"
    parametros = {
        "api": "1",
        "query": location
    }
    query_string = parse.urlencode(parametros)

    return base_url + query_string

def events_to_json(events_list: List[NamedTuple]) -> str:
    def json_serial(obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        if isinstance(obj, time):
            return obj.strftime("%H:%M")
        raise TypeError(f"Tipo {type(obj)} no es serializable en JSON")

    lista_diccionarios = [evento._asdict() for evento in events_list]
    
    return json.dumps(lista_diccionarios, default=json_serial, indent=4, ensure_ascii=False)


def filter_next_7_days(events_list: List[NamedTuple]) -> List[NamedTuple]:
    """
    Filtra eventos para los próximos 7 días sin contar el día actual.
    
    Args:
        events_list: Lista de eventos (NamedTuple con campo 'date')
    
    Returns:
        Lista de eventos filtrados en rango de fechas válidas
    """
    from datetime import timedelta
    
    hoy = date.today()
    fecha_inicio = hoy - timedelta(days=1)
    fecha_fin = hoy + timedelta(days=6)   
    
    eventos_filtrados = [
        evento for evento in events_list
        if fecha_inicio <= evento.date <= fecha_fin
    ]
    
    return eventos_filtrados