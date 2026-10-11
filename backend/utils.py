from urllib import parse
from pathlib import Path
from typing import NamedTuple, List, Tuple
from datetime import datetime, date, time, timedelta
import json
import re
import tempfile
import threading
import requests
from bs4 import Tag

http_session = requests.Session()

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
_en_ready = False
_installed_targets = []

CONTENT_LANG_ORDER = ("en", "es", "it", "de", "sr", "fr", "pt", "pl", "hi", "ru")
PIVOT_TARGETS = ("es", "it", "sr", "fr", "pt", "pl", "hi", "ru")
SR_MODEL_URL = "https://argos-net.com/v1/translate-en_sr-1_9.argosmodel"

class TranslatedText(str):
    def __new__(cls, english: str, by_lang: dict):
        obj = str.__new__(cls, english)
        obj.by_lang = dict(by_lang)
        return obj

    def __add__(self, other):
        if isinstance(other, TranslatedText):
            keys = set(self.by_lang) | set(other.by_lang)
            merged = {key: self.by_lang.get(key, "") + other.by_lang.get(key, "") for key in keys}
            return TranslatedText(str.__add__(self, other), _ordered_langs(merged))
        if isinstance(other, str):
            merged = {key: value + other for key, value in self.by_lang.items()}
            return TranslatedText(str.__add__(self, other), merged)
        return NotImplemented

    def __radd__(self, other):
        if isinstance(other, str) and not isinstance(other, TranslatedText):
            merged = {key: other + value for key, value in self.by_lang.items()}
            return TranslatedText(other + str.__str__(self), merged)
        return NotImplemented

def _ordered_langs(by_lang: dict) -> dict:
    return {code: by_lang[code] for code in CONTENT_LANG_ORDER if code in by_lang}

def _pair_installed(from_code: str, to_code: str) -> bool:
    import argostranslate.translate

    installed = argostranslate.translate.get_installed_languages()
    from_lang = next((lang for lang in installed if lang.code == from_code), None)
    to_lang = next((lang for lang in installed if lang.code == to_code), None)
    if from_lang is None or to_lang is None:
        return False
    return from_lang.get_translation(to_lang) is not None

def _install_serbian_model() -> bool:
    import argostranslate.package

    try:
        response = http_session.get(SR_MODEL_URL, timeout=180)
        response.raise_for_status()
        model_path = Path(tempfile.gettempdir()) / "translate-en_sr-1_9.argosmodel"
        model_path.write_bytes(response.content)
        argostranslate.package.install_from_path(str(model_path))
        return _pair_installed("en", "sr")
    except Exception as exc:
        print(f"Serbian Argos package could not be installed: {exc}")
        return False

def _install_pair(from_code: str, to_code: str, available) -> bool:
    import argostranslate.package

    package = next(
        (pkg for pkg in available if pkg.from_code == from_code and pkg.to_code == to_code),
        None,
    )
    try:
        if package is not None:
            argostranslate.package.install_from_path(package.download())
            return _pair_installed(from_code, to_code)
        if from_code == "en" and to_code == "sr":
            return _install_serbian_model()
    except Exception as exc:
        print(f"Could not install Argos package {from_code}->{to_code}: {exc}")
    return False

def ensure_translation_packages() -> None:
    global _translation_ready, _en_ready, _installed_targets
    if _translation_ready:
        return

    with _install_lock:
        if _translation_ready:
            return

        import argostranslate.package
        import argostranslate.settings

        available = []
        try:
            argostranslate.package.update_package_index()
            if argostranslate.settings.local_package_index.exists():
                available = argostranslate.package.get_available_packages()
        except Exception as exc:
            print(f"Could not update the Argos package index: {exc}")

        if not _pair_installed("de", "en"):
            if not _install_pair("de", "en", available):
                print("German to English Argos package is not available")

        for code in PIVOT_TARGETS:
            if _pair_installed("en", code):
                continue
            if not _install_pair("en", code, available):
                print(f"English to {code} Argos package is not available")

        _en_ready = _pair_installed("de", "en")
        _installed_targets = [code for code in PIVOT_TARGETS if _pair_installed("en", code)]
        _translation_ready = True

def translate_text(value) -> str:
    original = _as_text(value)
    if not original:
        return ""

    try:
        import argostranslate.translate

        ensure_translation_packages()
        by_lang = {"de": original}
        with _install_lock:
            english = ""
            if _en_ready:
                english = argostranslate.translate.translate(original, "de", "en") or ""
            by_lang["en"] = english or original
            if english:
                for code in _installed_targets:
                    try:
                        translated = argostranslate.translate.translate(english, "en", code) or ""
                    except Exception as exc:
                        print(f"Translation to {code} failed: {exc}")
                        translated = ""
                    if translated:
                        by_lang[code] = translated
        ordered = _ordered_langs(by_lang)
        return TranslatedText(ordered["en"], ordered)
    except Exception as exc:
        print(f"Translation failed, keeping original: {exc}")
        return TranslatedText(original, {"de": original, "en": original})

def location_url(location: str) -> str:
    base_url = "https://www.google.com/maps/search/?"
    parametros = {
        "api": "1",
        "query": location
    }
    query_string = parse.urlencode(parametros)

    return base_url + query_string

def ensure_town(location, community) -> str:
    loc = _as_text(location)
    town = _as_text(community)
    if not town:
        return loc
    if not loc:
        return town
    if town.lower() in loc.lower():
        return loc
    return f"{loc}, {town}"

def _export_text(value):
    if isinstance(value, TranslatedText):
        return dict(value.by_lang)
    return value

def events_to_json(events_list: List[NamedTuple]) -> str:
    def json_serial(obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        if isinstance(obj, time):
            return obj.strftime("%H:%M")
        raise TypeError(f"Tipo {type(obj)} no es serializable en JSON")

    lista_diccionarios = []
    for evento in events_list:
        record = evento._asdict()
        record["title"] = _export_text(record.get("title"))
        record["description"] = _export_text(record.get("description"))
        if record.get("community"):
            record["location"] = ensure_town(record.get("location"), record.get("community"))
            record["google_maps"] = location_url(record["location"])
        lista_diccionarios.append(record)

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