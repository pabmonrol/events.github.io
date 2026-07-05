from deep_translator import GoogleTranslator
from typing import List, NamedTuple
import requests
from bs4 import BeautifulSoup
from datetime import date, timedelta
import dateparser
from backend.classifier import event_classification
from backend.utils import check_location
from backend.model import Event
import re

city = "Eschen"
avoid_categories = {"Government", "Religion"}
translator = GoogleTranslator(source='de', target='en')

def scraper_eschen(url: str) -> List[NamedTuple]:
    res = []

    hour = None
    location = city
    google_maps = None
    price = None
    description = ""

    web = requests.get(url).text
    soup = BeautifulSoup(web, 'html.parser')
    links = soup.find_all(class_="link--underline clickable-parent")

    for link in links:
        page = requests.get(link.get('href')).text
        event = BeautifulSoup(page, 'html.parser')

        title = event.select_one("main h1.ct-headline span")
        date_page = event.find(text=re.compile("Datum:")).find_next(class_="ct-code-block")

        today = date.today()
        final_date = today + timedelta(days=6)

        if not title or not date_page:
            continue
        
        date_match = re.findall(r"\d{1,2}\.\d{2}\.\d{4}", date_page.text)
        date_ = dateparser.parse(date_match[0], settings={'DATE_ORDER': 'DMY'}).date()
        if today <= date_ <= final_date:
            title = translator.translate(title.text)
            category, icon, colour = event_classification(title)
            if category not in avoid_categories:
                hour = event.find("b", text=re.compile("Uhrzeit:")).find_next("span").get_text(strip=True)
                location_ = event.find("b", text=re.compile("Ort:")).find_next("span")
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
