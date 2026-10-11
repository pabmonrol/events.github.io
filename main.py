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
from backend.utils import events_to_json, filter_next_7_days, ensure_translation_packages
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from datetime import date
import json
import traceback

SCRAPERS = {scraper_ruggell: "https://www.ruggell.li/agenda",
            scraper_mauren: "https://www.mauren.li",
            scraper_gamprin_bendern: "https://www.gamprin.li/leben-gemeinschaft/veranstaltungen",
            scraper_schellenberg: "https://www.schellenberg.li/gemeinde/gesellschaft/veranstaltungen",
            scraper_eschen: "https://www.eschen.li/leben-soziales/agenda/",
            scraper_schaan: "https://www.schaan.li/veranstaltungen",
            scraper_vaduz: "https://www.vaduz.li/veranstaltungen",
            scraper_trissen: "https://www.triesen.li/agenda",
            scraper_triesenberg: "https://www.triesenberg.li/dorfleben/aktuelles/veranstaltungen/",
            scraper_balzers: "https://www.balzers.li/de/balzers-erleben/veranstaltungen/tblid/45",
            #scraper_
            }


def load_json_list(path):
    with open(path, "r", encoding="utf-8") as file:
        content = file.read().strip()
        if not content:
            return []

        data = json.loads(content)
        return data if isinstance(data, list) else []


def merge_unique_records(existing_records, new_records):
    merged_records = list(existing_records)
    seen_records = {
        json.dumps(record, sort_keys=True, ensure_ascii=False)
        for record in merged_records
    }

    for record in new_records:
        record_signature = json.dumps(record, sort_keys=True, ensure_ascii=False)
        if record_signature not in seen_records:
            merged_records.append(record)
            seen_records.add(record_signature)

    return merged_records


def archive_expired_special_events():
    ruta_special = Path("data/data_special.json")
    ruta_old_special = Path("data/old_data_special.json")

    today = date.today()
    special_events = load_json_list(ruta_special)

    expired_special_events = [evento for evento in special_events if date.fromisoformat(evento["date"]) < today]
    active_special_events = [evento for evento in special_events if date.fromisoformat(evento["date"]) >= today]

    if expired_special_events:
        old_special_events = load_json_list(ruta_old_special)
        updated_old_special_events = merge_unique_records(old_special_events, expired_special_events)

        with open(ruta_old_special, "w", encoding="utf-8") as f_old_special:
            json.dump(updated_old_special_events, f_old_special, ensure_ascii=False, indent=2)

        with open(ruta_special, "w", encoding="utf-8") as f_special:
            json.dump(active_special_events, f_special, ensure_ascii=False, indent=2)


def scrape_and_filter(scraper_fn, url):
    return filter_next_7_days(scraper_fn(url))

def run_all_scrapers():
    ensure_translation_packages()
    eventos_totales = []
    failures = []

    with ThreadPoolExecutor(max_workers=len(SCRAPERS)) as executor:
        futures = {
            executor.submit(scrape_and_filter, scraper_fn, url): scraper_fn.__name__
            for scraper_fn, url in SCRAPERS.items()
        }

        for future, name in futures.items():
            try:
                events = future.result()
                eventos_totales.extend(events)
                print(f"{name}: {len(events)} events")
            except Exception:
                failures.append((name, traceback.format_exc()))
                print(f"Scraper failed: {name}\n{traceback.format_exc()}")

    if failures:
        failed_names = ", ".join(name for name, _ in failures)
        print(f"{len(failures)} scrapers failed: {failed_names}")

    if not eventos_totales:
        raise SystemExit("No events scraped")

    json_resultado = events_to_json(eventos_totales)
    ruta_data = Path("data/data.json")
    ruta_old_data = Path("data/old_data.json")

    current_data = load_json_list(ruta_data) if ruta_data.exists() else []
    old_data = load_json_list(ruta_old_data)
    updated_old_data = merge_unique_records(old_data, current_data)

    with open(ruta_old_data, "w", encoding="utf-8") as f_viejo:
        json.dump(updated_old_data, f_viejo, ensure_ascii=False, indent=2)

    ruta_data.unlink(missing_ok=True)

    with open("data/data.json", "w", encoding="utf-8") as f:
        f.write(json_resultado)


if __name__ == "__main__":
    archive_expired_special_events()
    run_all_scrapers()