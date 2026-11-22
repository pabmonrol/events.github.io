from typing import *
from bs4 import BeautifulSoup, Tag
from datetime import date
import dateparser
from playwright.sync_api import sync_playwright
from backend.utils import check_right_date, get_hour, location_url, check_is_senior, translate_text
from backend.classifier import event_classification
from backend.model import Event


city = "Triesenberg"
avoid_categories = {"Government", "Religion"}

year = str(date.today().year)
USER_AGENT = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")


def _find_location_triesenberg(data_list: List[Tag], city: str) -> str|Tag:
    location = city    
    for data in data_list:
        title_data = data.find("h3")
        paragraph = data.find("p")
        if title_data and title_data.text.strip() == "Veranstaltungsort" and paragraph:
            res = paragraph.text
            if city not in res:
                location = res.replace("\n", "").strip() + ", " + city
                
    return location


def _find_description_triesenberg(data_list: List[Tag]) -> str:
    res = ""
    for data in data_list:
        title_data = data.find("h3")
        paragraph = data.find("p")
        if title_data and title_data.text.strip() == "Details" and paragraph:
            res = paragraph.text
    return res


def scraper_triesenberg(url: str) -> List[NamedTuple]:
    res = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(user_agent=USER_AGENT, locale="de-DE")

        page.goto(url, wait_until="domcontentloaded")
        page.wait_for_selector(".grid-item.grid-33", timeout=15000)
        soup = BeautifulSoup(page.content(), 'html.parser')
        links = soup.find_all(class_="grid-item grid-33")

        for link in links:
            hour = None
            location = city
            google_maps = None
            price = None
            description = ""

            try:
                date_body = link.find("div", class_="event-overview-date")
                if not date_body:
                    continue

                day_text = date_body.find("div", class_="day").text
                month_text = date_body.find("div", class_="month").text
                date_text = day_text + "-" + month_text + "-" + year
                date_ = dateparser.parse(date_text, settings={'DATE_ORDER': 'DMY'}).date()

                if not check_right_date(date_):
                    continue

                title_body = link.find("div", class_="overview-title")
                if not title_body:
                    continue
                title = translate_text(title_body.text)

                if check_is_senior(title):
                    continue

                hour_page = link.find("div", class_="overview-date")
                if hour_page and hour_page.text != "":
                    hour = get_hour(hour_page.text)

                event_link = link.find("a", class_="event-overview-item overview-item")
                if not event_link:
                    event_link = link.find("a", class_="event-overview-item overview-item has-image")

                if not event_link:
                    continue

                page.goto(event_link.get('href'), wait_until="domcontentloaded")
                page.wait_for_selector("div.event-data-item", timeout=10000)
                event = BeautifulSoup(page.content(), 'html.parser')

                data = event.find_all("div", class_="event-data-item")
                description_page = _find_description_triesenberg(data)
                if description_page:
                    text_body = event.find(class_="eventdetail__textbody")
                    if text_body:
                        p_tag = text_body.find_next("p")
                        if p_tag:
                            description = translate_text(p_tag.text.strip())
                
                category, icon, colour = event_classification(" ".join([title, description]))
                if category in avoid_categories:
                    continue

                location = _find_location_triesenberg(data, city)
                google_maps = location_url(location)

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
            except Exception:
                continue

    return res