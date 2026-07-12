from deep_translator import GoogleTranslator
from typing import *
import requests
from bs4 import BeautifulSoup, Tag
import re
import dateparser
from backend.utils import check_right_date, get_hour, get_price, location_url, check_is_senior
from backend.classifier import event_classification
from backend.model import Event


city = "Vaduz"
avoid_categories = {"Government", "Religion"}
translator = GoogleTranslator(source='de', target='en')

def _clean_vaduz_location(tags_desc: List[Tag]) -> Tuple[str]:
    strings = []
    for tag in tags_desc:
        line = tag.text.strip().replace("\t", "")
        strings.append(line)
    location_string = "\n".join(strings) + ", " + city

    return location_string, location_url(location_string)
        

def scraper_vaduz(url: str) -> List[NamedTuple]:
    res = []

    hour = None
    location = city
    google_maps = None
    price = None
    description = ""

    web = requests.get(url).text
    soup = BeautifulSoup(web, 'html.parser')
    links = soup.find_all(class_="small-7 medium-8 large-8 columns col_events_list_text")

    for link in links:
        title_body = link.find("div", class_="ccm-block-page-list-title").find('a')
        date_text = link.find(class_="ccm-block-page-list-date")
        if date_text and title_body:
            date_match = re.findall(r"\d{1,2}\.\d{2}\.\d{4}", date_text.text)
            date_ = dateparser.parse(date_match[0], settings={'DATE_ORDER': 'DMY'}).date()
            if not check_right_date(date_):
                continue
            page = requests.get(title_body.get('href')).text
            event = BeautifulSoup(page, 'html.parser')

            title = translator.translate(title_body.text)

            if check_is_senior(title):
                continue

            title_description_page = event.find("div", class_="summary").find_next("strong")
            description_page = event.find("div", class_="description").find_next("p")
            if title_description_page or description_page:
                title_description = translator.translate(title_description_page.text)
                description_body = translator.translate(description_page.text)
                description = title_description + "\n\n" + description_body
                price_text = event.find("div", class_="additional-info-wrapper").find_next("p")
                price = get_price(price_text.text)

            category, icon, colour = event_classification(" ".join([description, title]))
            if category in avoid_categories:
                continue

            hour_page = event.find("div", class_="schedule-block")
            hour_text = re.findall(r"\b(\d{1,2}:\d{2})\b", hour_page.text)
            if len(hour_text) != 0:
                hour = get_hour(hour_text[0])

            location_ = event.find("div", class_="row event-location-map-wrapper").find_all("div", class_="description-wrapper")
            location, google_maps = _clean_vaduz_location(location_)

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

