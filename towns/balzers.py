from typing import List, NamedTuple
from bs4 import BeautifulSoup
from datetime import date
import re
import dateparser
from backend.utils import check_right_date, get_hour, check_location, get_price, check_is_senior, translate_text, fetch_text
from backend.classifier import event_classification, AVOID_CATEGORIES
from backend.model import Event


city = "Balzers"


def _clean_date(text: str) -> date:
    match = re.search(r"(\d{1,2}\.\s*–\s*\d{1,2}\.\s*[a-zA-ZÁ-ÿ]+\s*\d{4})", text)
    if match:
        clean_date = re.sub(r"\.\s*–.*", ".", match.group(1))
    else:
        match = re.search(r"(\d{1,2}\.\s*[a-zA-ZÁ-ÿ]+\s*\d{4})", text)
        clean_date = match.group(1)
    return dateparser.parse(clean_date, languages=["de"]).date()


def scraper_balzers(url: str) -> List[NamedTuple]:
    res = []

    hour = None
    location = city
    google_maps = None
    price = None
    description = ""

    web = fetch_text(url)
    soup = BeautifulSoup(web, 'html.parser')
    links_left = soup.find_all("div", class_="col-24 col-xs-12 col-md-10 col-lg-5 col-md-offset-1 col-lg-offset-1")
    links_right = soup.find_all("div", class_="col-24 col-xs-12 col-md-10 col-lg-5 col-md-offset-1 col-lg-offset-0")
    links = links_left, links_right

            date_text = link.find_next("div", class_="mdl030-list-item cell-1 mdl030-datum").text
            date_ = _clean_date(date_text)
            if not check_right_date(date_):
                continue

            event_link = link.find("a").get("href")
            page = fetch_text(event_link)
            event = BeautifulSoup(page, 'html.parser')

            block_info = event.find("div", class_="mdl-container mdl-art-030 bg-weiss mdl030-detail-text-item")
            title_page = block_info.find("h1")
            if not title_page:
                continue

            title = translate_text(title_page.text)
            if check_is_senior(title):
                continue

            infos = event.find("div", class_="col-24 col-xs-12 col-md-6 col-lg-5 col-lg-offset-1").find("div", class_="left__panel").find("div", class_="mdl-container")
            if infos:
                description_texts = infos.find_all("p")
                description_joined = "\n".join(d.text.strip() for d in description_texts)
                description = translate_text(description_joined)
                price = get_price(description_joined)

            category, icon, colour = event_classification(" ".join([title, description]))
            if category in AVOID_CATEGORIES:
                continue

            hour_page = event.select_one("span.mdl030-uhrzeit.text-schlamm")
            hour_text = hour_page.get_text(" ", strip=True) if hour_page else ""
            hour_list = re.findall(r"(\d{1,2}[:.]\d{2})", hour_text)
            if hour_list:
                hour = get_hour(hour_list[0])

            location_tag = event.find("div", class_="padding-klein text-small bg-weiss text-dunkelblau").find("p")
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
