from towns.ruggell import scraper_ruggell
from towns.mauren import scraper_mauren
from towns.gamprin_bendern import scraper_gamprin_bendern
from towns.schellenberg import scraper_schellenberg
from towns.eschen import scraper_eschen
from towns.schaan import scraper_schaan
from towns.vaduz import scraper_vaduz
from towns.triesen import scraper_trissen
from towns.triesenberg import scraper_triesenberg
from towns.balzers import scraper_balzers
from backend.utils import events_to_json, filter_next_7_days
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from datetime import date
import json

SCRAPERS = {scraper_ruggell: "https://www.ruggell.li/agenda",
            scraper_mauren: "https://www.mauren.li",
            scraper_gamprin_bendern: "https://www.gamprin.li/leben-gemeinschaft/veranstaltungen",
            scraper_schellenberg: "https://www.schellenberg.li/gemeinde/gesellschaft/veranstaltungen",
            scraper_eschen: "https://www.eschen.li/leben-soziales/agenda/",
            scraper_schaan: "https://www.schaan.li/veranstaltungen",
            scraper_vaduz: "https://www.vaduz.li/veranstaltungen",
            scraper_trissen: "https://www.triesen.li/agenda",
            scraper_triesenberg: "https://www.triesenberg.li/dorfleben/aktuelles/veranstaltungen/",
            scraper_balzers: "https://www.balzers.li/de/balzers-erleben/veranstaltungen/tblid/45"
            }
def archive_expired_special_events():
    ruta_special = Path("data/data_special.json")
    ruta_old_special = Path("data/old_data_special.json")

    today = date.today()
    with open(ruta_special, "r", encoding="utf-8") as f_special:
        special_events = json.load(f_special)

    expired_special_events = [evento for evento in special_events if date.fromisoformat(evento["date"]) < today]
    active_special_events = [evento for evento in special_events if date.fromisoformat(evento["date"]) >= today]

    if expired_special_events:
        old_special_events = []

        with open(ruta_old_special, "r", encoding="utf-8") as f_old_special:
            old_special_events = json.load(f_old_special)

        with open(ruta_old_special, "w", encoding="utf-8") as f_old_special:
            json.dump(old_special_events + expired_special_events, f_old_special, ensure_ascii=False, indent=2)

        with open(ruta_special, "w", encoding="utf-8") as f_special:
            json.dump(active_special_events, f_special, ensure_ascii=False, indent=2)

def run_all_scrapers():
    eventos_totales = []

    scrapers_funciones = list(SCRAPERS.keys())
    scrapers_urls = list(SCRAPERS.values())

    with ThreadPoolExecutor(max_workers=len(SCRAPERS)) as executor:
        resultados = executor.map(
            lambda fn, url: filter_next_7_days(fn(url)), 
            scrapers_funciones, 
            scrapers_urls
        )
        for eventos in resultados:
            eventos_totales.extend(eventos)

    if eventos_totales:
        json_resultado = events_to_json(eventos_totales)
        ruta_data = Path("data/data.json")
        
        if ruta_data.exists():
            with open("data/data.json", "r", encoding="utf-8") as f_actual:
                contenido_actual = f_actual.read()
                
            with open("data/old_data.json", "w", encoding="utf-8") as f_viejo:
                f_viejo.write(contenido_actual)
                
        ruta_data.unlink(missing_ok=True)
        
        with open("data/data.json", "w", encoding="utf-8") as f:
            f.write(json_resultado)


if __name__ == "__main__":
    archive_expired_special_events()
    run_all_scrapers()