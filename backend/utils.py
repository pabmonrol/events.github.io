from urllib import parse
from typing import NamedTuple, List, Tuple
from datetime import datetime, date, time, timedelta
import json
import re
import threading
from bs4 import Tag

def _as_text(value) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if hasattr(value, "get_text"):
        return value.get_text(strip=True)
    return str(value).strip()

_install_lock = threading.Lock()
_translation_ready = False

def _de_en_installed() -> bool:
    import argostranslate.translate

    installed = argostranslate.translate.get_installed_languages()
    from_lang = next((lang for lang in installed if lang.code == "de"), None)
    to_lang = next((lang for lang in installed if lang.code == "en"), None)
    if from_lang is None or to_lang is None:
        return False
    return from_lang.get_translation(to_lang) is not None

def _ensure_de_en() -> None:
    global _translation_ready
    if _translation_ready:
        return

    with _install_lock:
        if _translation_ready:
            return
        if not _de_en_installed():
            import argostranslate.package
            import argostranslate.settings

            argostranslate.package.update_package_index()
            if not argostranslate.settings.local_package_index.exists():
                raise RuntimeError("Could not download the Argos package index")

            available = argostranslate.package.get_available_packages()
            package = next(
                (
                    pkg for pkg in available
                    if pkg.from_code == "de" and pkg.to_code == "en"
                ),
                None,
            )
            if package is None:
                raise RuntimeError("German to English Argos package is not available")
            argostranslate.package.install_from_path(package.download())
        _translation_ready = True

def translate_text(value) -> str:
    original = _as_text(value)
    if not original:
        return ""

    try:
        import argostranslate.translate

        _ensure_de_en()
        translated = argostranslate.translate.translate(original, "de", "en")
        if not translated:
            return original
        return translated
    except Exception as exc:
        print(f"Translation failed, keeping original: {exc}")
        return original

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
    hoy = date.today()
    fecha_inicio = hoy 
    fecha_fin = hoy + timedelta(days=6)   
    
    eventos_filtrados = [
        evento for evento in events_list
        if fecha_inicio <= evento.date <= fecha_fin
    ]
    
    return eventos_filtrados

def verificar_fecha_limite(lista_tuplas: List[NamedTuple]) -> bool:
    if not lista_tuplas:
        return False
    
    fecha_limite = date.today() + timedelta(days=6)

    return any(evento.date >= fecha_limite for evento in lista_tuplas)

def get_price(description: str)->float:
    if not description:
        return None

    text_lower = description.lower()

    pattern = r'(?:chf\s*(\d+(?:[.,]\d+)?))|(\d+(?:[.,]\d+)?)(?:\.-)?\s*chf'
    
    match = re.search(pattern, text_lower)
    if match:
        price_str = match.group(1) or match.group(2)
        price_str = price_str.replace(',', '.')
        return float(price_str)

def get_hour(hour_text: str) -> time:
    match = re.search(r"\d{1,2}[:.]\d{2}", hour_text)
    first_hour = match.group().replace(".", ":")
    return datetime.strptime(first_hour, "%H:%M").time()

def check_location(location_text: Tag, city: str) -> Tuple[str]:
    location = city
    if location_text:
        location = location_text.get_text(strip=True)
        google_maps = location_url(location + ", " + city)
        location = location.replace("\n", "").strip() + ", " + city
    else:
        google_maps = location_url(city)
        
    return location, google_maps

def check_right_date(date_: date) -> bool:
    today = date.today()
    final_date = today + timedelta(days=6)
    
    return today <= date_ <= final_date

def check_is_senior(title: str) -> bool:
    return "senior" in title.lower() or "seniors" in title.lower()