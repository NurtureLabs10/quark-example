import requests
from bs4 import BeautifulSoup
import re

def get_current_gas_price(blockchain='BNB'):
    if blockchain.startswith("ETH"):
        url = "https://ethgasstation.info/"
        r = requests.get(url)
        soup = BeautifulSoup(r.text, "html.parser")

        return int(soup.find('div', class_='count standard').getText())

    url = "https://bscscan.com/chart/gasprice"
    r = requests.get(url)
    soup = BeautifulSoup(r.text, "html.parser")
    s = str(soup).split("var litChartData = ")[1].split(';')[0]
    return float(re.findall("(([0-9]*|[0-9]*.[0-9]*) Gwei)", s)[-1][1][1:])

# standard_gasprice = get_current_gas_price()

