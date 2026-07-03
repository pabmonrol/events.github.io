import requests
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator
from typing import List, NamedTuple
from datetime import date, timedelta
from backend.classifier import event_classification
import dateparser
from backend.utils import get_price, get_hour, check_location
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
    events = soup.find_all(class_="mega-link-overlay")
    unique_urls = set(event_.get('href') for event_ in events if event_.get('href'))

    today = date.today()
    final_date = today + timedelta(days=6)

    for event in unique_urls:
        page = requests.get(event).text
        soup_page = BeautifulSoup(page, 'html.parser')
        date_text = soup_page.find(class_="sw-date")
        title_text = soup_page.find(class_="sw-title")
        if not date_text or not title_text:
            continue
        
        date_ = dateparser.parse(date_text.text).date()
        if today <= date_ <= final_date:
            title = translator.translate(title_text.text)
            category, icon, colour = event_classification(title)
            if category not in avoid_categories:
                hour_ = soup_page.find('div', class_="event-time")
                if hour_:
                    hour = get_hour(hour_.get_text(strip=True))
                location, google_maps = check_location(soup_page.find(class_="event-location"), city)
                description_text = soup_page.find(class_="sw-description")
                
                if description_text:
                    description = translator.translate(description_text.text)
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
                                price=price))
        else:
            continue
    return res







