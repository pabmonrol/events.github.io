from deep_translator import GoogleTranslator
from towns.ruggell import scraper_ruggell
from towns.mauren import scraper_mauren
from backend.utils import events_to_json, filter_next_7_days
from pathlib import Path

SCRAPERS = [scraper_ruggell, scraper_mauren]

avoid_categories = {"Government", "Religion"}
translator = GoogleTranslator(source='de', target='en')

def run_all_scrapers():
    eventos_totales = []
    
    for scraper in SCRAPERS:
        eventos_comunidad = filter_next_7_days(scraper(avoid_categories, translator))
        eventos_totales.extend(eventos_comunidad)

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