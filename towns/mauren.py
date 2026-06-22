import requests
from bs4 import BeautifulSoup
import re
from deep_translator import GoogleTranslator
from typing import NamedTuple, List, Set, Optional
from backend.classifier import event_classification
import dateparser
from backend.model import Event
from datetime import datetime, time
from backend.utils import location_url

INFO = {"hour":'Zeit', "location":'Wo'}

city, url = "Mauren", "https://www.mauren.li/agenda"

web = requests.get(url).text

sopa = BeautifulSoup(web, 'html.parser')

links_events = sopa.find_all(class_='agenda__itemlink')
events = ["https://www.mauren.li"+link.get('href') for link in links_events]
avoid_categories = {"Government", "Religion"}
translator = GoogleTranslator(source='de', target='en')

def _get_price(description: str)->float:
    if not description:
        return None

    text_lower = description.lower()

    pattern = r'(?:chf\s*(\d+(?:[.,]\d+)?))|(\d+(?:[.,]\d+)?)(?:\.-)?\s*chf'
    
    match = re.search(pattern, text_lower)
    if match:
        price_str = match.group(1) or match.group(2)
        price_str = price_str.replace(',', '.')
        return float(price_str)
    
def _get_hour(hour_text: str) -> time:
    match = re.search(r'\d{1,2}\.\d{2}', hour_text)
    if match:
        hour_re = match.group(0)
        return datetime.strptime(hour_re, "%H.%M").time()
    return None

def _find_value(sopa_, tag: str) -> Optional[str]:
    item = sopa_.find('li', class_="sidelist__item", attrs={"data-name":tag})
    if item:
        text = item.find('span', class_="sidelist__text").text
        if text:
            return text

def scraper_mauren(avoid_categories: Set[str], translator) -> List[NamedTuple]:
    res = []

    hour = None
    location = city
    google_maps = None
    price = None

    for event in events:
        description = None

        html_evento = requests.get(event).text
        sopa_evento = BeautifulSoup(html_evento, 'html.parser')

        date_text = _find_value(sopa_evento, "Datum")
        title_text = sopa_evento.find(class_="eventdetail__headline page__headline")
        if not date_text or not title_text:
            continue

        title = translator.translate(title_text.text)
        category, icon, colour = event_classification(title)
        if category not in avoid_categories:
            date_ = dateparser.parse(date_text).date()
            hour = _get_hour(_find_value(sopa_evento, "Zeit"))
            location = _find_value(sopa_evento, "Ort")
            google_maps = location_url(location)
            description_text = translator.translate(sopa_evento.find(class_="eventdetail__textbody mce").text)
            if description_text:
                description = description_text
            price = _get_price(description)
        
            res.append(Event(title=title,
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
