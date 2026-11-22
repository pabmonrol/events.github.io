from typing import List, NamedTuple
from bs4 import BeautifulSoup
import re
import dateparser
from backend.classifier import event_classification
from backend.utils import check_location, check_is_senior, check_right_date, get_hour, translate_text, http_session
from backend.model import Event


city = "Eschen"
avoid_categories = {"Government", "Religion"}


def scraper_eschen(url: str) -> List[NamedTuple]:
    res = []

    web = http_session.get(url).text
    soup = BeautifulSoup(web, "html.parser")
    links = soup.find_all(class_="link--underline clickable-parent")

    for link in links:
        hour = None
        location = city
        google_maps = None
        price = None
        description = ""

        page = http_session.get(link.get("href")).text
        event = BeautifulSoup(page, "html.parser")

        title_page = event.select_one("main h1.ct-headline span")
        date_page = event.find(text=re.compile("Datum:")).find_next(class_="ct-code-block")
        if not (title_page and date_page):
            continue

        title = translate_text(title_page.text)
        if check_is_senior(title):
            continue

        date_match = re.findall(r"\d{1,2}\.\d{2}\.\d{4}", date_page.text)
        date_ = dateparser.parse(date_match[0], settings={"DATE_ORDER": "DMY"}).date()
        if not check_right_date(date_):
            continue

        category, icon, colour = event_classification(" ".join([description, title]))
        if category in avoid_categories:
            continue

        hour_label = event.find("b", text=re.compile("Uhrzeit:"))
        hour_span = hour_label.find_next("span") if hour_label else None
        if hour_span:
            hour = get_hour(hour_span.get_text(strip=True))

        location_label = event.find("b", text=re.compile("Ort:"))
        location_tag = location_label.find_next("span") if location_label else None
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
