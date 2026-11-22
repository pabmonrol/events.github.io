from typing import List, NamedTuple
from bs4 import BeautifulSoup
from datetime import date, timedelta
import dateparser
from backend.utils import check_right_date, get_hour, check_location, check_is_senior, translate_text, http_session, clean_detail, DETAIL_LABELS
from backend.classifier import event_classification
from backend.model import Event


city = "Triesen"
avoid_categories = {"Government", "Religion"}


def scraper_triesen(url: str) -> List[NamedTuple]:
    res = []

    web = http_session.get(url).text
    soup = BeautifulSoup(web, "html.parser")
    events = soup.find_all(class_="event")

    reached_limit = False
    date_limit = date.today() + timedelta(days=6)

    for event in events:
        title_body = event.find("h3", class_="title")
        date_body = event.find("div", class_="date")
        if not (date_body and title_body):
            continue

        hour = None
        location = city
        google_maps = None
        price = None
        description = ""

        date_ = dateparser.parse(date_body.text, languages=["de"]).date()
        if date_ > date_limit:
            reached_limit = True
        if not check_right_date(date_):
            continue

        title = translate_text(title_body.text)
        if check_is_senior(title):
            continue

        category, icon, colour = event_classification(" ".join([description, title]))
        if category in avoid_categories:
            continue

        attributes = event.find(class_="attributes")
        if attributes:
            hour_text = clean_detail(attributes, DETAIL_LABELS["hour"])
            location_text = clean_detail(attributes, DETAIL_LABELS["location"])
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
                         price=price))

    if reached_limit:
        return res

    next_month_btn = soup.find("a", class_="arrow-right", id="content_aR")
    href = next_month_btn.get("href") if next_month_btn else None
    if not href:
        return res

    return res + scraper_triesen(f"https://www.triesen.li{href}")
