from deep_translator import GoogleTranslator
from towns.ruggell import scraper_ruggell
from towns.mauren import scraper_mauren
from backend.utils import events_to_json, filter_next_7_days
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

SCRAPERS = {scraper_ruggell: "https://www.ruggell.li/agenda",
            scraper_mauren: "https://www.mauren.li"}

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
    run_all_scrapers()