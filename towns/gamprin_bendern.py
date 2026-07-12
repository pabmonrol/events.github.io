import requests
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator
from typing import List, NamedTuple
from datetime import date, timedelta
from urllib.parse import urljoin, urlparse
from backend.classifier import event_classification
import dateparser
from backend.utils import get_price, get_hour, check_location, check_is_senior, check_right_date
from backend.model import Event


city = "Gamprin/Bendern"
avoid_categories = {"Government", "Religion"}
translator = GoogleTranslator(source='de', target='en')

def scraper_gamprin_bendern(url: str) -> List[NamedTuple]:
    res = []

    hour = None
    location = city
    google_maps = None
    price = None
    description = ""

    web = requests.get(url).text
    soup = BeautifulSoup(web, 'html.parser')
    events = soup.find_all("div", class_="events-list-entry ccm-block-page-list-page-entry")

    year = str(date.today().year)

    for event in events:
        event_link = event.find(class_="mega-link-overlay").get('href')
        event_url = urljoin(url, event_link)
        parsed_event = urlparse(event_url)

        if parsed_event.netloc == "www.gamprin.li" and parsed_event.path in ("", "/"):
            title_text = event.find_next("div", class_="mega-link-overlay").find("a").text
            title = translator.translate(title_text.text)
            
            if check_is_senior(title):
                continue

            category, icon, colour = event_classification(title)
            if category in avoid_categories:
                continue

            day = event.find_next(class_="day").text
            month = event.find_next(class_="month").text
            date_string = day + "-" + month + "-" + year
            date_ = dateparser.parse(date_string, settings={'DATE_ORDER': 'DMY'}).date()

            if not check_right_date(date_):
                continue

            hour_text = event.find_next("div", class_="event-list-time")
            if hour_text:
                hour = get_hour(hour_text.text)
        else: 
            page = requests.get(event_url).text
            soup_page = BeautifulSoup(page, 'html.parser')
            date_text = soup_page.find(class_="sw-date")
            title_text = soup_page.find(class_="sw-title")
            if not date_text or not title_text:
                continue
            
            date_ = dateparser.parse(date_text.text).date()
            if not check_right_date(date_):
                continue
            
            title = translator.translate(title_text.text)
            if check_is_senior(title):
                continue
            
            hour_ = soup_page.find('div', class_="event-time")
            if hour_:
                hour = get_hour(hour_.get_text(strip=True))
            location, google_maps = check_location(soup_page.find(class_="event-location"), city)
            description_text = soup_page.find(class_="sw-description")
            
            if description_text:
                description = translator.translate(description_text.text)
                price = get_price(description)

            category, icon, colour = event_classification(" ".join([description, title]))
            if category in avoid_categories:
                continue                    

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
                        price=price))
    return res







