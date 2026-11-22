from bs4 import BeautifulSoup, Tag
import re
from typing import NamedTuple, List, Set
from backend.classifier import event_classification
import dateparser
from backend.model import Event
from datetime import datetime, date, timedelta
from backend.utils import location_url, check_is_senior, check_right_date, translate_text, fetch_text

INFO = {"hour":'Zeit', "location":'Wo'}
city = "Ruggell"
avoid_categories = {"Government", "Religion"}

today = date.today()
final_date = today + timedelta(days=6)

def _clean_detail(attributes: Tag, info: str) -> str | None:
    for b in attributes.find_all('b'):
        texto_al_lado = b.next_sibling

        if info in b.text and info == INFO.get("hour"):
            if texto_al_lado:
                match = re.search(r'\d{1,2}\.\d{2}', texto_al_lado)
                if match:
                    return match.group()
                    
        elif info in b.text and info == INFO.get("location"):
            return texto_al_lado.strip() if texto_al_lado else None
            
    # Si termina el bucle y no entró en ningún 'if', devuelve None
    return None

def scraper_ruggell(url: str) -> List[NamedTuple]:
    res = []
    seen = set()

    while url and url not in seen:
        seen.add(url)

        web = fetch_text(url)
        soup = BeautifulSoup(web, 'html.parser')
        events = soup.find_all(class_='infos')

        hour = None
        location = city
        google_maps = None
        price = None
        reached_limit = False

        for event in events:
            description = None

            if not event.find(class_='date') or not event.find(class_='title'):
                continue

            parsed = dateparser.parse(event.find(class_='date').text)
            if parsed is None:
                continue
            date_ = parsed.date()
            if date_ >= final_date:
                reached_limit = True
            if not check_right_date(date_):
                continue

            title = translate_text(event.find(class_='title').text)

            if check_is_senior(title):
                continue

            description = event.find(class_='text').text
            description = translate_text(description)

            category, icon, colour = event_classification(" ".join([title, description]))
            if category in avoid_categories:
                continue

            attributes = event.find(class_='attributes')
            if attributes:
                hour_text = _clean_detail(attributes, INFO.get("hour"))
                location_text = _clean_detail(attributes, INFO.get("location"))
                if hour_text:
                    hour = datetime.strptime(hour_text, "%H.%M").time()
                if location_text:
                    location = str(location_text).strip()
                    google_maps = location_url(location_text)
            ev = Event(community=city,
                            title=title,
                            icon=icon,
                            colour=colour,
                            category=category,
                            date=date_,
                            time=hour,
                            location=location,
                            google_maps=google_maps,
                            description=description,
                            price=price
                            )
            res.append(ev)

        if reached_limit:
            break

        next_month_btn = soup.find('a', class_='arrow-right', id='content_aR')
        if next_month_btn is None or not next_month_btn.get('href'):
            break
        url = f"https://www.ruggell.li{next_month_btn.get('href')}"

    return res
