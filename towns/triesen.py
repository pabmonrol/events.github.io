from typing import *
from bs4 import BeautifulSoup, Tag
import dateparser
import re
from datetime import date, timedelta
from backend.utils import check_right_date, get_hour, check_location, check_is_senior, translate_text, fetch_text
from backend.classifier import event_classification
from backend.model import Event



INFO = {"hour":'Zeit', "location":'Wo'}
city = "Triesen"
avoid_categories = {"Government", "Religion"}

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

def scraper_trissen(url: str) -> List[NamedTuple]:
    res = []

    hour = None
    location = city
    google_maps = None
    price = None
    description = ""

    web = fetch_text(url)
    soup = BeautifulSoup(web, 'html.parser')
    events = soup.find_all(class_="event")

    limite_superaged = False
    fecha_limite = date.today() + timedelta(days=6)

    for event in events:
        title_body = event.find("h3", class_="title")
        date_body = event.find("div", class_="date")
        if date_body and title_body:
            date_ = dateparser.parse(date_body.text, languages=["de"]).date()

            if date_ > fecha_limite:
                limite_superaged = True

            if not check_right_date(date_):
                continue
            title = translate_text(title_body.text)

            if check_is_senior(title):
                continue

            category, icon, colour = event_classification(" ".join([title, description]))

            if category not in avoid_categories:
                attributes = event.find(class_='attributes')
                if attributes:
                    hour_text = _clean_detail(attributes, INFO.get("hour"))
                    location_text = _clean_detail(attributes, INFO.get("location"))
                    if hour_text:
                        hour = get_hour(hour_text)
                    if location_text:
                        location, google_maps = check_location(location_text, city)

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
    if not limite_superaged:
        next_month_btn = soup.find('a', class_="arrow-right", id="content_aR")
        if next_month_btn and next_month_btn.get('href'):
            next_url = f"https://www.triesen.li{next_month_btn.get('href')}"
        res.extend(scraper_trissen(next_url))
    return res
