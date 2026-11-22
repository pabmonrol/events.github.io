from typing import List, NamedTuple
from bs4 import BeautifulSoup
from datetime import date
from urllib.parse import urljoin, urlparse
import dateparser
from backend.classifier import event_classification
from backend.utils import get_price, get_hour, check_location, check_is_senior, check_right_date, translate_text, http_session
from backend.model import Event


city = "Gamprin/Bendern"
avoid_categories = {"Government", "Religion"}


def scraper_gamprin_bendern(url: str) -> List[NamedTuple]:
    res = []

    web = http_session.get(url).text
    soup = BeautifulSoup(web, "html.parser")
    events = soup.find_all("div", class_="events-list-entry ccm-block-page-list-page-entry")

    year = str(date.today().year)

    for event in events:
        hour = None
        location = city
        google_maps = None
        price = None
        description = ""

        event_link = event.find(class_="mega-link-overlay").get("href")
        event_url = urljoin(url, event_link)
        parsed_event = urlparse(event_url)

        if parsed_event.netloc == "www.gamprin.li" and parsed_event.path in ("", "/"):
            title_text = event.find_next("div", class_="mega-link-overlay").find("a").text
            title = translate_text(title_text)
            if check_is_senior(title):
                continue

            category, icon, colour = event_classification(" ".join([description, title]))
            if category in avoid_categories:
                continue

            day = event.find_next(class_="day").text
            month = event.find_next(class_="month").text
            date_ = dateparser.parse(f"{day}-{month}-{year}", settings={"DATE_ORDER": "DMY"}).date()
            if not check_right_date(date_):
                continue

            hour_text = event.find_next("div", class_="event-list-time")
            if hour_text:
                hour = get_hour(hour_text.text)
        else:
            page = http_session.get(event_url).text
            event_page = BeautifulSoup(page, "html.parser")

            date_text = event_page.find(class_="sw-date")
            title_text = event_page.find(class_="sw-title")
            if not date_text or not title_text:
                continue

            date_ = dateparser.parse(date_text.text).date()
            if not check_right_date(date_):
                continue

            title = translate_text(title_text.text)
            if check_is_senior(title):
                continue

            hour_tag = event_page.find("div", class_="event-time")
            if hour_tag:
                hour = get_hour(hour_tag.get_text(strip=True))

            location, google_maps = check_location(event_page.find(class_="event-location"), city)

            description_tag = event_page.find(class_="sw-description")
            if description_tag:
                description = translate_text(description_tag.text)
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
