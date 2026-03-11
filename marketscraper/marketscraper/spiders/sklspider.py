import scrapy
import time
import math
import re

from marketscraper.items import ProdItem, clean_price

class SklSpider(scrapy.Spider):
    name = "sklavenitis"
    #Δεν φεύγει εκτός domain, φαρμάροντας άκυρα πράγματα
    allowed_domains = ["www.sklavenitis.gr"]
    #Ξεκινάμε από κατηγορίες για να τραβήξουμε cats, subcats με τους συνδέσμους για να περιηγηθούμε
    start_urls = ["https://www.sklavenitis.gr/katigories/"]


    def parse(self, response):

        #Selector για τις κατηγορίες
        categories = response.css('div.categories_item')

        for cat in categories:
            #Print τον τίτλο κατηγορίας

            category_name = cat.css('h3.categories_title::text').get().strip().replace('\r','').replace('\n','').replace('\t','')

            #Track τον selector για κάθε υποκατηγορία
            subcats = cat.css('ul li')
            for subcat in subcats:
                subcat_name = subcat.css('a::text').get().strip().replace('\r','').replace('\n','').replace('\t','')

                # Επίσκεψη σε κάθε subcat για να τραβήξουμε τα στοιχεία με τον παρακάτω κώδικα product crawl
                rel_subcat_url = subcat.css('a::attr(href)').get()


                #κλήση συνάρτησης για να κάνει parse κάθε σελίδα ξέχωριστά με το σχετικό url για κάθε subcat
                #Χρήση meta για αποστολή δεδομένων στην άλλη συνάρτηση για την δομή του json
                yield response.follow(rel_subcat_url,
                                      callback=self.parse_subcat_page,
                                      meta={
                                          'category_name': category_name,
                                          'subcat_name': subcat_name,
                                      })



    def parse_subcat_page(self, response):
        #Τραβάμε τα μεταdata για να δομηθεί καλά το json - στοιχεία instert της βάσης
        category_name = response.meta['category_name']
        subcat_name = response.meta['subcat_name']

        """
        Πρόβλημα: Στην αρχική σελίδα κάθε υποκατηγορίας φορτώνονται max 24 προϊόντα.

        Αντιμετώπιση:
        Φαίνεται πως αλλάζει το url (προσθήκη /?pg=...) με τον αριθμό (άγνωστο) των σελιδών.
        Λογική:
        Κοιτάω από το σύνολο των προϊόντων στο κάτω μέρος
        Τραβάω το max προϊόντων από την σελίδα (χχχ από τα max)
        Διαιρώ με 24 σε άνω κατώφλι για να δω πόσες σελίδες χρειάζονται για να τα πάρω όλα.
        (Αν αποτέλεσμα <=1 συνεχίζω κανονικά, δεν χρειάζεται άλλη σελίδα - scroll)
        Αν αποτέλεσμα>1, θέτω το url με το αποτέλεσμα που βρήκα για να τα πάρω απευθείας όλα.
            - Πρόβλημα: φορτώνει μόνο τα τελευταία και όχι όλα, αλλαγή λογικής και parse κάθε σελίδα μέχρι και την τελευταία.
        Αν είμαι ήδη σε σελίδα χωρίς pg, ή έχω κάνει την διαδικασία ή δεν έχει άλλες σελίδες για να κάνω την διαδικασία
        """

        if "pg=" not in response.url:
            # Πάρε το πλήθος προϊόντων
            summary_text = response.css('span.current-page::text').get()
            #Χ από τα Υ προϊόντα
            match = re.search(r'από τα (\d+)', summary_text)
            # Πιάνει τον αριθμό συνολικών προϊόντων Υ με regex
            if match:
                # εφόσον βρίσκεται στο page, φέρε τον αριθμό () από όλο το ταίριασμα
                total_products = int(match.group(1))
                #βγάλε τον άνω ακέραιο για σύνολο σελίδων
                total_pages = math.ceil(total_products / 24)
            else:
                total_pages = 1

            # Αν έχει παραπάνω από 1 σελίδα, τότε κάνουμε αναδρομική σε κάθε σελίδα, για την συλλογή
            base_url = response.url.split('?')[0]
            for page in range(1, total_pages + 1):
                page_url = f"{base_url}?pg={page}"
                yield response.follow(
                    page_url,
                    callback=self.parse_subcat_page,
                    meta={
                        'category_name': category_name,
                        'subcat_name': subcat_name,
                        'pagination': True
                    }
                )
            return



        # Ορισμός των selector css για να βρεί αυτά που θέλω στην σελίδα
        prods = response.css('div[data-plugin-product]')
        #Λίστα προϊόντων για να γίνει πιο όμορφα το parse
        prod_list = []

        for prod in prods:
            #Για κάθε προϊόν, φτιάχνουμε ένα dic και αποθηκέυουμε τα δεδομένα

            product = {
                'name': prod.css('h4.product__title a::text').get(),
                # Καθαρίζουμε από break chars που επιστρέφει το response
                'price/kg': clean_price(prod.css('div.priceKil::text').get()),
                'price': clean_price(prod.css('div.price::text').get()),
            }
            prod_list.append(product)

        #Επιστρέφεται η δομή
        #Κατ
        # - Υποκατ
        # - - Προϊόν
        #yield {
        #    'category': category_name,
        #    'subcategory': subcat_name,
        #    'products': prod_list
        #}

        #Δημιουργία item
        prod_item = ProdItem()


        prod_item['category'] = category_name
        prod_item['subcategory'] = subcat_name
        prod_item['products'] = prod_list

        #print(f"Υποκατηγορία: {subcat_name} — Προϊόντα: {len(prod_list)}")
        yield prod_item



        # Function για να τραβάει όλα τα προϊόντα αφού έχουμε μπει σε υποκατηγορία
"""
        #Ορισμός των selector css για να βρεί αυτά που θέλω στην σελίδα
        coffee_prods = response.css('div[data-plugin-product]')

        #Πρέπει να λυθεί το θέμα του να ξεκινάει από κοινό response,
        #ώστε να τα φέρνει όλα πίσω σε ένα yield.
        #- solved -> response βάσει ID.
        
        #Δεν μπορεί να κάνει iterate καθώς επιστρέφει 1 μόνο στοιχείο (productlist)
        #- solved -> Πιάνει τα div[data-plugin-product]
        #- που αποτελείται κάθε καταχώρηση προϊόντος
        
        #Εκκρεμεί να scrollάρει για να φέρνει όλα τα στοιχεία



        #loop σε όλα τα προϊόντα που σύλλεξα
        for prod in coffee_prods:
            #yield: αντίστοιχο return
            yield{
                'name'      : prod.css('h4.product__title a::text').get(),
                #Καθαρίζουμε από break chars που επιστρέφει το response
                'price/kg'  : prod.css('div.priceKil::text').get().strip().replace('\n', '').replace('\r', ''),
                'price'     : prod.css('div.price::text').get().strip().replace('\n', '').replace('\r', '').replace('\t', ''),
            }
"""
