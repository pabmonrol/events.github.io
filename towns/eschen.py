from typing import List, NamedTuple
from bs4 import BeautifulSoup
import re
import dateparser
from backend.classifier import event_classification
from backend.utils import check_location, check_is_senior, check_right_date, translate_text, fetch_text
from backend.model import Event


city = "Eschen"
avoid_categories = {"Government", "Religion"}


def scraper_eschen(url: str) -> List[NamedTuple]:
    res = []

    hour = None
    location = city
    google_maps = None
    price = None
    description = ""

    web = fetch_text(url)
    soup = BeautifulSoup(web, 'html.parser')
    links = soup.find_all(class_="link--underline clickable-parent")

    for link in links:
        page = fetch_text(link.get('href'))
        event = BeautifulSoup(page, 'html.parser')

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
            
        category, icon, colour = event_classification(" ".join([title, description]))
        if category not in avoid_categories:
            hour = event.find("b", text=re.compile("Uhrzeit:")).find_next("span").get_text(strip=True)
            location_ = event.find("b", text=re.compile("Ort:")).find_next("span")
            location, google_maps = check_location(location_, city)
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
