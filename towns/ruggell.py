from bs4 import BeautifulSoup
from typing import NamedTuple, List
from datetime import datetime, date, timedelta
from backend.utils import location_url, check_is_senior, check_right_date, translate_text, fetch_text

city = "Ruggell"
avoid_categories = {"Government", "Religion"}


def scraper_ruggell(url: str) -> List[NamedTuple]:
    res = []
    seen = set()

    final_date = date.today() + timedelta(days=6)

    while url and url not in seen:
        seen.add(url)

        web = fetch_text(url)
        soup = BeautifulSoup(web, 'html.parser')
        events = soup.find_all(class_='infos')

        reached_limit = False

        for event in events:
            hour = None
            location = city
            google_maps = None
            price = None
            description = None

            if not event.find(class_="date") or not event.find(class_="title"):
                continue

            parsed = dateparser.parse(event.find(class_="date").text)
            if parsed is None:
                continue
            date_ = parsed.date()
            if date_ >= final_date:
                reached_limit = True
            if not check_right_date(date_):
                continue

            title = translate_text(event.find(class_="title").text)
            if check_is_senior(title):
                continue

            description = translate_text(event.find(class_="text").text)

            category, icon, colour = event_classification(" ".join([title, description]))
            if category in avoid_categories:
                continue

            attributes = event.find(class_="attributes")
            if attributes:
                hour_text = clean_detail(attributes, DETAIL_LABELS["hour"])
                location_text = clean_detail(attributes, DETAIL_LABELS["location"])
                if hour_text:
                    hour = datetime.strptime(hour_text, "%H.%M").time()
                if location_text:
                    location = str(location_text).strip()
                    google_maps = location_url(location_text)

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

        if reached_limit:
            break

        next_month_btn = soup.find("a", class_="arrow-right", id="content_aR")
        if next_month_btn is None or not next_month_btn.get("href"):
            break
        url = f"https://www.ruggell.li{next_month_btn.get('href')}"

    return res
