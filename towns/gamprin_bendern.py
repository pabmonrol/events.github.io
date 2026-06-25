import requests
from bs4 import BeautifulSoup



city, url = "Gamprin/Bendern", "https://www.gamprin.li/leben-gemeinschaft/veranstaltungen"
web = requests.get(url + "/agenda").text
soup = BeautifulSoup(web, 'html.parser')