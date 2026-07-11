from deep_translator import GoogleTranslator
from typing import *
import requests
from bs4 import BeautifulSoup, Tag
from datetime import date
import dateparser
from backend.utils import check_right_date, get_hour, location_url
from backend.classifier import event_classification
from backend.model import Event


city = "Triesenberg"
avoid_categories = {"Government", "Religion"}
translator = GoogleTranslator(source='de', target='en')

year = str(date.today().year)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
}

def _find_location_triesenberg(data_list: List[Tag], city: str) -> str|Tag:
    res = city
    for data in data_list:
        title_data = data.find("h3")
        if title_data == "Veranstaltungsort":
            res = data.find("p").text
    
    return res

def _find_description_triesenberg(data_list: List[Tag]) -> str:
    res = ""
    for data in data_list:
        title_data = data.find("h3")
        if title_data == "Details":
            res = data.find("p").text
    
    return res

def scraper_triesenberg(url: str) -> List[NamedTuple]:
    res = []

    hour = None
    location = city
    google_maps = None
    price = None
    description = ""

    web = requests.get(url, headers=HEADERS).text
    soup = BeautifulSoup(web, 'html.parser')
    links = soup.find_all(class_="grid-item grid-33")

    for link in links:
        date_body = link.find("div", class_="event-overview-date")
        if date_body:
            day_text =  date_body.find("div", class_="day").text
            month_text = date_body.find("div", class_="month").text
            date_text = day_text + "-" + month_text + "-" + year
            date_ = dateparser.parse(date_text, settings={'DATE_ORDER': 'DMY'}).date()

            if not check_right_date(date_):
                continue
            
            title_body = link.find("div", class_="overview-title")
            if title_body:
                title = translator.translate(title_body.text)
                hour_page = link.find("div", class_="overview-date")
                if hour_page and hour_page.text != "":
                    hour = get_hour(hour_page.text)
                    
                event_link= link.find("a", class_="event-overview-item overview-item")
                if not event_link:
                    event_link= link.find("a", class_="event-overview-item overview-item has-image")
                    
                page = requests.get(event_link.get('href'), headers=HEADERS).text
                event = BeautifulSoup(page, 'html.parser')

                category, icon, colour = event_classification(title)

                if category not in avoid_categories:
                    data = event.find_all("div", class_="event-data-item")
                    location = _find_location_triesenberg(data, city)
                    google_maps = location_url(location)

                    description_page = _find_description_triesenberg(data)
                    if description_page:
                        description_text = event.find(class_="eventdetail__textbody mce").find_next("p")
                        description = translator.translate(description_text)
                    
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


