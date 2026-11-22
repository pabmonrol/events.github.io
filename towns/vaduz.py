from typing import List, NamedTuple, Tuple
from bs4 import BeautifulSoup, Tag
import re
import dateparser
from backend.utils import check_right_date, get_hour, get_price, location_url, check_is_senior, translate_text, fetch_text
from backend.classifier import event_classification
from backend.model import Event


city = "Vaduz"
avoid_categories = {"Government", "Religion"}


def _clean_location(tags_desc: List[Tag]) -> Tuple[str, str]:
    lines = [tag.text.strip().replace("\t", "") for tag in tags_desc]
    location_string = "\n".join(lines) + ", " + city
    return location_string, location_url(location_string)


def scraper_vaduz(url: str) -> List[NamedTuple]:
    res = []

    hour = None
    location = city
    google_maps = None
    price = None
    description = ""

    web = fetch_text(url)
    soup = BeautifulSoup(web, 'html.parser')
    links = soup.find_all(class_="small-7 medium-8 large-8 columns col_events_list_text")

    for link in links:
        title_body = link.find("div", class_="ccm-block-page-list-title").find("a")
        date_text = link.find(class_="ccm-block-page-list-date")
        if date_text and title_body:
            date_match = re.findall(r"\d{1,2}\.\d{2}\.\d{4}", date_text.text)
            date_ = dateparser.parse(date_match[0], settings={'DATE_ORDER': 'DMY'}).date()
            if not check_right_date(date_):
                continue
            page = fetch_text(title_body.get('href'))
            event = BeautifulSoup(page, 'html.parser')

        hour = None
        location = city
        google_maps = None
        price = None
        description = ""

        date_match = re.findall(r"\d{1,2}\.\d{2}\.\d{4}", date_text.text)
        date_ = dateparser.parse(date_match[0], settings={"DATE_ORDER": "DMY"}).date()
        if not check_right_date(date_):
            continue

        page = http_session.get(title_body.get("href")).text
        event = BeautifulSoup(page, "html.parser")

            category, icon, colour = event_classification(" ".join([title, description]))
            if category in avoid_categories:
                continue

        title_description_page = event.find("div", class_="summary").find_next("strong")
        description_page = event.find("div", class_="description").find_next("p")
        if title_description_page or description_page:
            title_description = translate_text(title_description_page.text)
            description_body = translate_text(description_page.text)
            description = title_description + "\n\n" + description_body
            price_text = event.find("div", class_="additional-info-wrapper").find_next("p")
            price = get_price(price_text.text)

        category, icon, colour = event_classification(" ".join([description, title]))
        if category in avoid_categories:
            continue

        hour_page = event.find("div", class_="schedule-block")
        hour_text = re.findall(r"\b(\d{1,2}:\d{2})\b", hour_page.text)
        if hour_text:
            hour = get_hour(hour_text[0])

        location_tags = event.find("div", class_="row event-location-map-wrapper").find_all("div", class_="description-wrapper")
        location, google_maps = _clean_location(location_tags)

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
