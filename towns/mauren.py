import requests
from bs4 import BeautifulSoup
import re
from typing import NamedTuple, List, Set, Optional
from backend.classifier import event_classification
import dateparser
from backend.model import Event
from datetime import time, date, timedelta
from backend.utils import location_url, verificar_fecha_limite, get_price, check_is_senior, check_right_date, translate_text


city = "Mauren"
avoid_categories = {"Government", "Religion"}


def _find_value(sopa_, tag: str) -> Optional[str]:
    item = sopa_.find('li', class_="sidelist__item", attrs={"data-name":tag})
    if item:
        text = item.find('span', class_="sidelist__text").text
        if text:
            return f"{text}, {city}"
        
def _next_content(soup_page) -> Optional[str]:
    next_links_events = soup_page.find(class_='agenda__itemlink')
    if next_links_events:
        ul_element = next_links_events.find('ul', class_='insidenav__list')
        if ul_element:
            lis = ul_element.find_all('li')
            if len(lis) > 1:
                return lis[1].get('href')
    return None

def _get_hour(hour_text: str) -> time:
    patron = r'(\d{1,2})(?:[:.](\d{2}))?(?:[:.]\d{2})?\s*([ap]\.?m\.?|uhr|h(?:oras?)?)?'
    
    for match in re.finditer(patron, hour_text, re.IGNORECASE):
        hora_str = match.group(1)
        minuto_str = match.group(2)
        indicador_str = match.group(3)

        # Filtro: Ahora también dejamos pasar si encuentra la palabra "Uhr" o "h"
        if not minuto_str and not indicador_str:
            continue

        hour = int(hora_str)
        minute = int(minuto_str) if minuto_str else 0
        
        if indicador_str:
            indicador = re.sub(r'[\s.]', '', indicador_str.lower())
            
            if indicador == 'pm' and hour < 12:
                hour += 12
            elif indicador == 'am' and hour == 12:
                hour = 0
        
        if 0 <= hour <= 23 and 0 <= minute <= 59:
            return time(hour, minute)
            
    return None

def _get_list_events(events_cont, hour: time, location: str, google_maps: str, price: float):
    res = []

    for event in events_cont:
        description = ""

        html_evento = requests.get(event).text
        sopa_evento = BeautifulSoup(html_evento, 'html.parser')

        date_item = sopa_evento.find('li', class_="sidelist__item", attrs={"data-name": "Datum"})
        date_span = date_item.find('span', class_="sidelist__text") if date_item else None
        date_text = date_span.get_text(strip=True) if date_span else ""
        title_text = sopa_evento.find(class_="eventdetail__headline page__headline")
        if not date_text or not title_text:
            continue

        parsed = dateparser.parse(date_text, languages=["de"], settings={"DATE_ORDER": "DMY"})
        if parsed is None:
            continue
        date_ = parsed.date()
        if not check_right_date(date_):
            continue

        title = translate_text(title_text.text)

        if check_is_senior(title):
            continue
        description = sopa_evento.find(class_="eventdetail__textbody mce")
        if description:
            description = translate_text(description.text)
        else:
            description = ""

        category, icon, colour = event_classification(" ".join([description, title]))
        if category in avoid_categories:
            continue

        hour_text = _find_value(sopa_evento, "Zeit")
        hour = _get_hour(hour_text) if hour_text else None
        location = _find_value(sopa_evento, "Ort") or city
        google_maps = location_url(location)
        price = get_price(description)
    
        res.append(Event(community=city,
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
    return res

def scraper_mauren(url: str) -> List[NamedTuple]:
    final_list = []
    hour = None
    location = city
    google_maps = None
    price = None

    web = requests.get(url + "/agenda").text
    soup = BeautifulSoup(web, 'html.parser')
    links_events = soup.find_all(class_='agenda__itemlink')
    events = [url + link.get('href') for link in links_events]

    event_cont = events

    final_list.extend(_get_list_events(events_cont=event_cont, hour=hour, location=location, google_maps=google_maps, price=price))

    current_soup = soup 

    while not verificar_fecha_limite(final_list):
        next_event_path = _next_content(current_soup)
        if not next_event_path:
            break

        next_event_url = url + next_event_path
        
        web_siguiente = requests.get(next_event_url).text
        current_soup = BeautifulSoup(web_siguiente, 'html.parser')
        
        links_nuevos = current_soup.find_all(class_='agenda__itemlink')
        event_cont_nuevo = [url + link.get('href') for link in links_nuevos]
        
        nuevos_eventos = _get_list_events(events_cont=event_cont_nuevo, hour=hour, location=location, google_maps=google_maps, price=price)
        if not nuevos_eventos:
            break

        final_list.extend(nuevos_eventos)

    return final_list
