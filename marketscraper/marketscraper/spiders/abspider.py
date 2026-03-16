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
            manufacturer = p.get("manufacturerName") or ""
            sub_brand = p.get("manufacturerSubBrandName") or ""

            # Φτιάχνουμε prefix: "ΟΛΥΜΠΟΣ FREELACT" ή "ΟΛΥΜΠΟΣ" ή ""
            if sub_brand:
                brand_prefix = f"{manufacturer} {sub_brand}"
            elif manufacturer:
                brand_prefix = manufacturer
            else:
                brand_prefix = ""

            prod_name = p.get("name") or ""
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
        """
        URL μορφή: /el/eshop/TopCat/SubCat/SubSubCat/ProductSlug/p/CODE

        Segments μεταξύ eshop και /p/:
        [TopCat, SubCat?, SubSubCat?, ProductSlug]

        Αφαιρούμε TopCat (index 0) και ProductSlug (τελευταίο).
        Ψάχνουμε από το βαθύτερο προς τα πάνω στο slug_to_name.
        """
        if not prod_url:
            return ""

        parts = prod_url.strip("/").split("/")
        try:
            p_index = parts.index("p")
        except ValueError:
            return ""

        # [TopCat, SubCat?, SubSubCat?, ProductSlug]
        cat_slugs = parts[2:p_index]

        # Χρειαζόμαστε τουλάχιστον TopCat + 1 subcat + ProductSlug = 3
        if len(cat_slugs) < 3:
            return ""

        # Αφαιρούμε TopCat και ProductSlug, κρατάμε subcat slugs
        subcat_slugs = cat_slugs[1:-1]

        # Από το βαθύτερο προς τα πάνω
        for slug in reversed(subcat_slugs):
            if slug in slug_to_name:
                return slug_to_name[slug]

        return ""