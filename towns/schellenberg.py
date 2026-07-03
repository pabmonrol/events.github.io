from deep_translator import GoogleTranslator
from typing import List, NamedTuple
import requests
from bs4 import BeautifulSoup
from datetime import date, timedelta
import dateparser
from backend.classifier import event_classification
from backend.model import Event
from backend.utils import get_hour, check_location

city = "Schellenberg"
avoid_categories = {"Government", "Religion"}
translator = GoogleTranslator(source='de', target='en')

def scraper_schellenberg(url: str) -> List[NamedTuple]:
    res = []

    hour = None
    location = city
    google_maps = None
    price = None
    description = ""

    web = requests.get(url).text
    soup = BeautifulSoup(web, 'html.parser')
    events = soup.find_all(class_="eventrow eventslist__row")

    today = date.today()
    final_date = today + timedelta(days=6)

    for event in events:
        if not event.find(class_="sr-only") or not event.find(class_="eventrow__title title3"):
            continue
        date_text = event.find(class_="sr-only").get("datetime")
        date_ = dateparser.parse(date_text).date()
        if today <= date_ <= final_date:
            title = translator.translate(event.find(class_="eventrow__title title3").text)
            category, icon, colour = event_classification(title)

            if category not in avoid_categories:
                hour_text = event.find("time", class_="text").text
                hour = get_hour(hour_text)

                location_ = event.find("div", class_="eventrow__location")
                location, google_maps = check_location(location_, city)
        
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
        else:
            continue
    return res




