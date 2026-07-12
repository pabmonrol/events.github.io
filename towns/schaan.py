from deep_translator import GoogleTranslator
from typing import *
import requests
from bs4 import BeautifulSoup
from datetime import date, timedelta
import re
import dateparser
from backend.utils import check_right_date, get_hour, check_location, get_price, check_is_senior
from backend.classifier import event_classification
from backend.model import Event


city = "Schaan"
avoid_categories = {"Government", "Religion"}
translator = GoogleTranslator(source='de', target='en')

def scraper_schaan(url: str) -> List[NamedTuple]:
    res = []

    hour = None
    location = city
    google_maps = None
    price = None
    description = ""

    web = requests.get(url).text
    soup = BeautifulSoup(web, 'html.parser')
    links = soup.find_all(class_="sw-list-item")


    for link in links:
        title_link = link.find(class_="sw-title").find('a').get('href')
        date_text = link.find(class_="sw-date")
        if date_text and title_link:
            date_match = re.findall(r"\d{1,2}\.\d{2}\.\d{4}", date_text.text)
            date_ = dateparser.parse(date_match[0], settings={'DATE_ORDER': 'DMY'}).date()
            
            if not check_right_date(date_):
                continue
            page = requests.get(title_link).text
            event = BeautifulSoup(page, 'html.parser')

            title = translator.translate(event.find(class_="sw-title").text)

            if check_is_senior(title):
                continue

            description_page = event.find("div", class_="vier")
            if description_page:
                description_text = event.find(class_="eventdetail__textbody mce").find_next("p")
                description = translator.translate(description_text)
                price = get_price(description_text)

            category, icon, colour = event_classification(" ".join([description, title]))
            if category in avoid_categories:
                continue

            hour_page = event.find(class_="sw-date")
            hour_text = re.findall(r"\d{1,2}:\d{2}", hour_page.text)
            hour = get_hour(hour_text[0])

            location_ = event.find("a", class_="primary-color")
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
    return res

        

        