from typing import List, NamedTuple, Optional
from bs4 import BeautifulSoup
from datetime import time
import re
import dateparser
from backend.classifier import event_classification
from backend.model import Event
from backend.utils import location_url, reached_date_limit, get_price, check_is_senior, check_right_date, translate_text, http_session


city = "Mauren"
avoid_categories = {"Government", "Religion"}


def _find_value(page_soup, tag: str) -> Optional[str]:
    item = page_soup.find("li", class_="sidelist__item", attrs={"data-name": tag})
    if item:
        text = item.find("span", class_="sidelist__text").text
        if text:
            return f"{text}, {city}"
    return None


def _next_page(soup_page) -> Optional[str]:
    next_link = soup_page.find(class_="agenda__itemlink")
    if next_link:
        ul_element = next_link.find("ul", class_="insidenav__list")
        if ul_element:
            items = ul_element.find_all("li")
            if len(items) > 1:
                return items[1].get("href")
    return None


def _parse_hour(hour_text: str) -> Optional[time]:
    pattern = r"(\d{1,2})(?:[:.](\d{2}))?(?:[:.]\d{2})?\s*([ap]\.?m\.?|uhr|h(?:oras?)?)?"

    for match in re.finditer(pattern, hour_text, re.IGNORECASE):
        hour_str = match.group(1)
        minute_str = match.group(2)
        indicator_str = match.group(3)

        if not minute_str and not indicator_str:
            continue

        hour = int(hour_str)
        minute = int(minute_str) if minute_str else 0

        if indicator_str:
            indicator = re.sub(r"[\s.]", "", indicator_str.lower())
            if indicator == "pm" and hour < 12:
                hour += 12
            elif indicator == "am" and hour == 12:
                hour = 0

        if 0 <= hour <= 23 and 0 <= minute <= 59:
            return time(hour, minute)

    return None


def _scrape_event_pages(event_urls: List[str]) -> List[NamedTuple]:
    res = []

    for event_url in event_urls:
        description = ""

        page = http_session.get(event_url).text
        event_soup = BeautifulSoup(page, "html.parser")

        date_item = event_soup.find("li", class_="sidelist__item", attrs={"data-name": "Datum"})
        date_span = date_item.find("span", class_="sidelist__text") if date_item else None
        date_text = date_span.get_text(strip=True) if date_span else ""
        title_tag = event_soup.find(class_="eventdetail__headline page__headline")
        if not date_text or not title_tag:
            continue

        parsed = dateparser.parse(date_text, languages=["de"], settings={"DATE_ORDER": "DMY"})
        if parsed is None:
            continue
        date_ = parsed.date()
        if not check_right_date(date_):
            continue

        title = translate_text(title_tag.text)
        if check_is_senior(title):
            continue

        description_tag = event_soup.find(class_="eventdetail__textbody mce")
        description = translate_text(description_tag.text) if description_tag else ""

        category, icon, colour = event_classification(" ".join([description, title]))
        if category in avoid_categories:
            continue

        hour_text = _find_value(event_soup, "Zeit")
        hour = _parse_hour(hour_text) if hour_text else None
        location = _find_value(event_soup, "Ort") or city
        google_maps = location_url(location)
        price = get_price(description)

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


def scraper_mauren(url: str) -> List[NamedTuple]:
    final_list = []

    web = http_session.get(url + "/agenda").text
    soup = BeautifulSoup(web, "html.parser")
    event_urls = [url + link.get("href") for link in soup.find_all(class_="agenda__itemlink")]

    final_list.extend(_scrape_event_pages(event_urls))

    current_soup = soup
    while not reached_date_limit(final_list):
        next_path = _next_page(current_soup)
        if not next_path:
            break

        web = http_session.get(url + next_path).text
        current_soup = BeautifulSoup(web, "html.parser")

        new_urls = [url + link.get("href") for link in current_soup.find_all(class_="agenda__itemlink")]
        new_events = _scrape_event_pages(new_urls)
        if not new_events:
            break

        final_list.extend(new_events)

    return final_list
