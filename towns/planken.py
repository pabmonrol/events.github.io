from typing import *
from backend.utils import fetch_text
from bs4 import BeautifulSoup


city = "Planken"
avoid_categories = {"Government", "Religion"}

def scraper_planken(url: str) -> List[NamedTuple]:
    res = []

    hour = None
    location = city
    google_maps = None
    price = None
    description = ""

    web = fetch_text(url)
    soup = BeautifulSoup(web, 'html.parser')
    events = soup.find_all(class_="sw-list-item")

    for event in events:
        title_page = event.find("div", class_="sw-title")
        date_page = event.find("div", class_="sw-date")
        day = date_page.find(class_="date-top")
        date__ = event.find()