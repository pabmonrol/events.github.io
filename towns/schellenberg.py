from typing import List, NamedTuple
from bs4 import BeautifulSoup
import dateparser
from backend.classifier import event_classification
from backend.model import Event
from backend.utils import get_hour, check_location, check_is_senior, check_right_date, translate_text, fetch_text


city = "Schellenberg"
avoid_categories = {"Government", "Religion"}


def scraper_schellenberg(url: str) -> List[NamedTuple]:
    res = []

    hour = None
    location = city
    google_maps = None
    price = None
    description = ""

    web = fetch_text(url)
    soup = BeautifulSoup(web, 'html.parser')
    events = soup.find_all(class_="eventrow eventslist__row")

    for event in events:
        hour = None
        location = city
        google_maps = None
        price = None
        description = ""

        date_tag = event.find(class_="sr-only")
        title_page = event.find(class_="eventrow__title title3")
        if not date_tag or not title_page:
            continue

        date_ = dateparser.parse(date_tag.get("datetime")).date()
        if not check_right_date(date_):
            continue

        title = translate_text(title_page.text)
        if check_is_senior(title):
            continue

        category, icon, colour = event_classification(" ".join([title, description]))
        if category in avoid_categories:
            continue

        hour = get_hour(event.find("time", class_="text").text)

        location_tag = event.find("div", class_="eventrow__location")
        location, google_maps = check_location(location_tag, city)

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
