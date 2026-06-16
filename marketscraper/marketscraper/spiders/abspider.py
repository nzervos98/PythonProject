import scrapy
import json
import urllib.parse
from urllib.parse import urlparse, parse_qs
from collections import defaultdict
from playwright.sync_api import sync_playwright

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

def get_search_hash():
    category_url = "https://www.ab.gr/el/eshop/Freska-Trofima/c/001"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        with page.expect_request(
            lambda r: "operationName=GetCategoryProductSearch" in r.url,
            timeout=30000,
        ) as req:
            page.goto(category_url, wait_until="domcontentloaded")

        url = req.value.url
        browser.close()

    qs = parse_qs(urlparse(url).query)
    extensions = json.loads(qs["extensions"][0])

    return extensions["persistedQuery"]["sha256Hash"]


NAV_HASH    = "29a05b50daa7ab7686d28bf2340457e2a31e1a9e4d79db611fcee435536ee01c"
SEARCH_HASH = get_search_hash()
PAGE_SIZE   = 20


def build_url(operation, variables, sha256):
    base = "https://www.ab.gr/api/v1/"
    params = {
        "operationName": operation,
        "variables":     json.dumps(variables, ensure_ascii=False),
        "extensions":    json.dumps({"persistedQuery": {"version": 1, "sha256Hash": sha256}}, ensure_ascii=False),
    }
    return base + "?" + urllib.parse.urlencode(params)


def build_slug_map(tree, top_level_info):
    """
    Χτίζουμε:
    1. slug_to_name: {url_slug: ελληνικό_όνομα}
       Από κάθε levelInfo.url: /el/eshop/.../SlugWeWant/c/CODE
       Παίρνουμε το segment πριν το /c/ ως slug key.
    2. top_code_to_name: {top_level_code: name} για top-level κατηγορίες
    """
    slug_to_name = {}

    for level in tree:
        for cat_info in level.get("categoriesInfo", []):
            for level_info in cat_info.get("levelInfo", []):
                url  = level_info.get("url", "")
                name = level_info.get("name", "")
                if not url or not name:
                    continue
                parts = url.strip("/").split("/")
                try:
                    c_index = parts.index("c")
                    slug = parts[c_index - 1]
                    slug_to_name[slug] = name
                except (ValueError, IndexError):
                    continue

    top_code_to_name = {}
    for item in top_level_info:
        code = item.get("code", "")
        name = item.get("name", "")
        url  = item.get("url", "")
        if code and name:
            top_code_to_name[code] = name
        if url and name:
            parts = url.strip("/").split("/")
            try:
                c_index = parts.index("c")
                slug = parts[c_index - 1]
                slug_to_name[slug] = name
            except (ValueError, IndexError):
                pass

    return slug_to_name, top_code_to_name


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
        SKIP_CATEGORIES = {"019", "031", "023"}  # Healthy Corner, Κάθε μέρα χαμηλή τιμή, Νέα Προϊόντα

        data = response.json()
        nav  = data["data"]["leftHandNavigationBar"]
        tree = nav["categoryTreeList"]
        top_level_info = nav.get("levelInfo", [])

        slug_to_name, top_code_to_name = build_slug_map(tree, top_level_info)

        level1 = tree[0]["categoriesInfo"]

        for cat in level1:
            code = cat.get("categoryCode")
            if not code or code in SKIP_CATEGORIES:
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
                meta={
                    "category_code":     code,
                    "page":              0,
                    "slug_to_name":      slug_to_name,
                    "top_code_to_name":  top_code_to_name,
                },
            )

    def parse_products(self, response):
        cat_code         = response.meta["category_code"]
        page             = response.meta["page"]
        slug_to_name     = response.meta["slug_to_name"]
        top_code_to_name = response.meta["top_code_to_name"]

        data        = response.json()
        search      = data.get("data", {}).get("categoryProductSearch", {})
        products    = search.get("products", [])
        pagination  = search.get("pagination", {})
        total_pages = pagination.get("totalPages", 1)

        top_category_name = top_code_to_name.get(cat_code, "")

        by_subcat = defaultdict(list)

        for p in products:

            price_obj   = p.get("price") or {}
            price_kg    = find_price(price_obj.get("supplementaryPriceLabel1"))
            prod_url    = p.get("url") or ""
            subcat_name = self._subcat_from_url(prod_url, slug_to_name)
            manufacturer = (p.get("manufacturerName") or "").strip().lstrip("-").strip()
            sub_brand = (p.get("manufacturerSubBrandName") or "").strip().lstrip("-").strip()

            # Φτιάχνουμε prefix: "ΟΛΥΜΠΟΣ FREELACT" ή "ΟΛΥΜΠΟΣ" ή ""
            if sub_brand:
                brand_prefix = f"{manufacturer} {sub_brand}"
            elif manufacturer:
                brand_prefix = manufacturer
            else:
                brand_prefix = ""

            prod_name = (p.get("name") or "").strip()
            if prod_name.startswith("- "):
                prod_name = prod_name[2:].strip()
            full_name = f"{brand_prefix} {prod_name}" if brand_prefix else prod_name

            by_subcat[subcat_name].append({
                "name": full_name,
                "price": price_obj.get("value"),
                "price/kg": price_kg,
                "subcat": subcat_name,
            })

        for subcat_name, prods in by_subcat.items():
            item = ProdItem()
            item["category"]    = top_category_name
            item["subcategory"] = subcat_name
            item["products"]    = prods
            yield item

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
                    "category_code":     cat_code,
                    "page":              next_page,
                    "slug_to_name":      slug_to_name,
                    "top_code_to_name":  top_code_to_name,
                },
            )

    def _subcat_from_url(self, prod_url, slug_to_name):
        if not prod_url:
            return ""

        parts = prod_url.strip("/").split("/")
        try:
            p_index = parts.index("p")
        except ValueError:
            return ""

        if p_index < 4:
            self.logger.debug(f"[SHORT_URL] {prod_url}")
            return ""

        subcat_slug = parts[3]

        if subcat_slug not in slug_to_name:
            self.logger.debug(f"[NO_SUBCAT] {prod_url} | slug={subcat_slug}")
            return ""

        return slug_to_name[subcat_slug]