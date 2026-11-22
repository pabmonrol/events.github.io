from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path
import json
import traceback

from towns.ruggell import scraper_ruggell
from towns.mauren import scraper_mauren
from towns.gamprin_bendern import scraper_gamprin_bendern
from towns.schellenberg import scraper_schellenberg
from towns.eschen import scraper_eschen
from towns.schaan import scraper_schaan
from towns.vaduz import scraper_vaduz
from towns.triesen import scraper_triesen
from towns.triesenberg import scraper_triesenberg
from towns.balzers import scraper_balzers
from backend.utils import events_to_json, filter_next_7_days, ensure_translation_packages, english_only_record

SCRAPERS = {
    scraper_ruggell: "https://www.ruggell.li/agenda",
    scraper_mauren: "https://www.mauren.li",
    scraper_gamprin_bendern: "https://www.gamprin.li/leben-gemeinschaft/veranstaltungen",
    scraper_schellenberg: "https://www.schellenberg.li/gemeinde/gesellschaft/veranstaltungen",
    scraper_eschen: "https://www.eschen.li/leben-soziales/agenda/",
    scraper_schaan: "https://www.schaan.li/veranstaltungen",
    scraper_vaduz: "https://www.vaduz.li/veranstaltungen",
    scraper_triesen: "https://www.triesen.li/agenda",
    scraper_triesenberg: "https://www.triesenberg.li/dorfleben/aktuelles/veranstaltungen/",
    scraper_balzers: "https://www.balzers.li/de/balzers-erleben/veranstaltungen/tblid/45",
}

DATA_FILE = Path("data/data.json")
OLD_DATA_FILE = Path("data/old_data.json")
SPECIAL_FILE = Path("data/data_special.json")
OLD_SPECIAL_FILE = Path("data/old_data_special.json")


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
        signature = json.dumps(record, sort_keys=True, ensure_ascii=False)
        if signature not in seen_records:
            merged_records.append(record)
            seen_records.add(signature)

    return merged_records


def archive_expired_special_events():
    today = date.today()
    special_events = load_json_list(SPECIAL_FILE)

    expired = [e for e in special_events if date.fromisoformat(e["date"]) < today]
    active = [e for e in special_events if date.fromisoformat(e["date"]) >= today]

    if expired:
        old_special = load_json_list(OLD_SPECIAL_FILE)
        with open(OLD_SPECIAL_FILE, "w", encoding="utf-8") as f:
            json.dump(merge_unique_records(old_special, expired), f, ensure_ascii=False, indent=2)
        with open(SPECIAL_FILE, "w", encoding="utf-8") as f:
            json.dump(active, f, ensure_ascii=False, indent=2)


def scrape_and_filter(scraper_fn, url):
    return filter_next_7_days(scraper_fn(url))


def run_all_scrapers():
    ensure_translation_packages()
    all_events = []
    failures = []

    with ThreadPoolExecutor(max_workers=len(SCRAPERS)) as executor:
        futures = {
            executor.submit(scrape_and_filter, scraper_fn, url): scraper_fn.__name__
            for scraper_fn, url in SCRAPERS.items()
        }

        for future, name in futures.items():
            try:
                events = future.result()
                all_events.extend(events)
                print(f"{name}: {len(events)} events")
            except Exception:
                failures.append((name, traceback.format_exc()))
                print(f"Scraper failed: {name}\n{traceback.format_exc()}")

    if failures:
        failed_names = ", ".join(name for name, _ in failures)
        print(f"{len(failures)} scrapers failed: {failed_names}")

    if not all_events:
        raise SystemExit("No events scraped")

    json_output = events_to_json(all_events)

    current_data = load_json_list(DATA_FILE) if DATA_FILE.exists() else []
    current_data = [english_only_record(record) for record in current_data]
    old_data = load_json_list(OLD_DATA_FILE)

    with open(OLD_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(merge_unique_records(old_data, current_data), f, ensure_ascii=False, indent=2)

    DATA_FILE.unlink(missing_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        f.write(json_output)


if __name__ == "__main__":
    archive_expired_special_events()
    run_all_scrapers()
