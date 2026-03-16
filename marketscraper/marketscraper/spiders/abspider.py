import re
import scrapy
import json
import urllib.parse
from collections import defaultdict

from marketscraper.items import ProdItem, find_price


AB_HEADERS = {
    "content-type": "application/json",
    "apollographql-client-name": "gr-ab-web-stores",
    "apollographql-client-version": "e23db29dffd65300a7defc27c5ee37a4a7c75c87",
    "x-apollo-operation-name": "GetCategoryProductSearch",
    "x-default-gql-refresh-token-disabled": "true",
    "referer": "https://www.ab.gr/",
    "user-agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/145.0.0.0 Safari/537.36"
    ),
}

NAV_HASH    = "29a05b50daa7ab7686d28bf2340457e2a31e1a9e4d79db611fcee435536ee01c"
SEARCH_HASH = "6207aa07553962b9956d475b63737d2b03b3eb7b7e6fa6ffbfc709f9894c5bdd"
PAGE_SIZE   = 20

#Create proper url so that AB knows it is a GraphQL query with persisted query hash and variables, sent by legit browser.
def build_url(operation, variables, sha256):
    base = "https://www.ab.gr/api/v1/"
    params = {
        "operationName": operation,
        "variables":     json.dumps(variables, ensure_ascii=False),
        "extensions":    json.dumps({"persistedQuery": {"version": 1, "sha256Hash": sha256}}, ensure_ascii=False),
    }
    return base + "?" + urllib.parse.urlencode(params)


class AbSpider(scrapy.Spider):
    name = "ab"
    allowed_domains = ["www.ab.gr"]

    async def start(self):
        url = build_url(
            "LeftHandNavigationBar",
            {"rootCategoryCode": "", "cutOffLevel": "4", "lang": "gr"},
            NAV_HASH,
        )
        yield scrapy.Request(url, headers=AB_HEADERS, callback=self.parse_nav)

    def parse_nav(self, response):
        data = response.json()
        tree = data["data"]["leftHandNavigationBar"]["categoryTreeList"]

        # Index 0 = level 1 (top-level categories)
        level1 = tree[0]["categoriesInfo"]

        for cat in level1:
            code = cat.get("categoryCode")
            if not code:
                continue
            yield scrapy.Request(
                build_url(
                    "GetCategoryProductSearch",
                    {
                        "lang": "gr",
                        "searchQuery": "",
                        "category": code,
                        "pageNumber": 0,
                        "pageSize": PAGE_SIZE,
                        "filterFlag": True,
                        "fields": "PRODUCT_TILE",
                        "plainChildCategories": True,
                    },
                    SEARCH_HASH,
                ),
                headers=AB_HEADERS,
                callback=self.parse_products,
                meta={"category_code": code, "page": 0},
            )

    def parse_products(self, response):
        cat_code    = response.meta["category_code"]
        page        = response.meta["page"]

        data        = response.json()
        search      = data.get("data", {}).get("categoryProductSearch", {})
        products    = search.get("products", [])
        pagination  = search.get("pagination", {})
        total_pages = pagination.get("totalPages", 1)

        # Ομαδοποίηση ανά firstLevelCategory για σωστή κατηγορία
        by_cat = defaultdict(list)
        for p in products:
            price_obj     = p.get("price") or {}
            first_cat     = p.get("firstLevelCategory") or {}
            category_name = first_cat.get("name") or ""

            # Τιμή/κιλό από supplementaryPriceLabel1 (π.χ. "8,11 €/ κιλ")
            price_kg = find_price(price_obj.get("supplementaryPriceLabel1"))

            # Υποκατηγορία από URL (3ο segment μετά /el/eshop/)
            url_parts = (p.get("url") or "").strip("/").split("/")
            subcat = url_parts[3] if len(url_parts) >= 4 else ""

            by_cat[category_name].append({
                "name":     p.get("name"),
                "price":    price_obj.get("value"),
                "price/kg": price_kg,
                "subcat":   subcat,
            })

        for cat_name, prods in by_cat.items():
            item = ProdItem()
            item["category"]    = cat_name
            item["subcategory"] = ""
            item["products"]    = prods
            yield item

        # Pagination
        next_page = page + 1
        if next_page < total_pages:
            yield scrapy.Request(
                build_url(
                    "GetCategoryProductSearch",
                    {
                        "lang": "gr",
                        "searchQuery": "",
                        "category": cat_code,
                        "pageNumber": next_page,
                        "pageSize": PAGE_SIZE,
                        "filterFlag": True,
                        "fields": "PRODUCT_TILE",
                        "plainChildCategories": True,
                    },
                    SEARCH_HASH,
                ),
                headers=AB_HEADERS,
                callback=self.parse_products,
                meta={
                    "category_code": cat_code,
                    "page": next_page,
                },
            )