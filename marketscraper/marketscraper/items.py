# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy
import re

#Συνάρτηση για να καθαρίσω το πεδίο τιμής από κάτω από escape cars και να το μετατρέψω σε συγκρίσιμο float
def clean_price(timh):
    try:
        return float(timh.strip().replace('\n', '').replace('\r', '').replace('\t', '').replace('€', '').replace(',','.'))
    except (ValueError, AttributeError):
        return None

def find_price(str_timh: str):
    """Εξάγει float από string τύπου '8,11 €/ κιλ'"""
    if not str_timh:
        return None
    m = re.search(r'[\d,\.]+', str_timh)
    if not m:
        return None
    try:
        return float(m.group().replace(',', '.'))
    except ValueError:
        return None

class MarketscraperItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass

class ProdItem(scrapy.Item):
    category = scrapy.Field()
    subcategory = scrapy.Field()
    products = scrapy.Field()