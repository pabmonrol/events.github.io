from typing import List, NamedTuple
from bs4 import BeautifulSoup
import re
import dateparser
from backend.utils import check_right_date, get_hour, check_location, get_price, check_is_senior, translate_text, fetch_text
from backend.classifier import event_classification
from backend.model import Event


city = "Schaan"
avoid_categories = {"Government", "Religion"}


def scraper_schaan(url: str) -> List[NamedTuple]:
    res = []

    hour = None
    location = city
    google_maps = None
    price = None
    description = ""

    web = fetch_text(url)
    soup = BeautifulSoup(web, 'html.parser')
    links = soup.find_all(class_="sw-list-item")

    for link in links:
        title_link = link.find(class_="sw-title").find("a").get("href")
        date_text = link.find(class_="sw-date")
        if date_text and title_link:
            date_match = re.findall(r"\d{1,2}\.\d{2}\.\d{4}", date_text.text)
            date_ = dateparser.parse(date_match[0], settings={'DATE_ORDER': 'DMY'}).date()
            
            if not check_right_date(date_):
                continue
            page = fetch_text(title_link)
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

        page = http_session.get(title_link).text
        event = BeautifulSoup(page, "html.parser")

            category, icon, colour = event_classification(" ".join([title, description]))
            if category in avoid_categories:
                continue

        description_page = event.find("div", class_="vier")
        if description_page:
            description_node = event.find(class_="eventdetail__textbody mce").find_next("p")
            description_text = description_node.get_text(strip=True) if description_node else ""
            description = translate_text(description_text)
            price = get_price(description_text)

        category, icon, colour = event_classification(" ".join([description, title]))
        if category in avoid_categories:
            continue

        hour_page = event.find(class_="sw-date")
        hour_text = re.findall(r"\d{1,2}:\d{2}", hour_page.text)
        if hour_text:
            hour = get_hour(hour_text[0])

        location_tag = event.find("a", class_="primary-color")
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
