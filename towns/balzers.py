from deep_translator import GoogleTranslator
from typing import *
import requests
from bs4 import BeautifulSoup
from datetime import date
import re
import dateparser
from backend.utils import check_right_date, get_hour, check_location, get_price
from backend.classifier import event_classification
from backend.model import Event


city = "Balzers"
avoid_categories = {"Government", "Religion"}
translator = GoogleTranslator(source='de', target='en')

def _clean_date_balzers(cadena: str) -> date:
    match = re.search(r"(\d{1,2}\.\s*–\s*\d{1,2}\.\s*[a-zA-ZÁ-ÿ]+\s*\d{4})", cadena)
    if match:
        fecha_limpia = re.sub(r"\.\s*–.*", ".", match.group(1))
    else:
        match = re.search(r"(\d{1,2}\.\s*[a-zA-ZÁ-ÿ]+\s*\d{4})", cadena)
        fecha_limpia = match.group(1)
    date_ = dateparser.parse(fecha_limpia, languages=["de"]).date()
    
    return date_


def scraper_balzers(url: str) -> List[NamedTuple]:
    res = []

    hour = None
    location = city
    google_maps = None
    price = None
    description = ""

    web = requests.get(url).text
    soup = BeautifulSoup(web, 'html.parser')
    links_left = soup.find_all("div", class_="col-24 col-xs-12 col-md-10 col-lg-5 col-md-offset-1 col-lg-offset-1")
    links_right = soup.find_all("div", class_="col-24 col-xs-12 col-md-10 col-lg-5 col-md-offset-1 col-lg-offset-0")
    links = links_left, links_right

    for link_item in links:
        for link in link_item:
            date_text = link.find_next("div", class_="mdl030-list-item cell-1 mdl030-datum").text
            date_ = _clean_date_balzers(date_text)
            if not check_right_date(date_):
                continue
            event_link = link.find("a").get("href")
            page = requests.get(event_link).text
            event = BeautifulSoup(page, 'html.parser')

            block_info = event.find("div", class_="mdl-container mdl-art-030 bg-weiss mdl030-detail-text-item")
            title = translator.translate(block_info.find("h1").text)
            category, icon, colour = event_classification(title)

            if category not in avoid_categories:
                hour_page = event.select_one("span.mdl030-uhrzeit.text-schlamm")
                hour_text = hour_page.get_text(" ", strip=True) if hour_page else ""
                hour_text_list = re.findall(r"(\d{1,2}[:.]\d{2})", hour_text)
                hour = get_hour(hour_text_list[0]) if hour_text_list else None

                location_ = event.find("span", class_="mdl030-ort")
                location, google_maps = check_location(location_, city)

                infos = event.find("div", class_="mdl-container")
                if description:
                    description_text = infos.find_next("p")
                    description_joined = "\n".join(description_text)
                    description = translator.translate(description_joined)
                    price = get_price(description_joined)

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



        
