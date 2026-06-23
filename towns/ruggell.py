import requests
from bs4 import BeautifulSoup, Tag
import re
from typing import NamedTuple, List, Set
from deep_translator import GoogleTranslator
from backend.classifier import event_classification
import dateparser
from backend.model import Event
from datetime import datetime
from backend.utils import location_url

INFO = {"hour":'Zeit', "location":'Wo'}
city, url = "Ruggell", "https://www.ruggell.li/agenda"
web = requests.get(url).text
soup = BeautifulSoup(web, 'html.parser')
avoid_categories = {"Government", "Religion"}
translator = GoogleTranslator(source='de', target='en')
events = soup.find_all(class_='infos')

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

def scraper_ruggell() -> List[NamedTuple]:
    res = []

    hour = None
    location = city
    google_maps = None
    price = None

    for event in events:
        description = None

        if not event.find(class_='date') or not event.find(class_='title'):
            continue

        title = translator.translate(event.find(class_='title').text)
        category, icon, colour = event_classification(title)
        if category not in avoid_categories:
            description = translator.translate(event.find(class_='text').text)
            date_ = dateparser.parse(event.find(class_='date').text).date()

            attributes = event.find(class_='attributes')
            if attributes:
                hour_text = _clean_detail(attributes, INFO.get("hour"))
                location_text = _clean_detail(attributes, INFO.get("location"))
                if hour_text:
                    hour = datetime.strptime(hour_text, "%H.%M").time()
                if location_text:
                    location = str(location_text).strip()
                    google_maps = location_url(location_text)

            res.append(Event(comunity=city,
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
                            ))
        else:
            continue

    return res