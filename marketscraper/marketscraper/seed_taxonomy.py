import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from marketscraper.marketscraper.models import (
    init_db,
    Supermarket,
    CanonicalTaxonomy,
    SourceTaxonomyMapping,
)

# =========================================================
# 1. Supermarkets
# =========================================================

SUPERMARKETS = [
    "ab",
    "sklavenitis",
]

# =========================================================
# 2. Canonical taxonomy
# =========================================================
# tuple:
# (category_code, category_label, subcategory_code, subcategory_label, sort_order)

CANONICAL_ROWS = [
    # Φρέσκα Τρόφιμα
    ("fresh_food", "Φρέσκα Τρόφιμα", "fruits", "Φρούτα", 10),
    ("fresh_food", "Φρέσκα Τρόφιμα", "vegetables", "Λαχανικά", 11),
    ("fresh_food", "Φρέσκα Τρόφιμα", "herbs", "Βότανα & Μυρωδικά", 12),

    # Αρτοποιείο
    ("bakery", "Αρτοποιείο", "bread", "Ψωμί", 20),
    ("bakery", "Αρτοποιείο", "toast_bread", "Ψωμί του Τοστ", 21),
    ("bakery", "Αρτοποιείο", "rusks", "Φρυγανιές & Παξιμάδια", 22),
    ("bakery", "Αρτοποιείο", "breadsticks_croutons", "Κριτσίνια & Croutons", 23),
    ("bakery", "Αρτοποιείο", "pastries", "Κέικ, Κρουασάν & Γλυκά Αρτοποιείου", 24),
    ("bakery", "Αρτοποιείο", "sweet_breads", "Τσουρέκια & Παραδοσιακά Γλυκά", 25),
    ("bakery", "Αρτοποιείο", "cookies_rings", "Κουλούρια & Βουτήματα", 26),
    ("bakery", "Αρτοποιείο", "dough", "Ζύμες, Πίτες & Τορτίγιες", 27),
    ("bakery", "Αρτοποιείο", "halva", "Χαλβάς", 28),

    # Γαλακτοκομικά & Ψυγείο
    ("dairy_chilled", "Γαλακτοκομικά & Ψυγείο", "milk", "Γάλα", 30),
    ("dairy_chilled", "Γαλακτοκομικά & Ψυγείο", "chocolate_milk", "Σοκολατούχα Γάλατα", 31),
    ("dairy_chilled", "Γαλακτοκομικά & Ψυγείο", "plant_milk", "Φυτικά Ροφήματα", 32),
    ("dairy_chilled", "Γαλακτοκομικά & Ψυγείο", "fridge_juices", "Χυμοί Ψυγείου", 33),
    ("dairy_chilled", "Γαλακτοκομικά & Ψυγείο", "yogurt", "Γιαούρτια", 34),
    ("dairy_chilled", "Γαλακτοκομικά & Ψυγείο", "kid_yogurts", "Βρεφικά & Παιδικά Γιαούρτια", 35),
    ("dairy_chilled", "Γαλακτοκομικά & Ψυγείο", "yogurt_desserts", "Επιδόρπια Γιαουρτιού", 36),
    ("dairy_chilled", "Γαλακτοκομικά & Ψυγείο", "protein_desserts", "Πρωτεϊνούχα Γιαούρτια & Γλυκίσματα", 37),
    ("dairy_chilled", "Γαλακτοκομικά & Ψυγείο", "chilled_desserts", "Επιδόρπια Ψυγείου", 38),
    ("dairy_chilled", "Γαλακτοκομικά & Ψυγείο", "rice_puddings", "Ρυζόγαλα & Γλυκίσματα Ψυγείου", 39),
    ("dairy_chilled", "Γαλακτοκομικά & Ψυγείο", "plant_desserts", "Φυτικά Επιδόρπια", 40),
    ("dairy_chilled", "Γαλακτοκομικά & Ψυγείο", "butter_cream", "Βούτυρο, Μαργαρίνες & Κρέμες", 41),
    ("dairy_chilled", "Γαλακτοκομικά & Ψυγείο", "eggs", "Αυγά", 42),
    ("dairy_chilled", "Γαλακτοκομικά & Ψυγείο", "spreads_salads", "Σαλάτες & Αλοιφές", 43),
    ("dairy_chilled", "Γαλακτοκομικά & Ψυγείο", "fresh_dough", "Νωπές Ζύμες, Φύλλα & Μαγιά", 44),
    ("dairy_chilled", "Γαλακτοκομικά & Ψυγείο", "fresh_pasta_sauces", "Φρέσκα Ζυμαρικά & Σάλτσες", 45),
    ("dairy_chilled", "Γαλακτοκομικά & Ψυγείο", "low_fat", "Προϊόντα Χαμηλών Λιπαρών", 46),

    # Τυριά & Αλλαντικά
    ("cheese_deli", "Τυριά & Αλλαντικά", "cheese", "Τυριά", 50),
    ("cheese_deli", "Τυριά & Αλλαντικά", "cold_cuts", "Αλλαντικά", 51),
    ("cheese_deli", "Τυριά & Αλλαντικά", "plant_substitutes", "Φυτικά Αναπληρώματα", 52),
    ("cheese_deli", "Τυριά & Αλλαντικά", "mixed_trays", "Σετ Αλλαντικών & Τυριών", 53),

    # Κρέας & Ψάρι
    ("meat_fish", "Κρέας & Ψάρι", "prepared_meat", "Παρασκευάσματα Κρεάτων & Πουλερικών", 60),
    ("meat_fish", "Κρέας & Ψάρι", "beef", "Μοσχάρι", 61),
    ("meat_fish", "Κρέας & Ψάρι", "pork", "Χοιρινό", 62),
    ("meat_fish", "Κρέας & Ψάρι", "poultry", "Πουλερικά", 63),
    ("meat_fish", "Κρέας & Ψάρι", "lamb_goat", "Αρνί & Κατσίκι", 64),
    ("meat_fish", "Κρέας & Ψάρι", "minced_meat", "Κιμάς", 65),
    ("meat_fish", "Κρέας & Ψάρι", "game", "Κυνήγι", 66),
    ("meat_fish", "Κρέας & Ψάρι", "fresh_fish", "Φρέσκα Ψάρια", 67),
    ("meat_fish", "Κρέας & Ψάρι", "fish_seafood", "Ψάρια & Θαλασσινά", 68),
    ("meat_fish", "Κρέας & Ψάρι", "shellfish", "Οστρακοειδή", 69),
    ("meat_fish", "Κρέας & Ψάρι", "cephalopods", "Χταπόδια, Καλαμάρια & Σουπιές", 70),
    ("meat_fish", "Κρέας & Ψάρι", "farm_fish", "Ψάρια Ιχθυοκαλλιέργειας", 71),

    # Κατεψυγμένα
    ("frozen", "Κατεψυγμένα", "frozen_vegetables", "Κατεψυγμένα Λαχανικά & Φρούτα", 80),
    ("frozen", "Κατεψυγμένα", "frozen_meals", "Κατεψυγμένα Γεύματα", 81),
    ("frozen", "Κατεψυγμένα", "frozen_meat_fish", "Κατεψυγμένο Κρέας, Ψάρια & Θαλασσινά", 82),
    ("frozen", "Κατεψυγμένα", "frozen_pastry", "Κατεψυγμένες Ζύμες, Πίτες & Πίτσες", 83),
    ("frozen", "Κατεψυγμένα", "frozen_plant_substitutes", "Κατεψυγμένα Φυτικά Αναπληρώματα", 84),
    ("frozen", "Κατεψυγμένα", "ice_cream", "Παγωτά", 85),
    ("frozen", "Κατεψυγμένα", "ice_icecubes", "Παγωτά & Παγάκια", 86),

    # Παντοπωλείο
    ("pantry", "Παντοπωλείο", "deli", "Delicatessen", 90),
    ("pantry", "Παντοπωλείο", "international", "Διεθνής Κουζίνα", 91),
    ("pantry", "Παντοπωλείο", "pasta_rice_legumes", "Ζυμαρικά, Ρύζι & Όσπρια", 92),
    ("pantry", "Παντοπωλείο", "canned_jarred", "Κονσέρβες, Βαζάκια & Τουρσιά", 93),
    ("pantry", "Παντοπωλείο", "tomato_products", "Ντοματικά", 94),
    ("pantry", "Παντοπωλείο", "sauces_condiments", "Σάλτσες, Καρυκεύματα, Dressings & Ζωμοί", 95),
    ("pantry", "Παντοπωλείο", "oils_vinegars", "Λάδια, Λίπη, Ξύδια & Ελιές", 96),
    ("pantry", "Παντοπωλείο", "baking", "Υλικά Ζαχαροπλαστικής & Μαγειρικής", 97),
    ("pantry", "Παντοπωλείο", "flours_sugars", "Άλευρα, Σιμιγδάλια, Ζάχαρη & Υποκατάστατα", 98),
    ("pantry", "Παντοπωλείο", "spreads_honey", "Μέλι, Μαρμελάδες & Αλείμματα", 99),
    ("pantry", "Παντοπωλείο", "instant_meals", "Πουρέδες, Σούπες & Noodles", 100),
    ("pantry", "Παντοπωλείο", "grains", "Σιτηρά, Κινόα, Σόγια & Λοιπά Δημητριακά", 101),

    # Ποτά
    ("beverages", "Ποτά", "water", "Νερά", 110),
    ("beverages", "Ποτά", "soft_drinks", "Αναψυκτικά, Σόδες & Ενεργειακά", 111),
    ("beverages", "Ποτά", "juices", "Χυμοί", 112),
    ("beverages", "Ποτά", "coffee", "Καφές", 113),
    ("beverages", "Ποτά", "tea", "Τσάι & Αφεψήματα", 114),
    ("beverages", "Ποτά", "cocoa_drinks", "Κακάο & Ροφήματα Σοκολάτας", 115),
    ("beverages", "Ποτά", "gums_candies", "Τσίχλες & Καραμέλες", 116),

    # Snacks & Πρωινό
    ("snacks_breakfast", "Snacks & Πρωινό", "cereals", "Δημητριακά", 120),
    ("snacks_breakfast", "Snacks & Πρωινό", "bars", "Μπάρες & Δημητριακά On-the-go", 121),
    ("snacks_breakfast", "Snacks & Πρωινό", "biscuits", "Μπισκότα", 122),
    ("snacks_breakfast", "Snacks & Πρωινό", "crackers", "Κράκερς", 123),
    ("snacks_breakfast", "Snacks & Πρωινό", "snacks", "Αλμυρά Snacks", 124),
    ("snacks_breakfast", "Snacks & Πρωινό", "chocolate_sweets", "Σοκολάτες & Γλυκίσματα", 125),
    ("snacks_breakfast", "Snacks & Πρωινό", "spreads", "Πραλίνες, Ταχίνι & Φιστικοβούτυρο", 126),
    ("snacks_breakfast", "Snacks & Πρωινό", "traditional_sweets", "Παραδοσιακά Γλυκίσματα", 127),
    ("snacks_breakfast", "Snacks & Πρωινό", "protein_powders", "Πρωτεΐνες σε Σκόνη", 128),
    ("snacks_breakfast", "Snacks & Πρωινό", "nuts_dried_fruits", "Ξηροί Καρποί & Αποξηραμένα Φρούτα", 129),

    # Καθαριότητα & Χαρτικά
    ("household_cleaning", "Καθαριότητα & Χαρτικά", "dish_detergents", "Απορρυπαντικά Πιάτων", 130),
    ("household_cleaning", "Καθαριότητα & Χαρτικά", "laundry_detergents", "Απορρυπαντικά Ρούχων", 131),
    ("household_cleaning", "Καθαριότητα & Χαρτικά", "hand_wash_laundry", "Πλύσιμο Ρούχων στο Χέρι", 132),
    ("household_cleaning", "Καθαριότητα & Χαρτικά", "fabric_softeners", "Μαλακτικά Ρούχων", 133),
    ("household_cleaning", "Καθαριότητα & Χαρτικά", "bleach_boosters", "Λευκαντικά & Ενισχυτικά Πλυσίματος", 134),
    ("household_cleaning", "Καθαριότητα & Χαρτικά", "dishwasher_additives", "Αποσκληρυντικά Πλυντηρίου", 135),
    ("household_cleaning", "Καθαριότητα & Χαρτικά", "home_cleaning", "Καθαριστικά Σπιτιού", 136),
    ("household_cleaning", "Καθαριότητα & Χαρτικά", "cleaning_accessories", "Σύνεργα & Αξεσουάρ Καθαρισμού", 137),
    ("household_cleaning", "Καθαριότητα & Χαρτικά", "paper_goods", "Χαρτικά", 138),
    ("household_cleaning", "Καθαριότητα & Χαρτικά", "air_fresheners", "Αρωματικά Χώρου & Κεριά", 139),
    ("household_cleaning", "Καθαριότητα & Χαρτικά", "insect_control", "Εντομοκτόνα & Εντομοαπωθητικά", 140),
    ("household_cleaning", "Καθαριότητα & Χαρτικά", "clothes_storage", "Φύλαξη & Περιποίηση Ρούχων", 141),
    ("household_cleaning", "Καθαριότητα & Χαρτικά", "ironing_linen", "Σιδέρωμα & Λευκά Είδη", 142),
    ("household_cleaning", "Καθαριότητα & Χαρτικά", "disposables_party", "Είδη Μιας Χρήσης & Πάρτι", 143),
    ("household_cleaning", "Καθαριότητα & Χαρτικά", "home_goods", "Είδη Οικιακής Χρήσης", 144),
    ("household_cleaning", "Καθαριότητα & Χαρτικά", "stationery", "Γραφική Ύλη & Χαρτοπωλείο", 145),

    # Προσωπική Περιποίηση
    ("personal_care", "Προσωπική Περιποίηση", "body_care", "Περιποίηση Σώματος", 150),
    ("personal_care", "Προσωπική Περιποίηση", "hair_care", "Περιποίηση Μαλλιών", 151),
    ("personal_care", "Προσωπική Περιποίηση", "oral_care", "Στοματική Υγιεινή", 152),
    ("personal_care", "Προσωπική Περιποίηση", "hygiene", "Προϊόντα Υγιεινής", 153),
    ("personal_care", "Προσωπική Περιποίηση", "mens_care", "Ανδρική Περιποίηση", 154),
    ("personal_care", "Προσωπική Περιποίηση", "womens_care", "Γυναικεία Περιποίηση", 155),
    ("personal_care", "Προσωπική Περιποίηση", "pharma", "Παραφαρμακευτικά Είδη", 156),
    ("personal_care", "Προσωπική Περιποίηση", "shaving", "Ξύρισμα & After Shave", 157),
    ("personal_care", "Προσωπική Περιποίηση", "face_care", "Υγιεινή & Περιποίηση Προσώπου", 158),
    ("personal_care", "Προσωπική Περιποίηση", "makeup", "Μακιγιάζ & Βερνίκια", 159),
    ("personal_care", "Προσωπική Περιποίηση", "child_care", "Βρεφικά & Παιδικά Καλλυντικά", 160),

    # Βρεφικά
    ("baby", "Βρεφικά", "diapers", "Πάνες", 170),
    ("baby", "Βρεφικά", "baby_wipes", "Μωρομάντηλα", 171),
    ("baby", "Βρεφικά", "baby_accessories", "Αξεσουάρ για το Μωρό", 172),
    ("baby", "Βρεφικά", "baby_food", "Βρεφικές & Παιδικές Τροφές", 173),
    ("baby", "Βρεφικά", "baby_milk", "Βρεφικά & Παιδικά Γάλατα", 174),
    ("baby", "Βρεφικά", "baby_snacks", "Βρεφικά & Παιδικά Snacks", 175),
    ("baby", "Βρεφικά", "baby_creams", "Βρεφικές & Παιδικές Κρέμες", 176),
    ("baby", "Βρεφικά", "baby_care", "Βρεφική Περιποίηση", 177),

    # Κατοικίδια
    ("pets", "Κατοικίδια", "cats", "Για Γάτες", 180),
    ("pets", "Κατοικίδια", "dogs", "Για Σκύλους", 181),
    ("pets", "Κατοικίδια", "birds_fish_other", "Πτηνά, Ψάρια & Άλλα Κατοικίδια", 182),
    ("pets", "Κατοικίδια", "other_pets", "Άλλα Κατοικίδια", 183),
    ("pets", "Κατοικίδια", "pet_hygiene", "Υγιεινή Κατοικιδίων", 184),

    # Έτοιμα Γεύματα
    ("ready_meals", "Έτοιμα Γεύματα", "sandwiches", "Σάντουιτς", 190),
    ("ready_meals", "Έτοιμα Γεύματα", "salads", "Έτοιμες Σαλάτες & Συνοδευτικά", 191),
    ("ready_meals", "Έτοιμα Γεύματα", "ready_meat_pasta_soups", "Έτοιμα Γεύματα Κρέας, Ζυμαρικά & Σούπες", 192),
    ("ready_meals", "Έτοιμα Γεύματα", "ready_fish_seafood", "Έτοιμα Γεύματα Ψάρια & Θαλασσινά", 193),
    ("ready_meals", "Έτοιμα Γεύματα", "pasta_rice_meals", "Γεύματα Ζυμαρικών & Ρυζιού", 194),
    ("ready_meals", "Έτοιμα Γεύματα", "legume_veg_meals", "Γεύματα Οσπρίων & Λαχανικών", 195),
    ("ready_meals", "Έτοιμα Γεύματα", "meat_poultry_meals", "Γεύματα με Κρέας & Πουλερικά", 196),
    ("ready_meals", "Έτοιμα Γεύματα", "fish_sushi_meals", "Γεύματα με Ψάρια, Θαλασσινά & Sushi", 197),
    ("ready_meals", "Έτοιμα Γεύματα", "oily_vegetable_meals", "Λαδερά", 198),
    ("ready_meals", "Έτοιμα Γεύματα", "soups", "Σούπες", 199),

    # Αλκοολούχα
    ("alcohol", "Αλκοολούχα", "wine", "Κρασί", 200),
    ("alcohol", "Αλκοολούχα", "beer", "Μπύρα", 201),
    ("alcohol", "Αλκοολούχα", "cider", "Μηλίτες", 202),
    ("alcohol", "Αλκοολούχα", "spirits", "Ποτά", 203),
]

# =========================================================
# 3. Source taxonomy mappings
# tuple:
# (source_category, source_subcategory, canonical_category_code, canonical_subcategory_code, mapping_type, notes)
# =========================================================

SOURCE_MAPPINGS = {
    "ab": [
        # Φρέσκα
        ("Οπωροπωλείο", "Φρούτα", "fresh_food", "fruits", "exact_pair", None),
        ("Οπωροπωλείο", "Λαχανικά", "fresh_food", "vegetables", "exact_pair", None),
        ("Οπωροπωλείο", None, "fresh_food", "vegetables", "category_fallback", "Fallback μόνο όταν λείπει υποκατηγορία"),

        # Άρτος Ζαχαροπλαστείο
        ("Άρτος Ζαχαροπλαστείο", "Cakes-Danish-Donuts", "bakery", "pastries", "exact_pair", None),
        ("Άρτος Ζαχαροπλαστείο", "Κουλούρια αλμυρά", "bakery", "cookies_rings", "exact_pair", None),
        ("Άρτος Ζαχαροπλαστείο", "Κουλούρια γλυκά", "bakery", "cookies_rings", "exact_pair", None),
        ("Άρτος Ζαχαροπλαστείο", "Κριτσίνια & Croutons", "bakery", "breadsticks_croutons", "exact_pair", None),
        ("Άρτος Ζαχαροπλαστείο", "Κρουασάν", "bakery", "pastries", "exact_pair", None),
        ("Άρτος Ζαχαροπλαστείο", "Παξιμάδια", "bakery", "rusks", "exact_pair", None),
        ("Άρτος Ζαχαροπλαστείο", "Παραδοσιακά Γλυκά", "bakery", "sweet_breads", "exact_pair", None),
        ("Άρτος Ζαχαροπλαστείο", "Τσουρέκια", "bakery", "sweet_breads", "exact_pair", None),
        ("Άρτος Ζαχαροπλαστείο", "Φρέσκο ψωμί", "bakery", "bread", "exact_pair", None),
        ("Άρτος Ζαχαροπλαστείο", "Φρυγανιές", "bakery", "rusks", "exact_pair", None),
        ("Άρτος Ζαχαροπλαστείο", "Χαλβάς", "bakery", "halva", "exact_pair", None),
        ("Άρτος Ζαχαροπλαστείο", "Ψωμί του τοστ", "bakery", "toast_bread", "exact_pair", None),

        # Έτοιμα Γεύματα
        ("Έτοιμα Γεύματα", "Έτοιμα Γεύματα Κρέας,Ζυμαρικά & Σούπες", "ready_meals", "ready_meat_pasta_soups", "exact_pair", None),
        ("Έτοιμα Γεύματα", "Έτοιμα Γεύματα Ψάρια & Θαλασσινά", "ready_meals", "ready_fish_seafood", "exact_pair", None),
        ("Έτοιμα Γεύματα", "Έτοιμα Σάντουιτς", "ready_meals", "sandwiches", "exact_pair", None),
        ("Έτοιμα Γεύματα", "Έτοιμες Σαλάτες", "ready_meals", "salads", "exact_pair", None),

        # Όλα για το μωρό
        ("Όλα για το μωρό", "Αξεσουάρ για το μωρό", "baby", "baby_accessories", "exact_pair", None),
        ("Όλα για το μωρό", "Βιολογικά", "baby", "baby_food", "exact_pair", "Προσωρινό broad mapping"),
        ("Όλα για το μωρό", "Βρεφικές τροφές", "baby", "baby_food", "exact_pair", None),
        ("Όλα για το μωρό", "Βρεφική Περιποίηση Σώματος", "baby", "baby_care", "exact_pair", None),
        ("Όλα για το μωρό", "Μωρομάντηλα", "baby", "baby_wipes", "exact_pair", None),
        ("Όλα για το μωρό", "Πάνες Μωρού", "baby", "diapers", "exact_pair", None),

        # Βασικά τυποποιημένα τρόφιμα
        ("Βασικά τυποποιημένα τρόφιμα", "Delicatessen", "pantry", "deli", "exact_pair", None),
        ("Βασικά τυποποιημένα τρόφιμα", "Αλεύρι-Σιμιγδάλι", "pantry", "flours_sugars", "exact_pair", None),
        ("Βασικά τυποποιημένα τρόφιμα", "Διεθνής Κουζίνα", "pantry", "international", "exact_pair", None),
        ("Βασικά τυποποιημένα τρόφιμα", "Είδη ζαχαροπλαστικής", "pantry", "baking", "exact_pair", None),
        ("Βασικά τυποποιημένα τρόφιμα", "Ελαιόλαδο & Ελιές", "pantry", "oils_vinegars", "exact_pair", None),
        ("Βασικά τυποποιημένα τρόφιμα", "Ζάχαρη", "pantry", "flours_sugars", "exact_pair", None),
        ("Βασικά τυποποιημένα τρόφιμα", "Ζυμαρικά", "pantry", "pasta_rice_legumes", "exact_pair", None),
        ("Βασικά τυποποιημένα τρόφιμα", "Κονσέρβες", "pantry", "canned_jarred", "exact_pair", None),
        ("Βασικά τυποποιημένα τρόφιμα", "Μείγματα για γλυκά", "pantry", "baking", "exact_pair", None),
        ("Βασικά τυποποιημένα τρόφιμα", "Μπαχαρικά-Αλάτι", "pantry", "sauces_condiments", "exact_pair", None),
        ("Βασικά τυποποιημένα τρόφιμα", "Ξύδι-Λεμόνι", "pantry", "oils_vinegars", "exact_pair", None),
        ("Βασικά τυποποιημένα τρόφιμα", "Ρύζι - Όσπρια", "pantry", "pasta_rice_legumes", "exact_pair", None),
        ("Βασικά τυποποιημένα τρόφιμα", "Σάλτσες-Dressings", "pantry", "sauces_condiments", "exact_pair", None),
        ("Βασικά τυποποιημένα τρόφιμα", "Σούπες-Ζωμοί-Κύβοι-Πουρές", "pantry", "instant_meals", "exact_pair", None),
        ("Βασικά τυποποιημένα τρόφιμα", "Σπορέλαιο & Μαγειρικά Λίπη", "pantry", "oils_vinegars", "exact_pair", None),

        # Γαλακτοκομικά...
        ("Γαλακτοκομικά, Φυτικά Ροφήματα & Είδη Ψυγείου", "Βούτυρο-Μαργαρίνη", "dairy_chilled", "butter_cream", "exact_pair", None),
        ("Γαλακτοκομικά, Φυτικά Ροφήματα & Είδη Ψυγείου", "Γάλα", "dairy_chilled", "milk", "exact_pair", None),
        ("Γαλακτοκομικά, Φυτικά Ροφήματα & Είδη Ψυγείου", "Γάλα & Φυτικά Ροφήματα", "dairy_chilled", "milk", "exact_pair", "Broad bucket incl. plant milk"),
        ("Γαλακτοκομικά, Φυτικά Ροφήματα & Είδη Ψυγείου", "Γιαούρτια", "dairy_chilled", "yogurt", "exact_pair", None),
        ("Γαλακτοκομικά, Φυτικά Ροφήματα & Είδη Ψυγείου", "Κρέμες γάλακτος & σαντιγύ", "dairy_chilled", "butter_cream", "exact_pair", None),
        ("Γαλακτοκομικά, Φυτικά Ροφήματα & Είδη Ψυγείου", "Κρέμες-Γλυκίσματα", "dairy_chilled", "chilled_desserts", "exact_pair", None),
        ("Γαλακτοκομικά, Φυτικά Ροφήματα & Είδη Ψυγείου", "Με Χαμηλά Λιπαρά", "dairy_chilled", "low_fat", "exact_pair", None),
        ("Γαλακτοκομικά, Φυτικά Ροφήματα & Είδη Ψυγείου", "Σαλάτες-Αλοιφές", "dairy_chilled", "spreads_salads", "exact_pair", None),
        ("Γαλακτοκομικά, Φυτικά Ροφήματα & Είδη Ψυγείου", "Φρέσκες ζύμες-Φύλλα-Μαγιά", "dairy_chilled", "fresh_dough", "exact_pair", None),
        ("Γαλακτοκομικά, Φυτικά Ροφήματα & Είδη Ψυγείου", "Φυτικά Ροφήματα", "dairy_chilled", "plant_milk", "exact_pair", None),
        ("Γαλακτοκομικά, Φυτικά Ροφήματα & Είδη Ψυγείου", "Χυμοί ψυγείου", "dairy_chilled", "fridge_juices", "exact_pair", None),
        ("Γαλακτοκομικά, Φυτικά Ροφήματα & Είδη Ψυγείου", "Αυγά", "dairy_chilled", "eggs", "exact_pair", None),

        # Γιαούρτια...
        ("Γιαούρτια, Κρέμες γάλακτος & Επιδόρπια ψυγείου", "Γιαούρτια", "dairy_chilled", "yogurt", "exact_pair", None),
        ("Γιαούρτια, Κρέμες γάλακτος & Επιδόρπια ψυγείου", "Επιδόρπια Ψυγείου", "dairy_chilled", "chilled_desserts", "exact_pair", None),
        ("Γιαούρτια, Κρέμες γάλακτος & Επιδόρπια ψυγείου", "Βούτυρο & Κρέμες", "dairy_chilled", "butter_cream", "exact_pair", None),

        # Για κατοικίδια
        ("Για κατοικίδια", "Αλλα κατοικίδια", "pets", "other_pets", "exact_pair", None),
        ("Για κατοικίδια", "Για γάτες", "pets", "cats", "exact_pair", None),
        ("Για κατοικίδια", "Για σκύλους", "pets", "dogs", "exact_pair", None),
        ("Για κατοικίδια", "Υγιεινή ζώων", "pets", "pet_hygiene", "exact_pair", None),

        # Personal care
        ("Είδη προσωπικής περιποίησης", "Ανδρική περιποίηση", "personal_care", "mens_care", "exact_pair", None),
        ("Είδη προσωπικής περιποίησης", "Αντηλιακά", "personal_care", "body_care", "exact_pair", "Temporary body care mapping"),
        ("Είδη προσωπικής περιποίησης", "Γυναικεία περιποίηση", "personal_care", "womens_care", "exact_pair", None),
        ("Είδη προσωπικής περιποίησης", "Παραφαρμακευτικά Είδη", "personal_care", "pharma", "exact_pair", None),
        ("Είδη προσωπικής περιποίησης", "Προσωπική υγιεινή", "personal_care", "hygiene", "exact_pair", None),
        ("Είδη προσωπικής περιποίησης", "Στοματική υγιεινή", "personal_care", "oral_care", "exact_pair", None),
        ("Είδη προσωπικής περιποίησης", "Φροντίδα μαλλιών", "personal_care", "hair_care", "exact_pair", None),
        ("Είδη προσωπικής περιποίησης", "Φροντίδα σώματος", "personal_care", "body_care", "exact_pair", None),

        # Beverages
        ("Κάβα, αναψυκτικά, νερά, ξηροί καρποί", "Aποξηραμένα φρούτα", "snacks_breakfast", "nuts_dried_fruits", "exact_pair", None),
        ("Κάβα, αναψυκτικά, νερά, ξηροί καρποί", "Αναψυκτικά", "beverages", "soft_drinks", "exact_pair", None),
        ("Κάβα, αναψυκτικά, νερά, ξηροί καρποί", "Βιολογικά", "beverages", "juices", "exact_pair", "Temporary broad mapping"),
        ("Κάβα, αναψυκτικά, νερά, ξηροί καρποί", "Κρασιά", "alcohol", "wine", "exact_pair", None),
        ("Κάβα, αναψυκτικά, νερά, ξηροί καρποί", "Μπύρες", "alcohol", "beer", "exact_pair", None),
        ("Κάβα, αναψυκτικά, νερά, ξηροί καρποί", "Νερά", "beverages", "water", "exact_pair", None),
        ("Κάβα, αναψυκτικά, νερά, ξηροί καρποί", "Ξηροί καρποί", "snacks_breakfast", "nuts_dried_fruits", "exact_pair", None),
        ("Κάβα, αναψυκτικά, νερά, ξηροί καρποί", "Ποτά", "alcohol", "spirits", "exact_pair", None),
        ("Κάβα, αναψυκτικά, νερά, ξηροί καρποί", "Χυμοί εκτός ψυγείου", "beverages", "juices", "exact_pair", None),

        # Cleaning / household
        ("Καθαριστικά - Χαρτικά & είδη σπιτιού", "Αξεσουάρ καθαρισμού", "household_cleaning", "cleaning_accessories", "exact_pair", None),
        ("Καθαριστικά - Χαρτικά & είδη σπιτιού", "Απορρυπαντικά Πιάτων", "household_cleaning", "dish_detergents", "exact_pair", None),
        ("Καθαριστικά - Χαρτικά & είδη σπιτιού", "Απορρυπαντικά Πλυντηρίου Ρούχων", "household_cleaning", "laundry_detergents", "exact_pair", None),
        ("Καθαριστικά - Χαρτικά & είδη σπιτιού", "Απορρυπαντικά για πλύσιμο στο χέρι", "household_cleaning", "hand_wash_laundry", "exact_pair", None),
        ("Καθαριστικά - Χαρτικά & είδη σπιτιού", "Αποσκληρυντικά πλυντηρίου", "household_cleaning", "dishwasher_additives", "exact_pair", None),
        ("Καθαριστικά - Χαρτικά & είδη σπιτιού", "Αρωματικά-Κεριά", "household_cleaning", "air_fresheners", "exact_pair", None),
        ("Καθαριστικά - Χαρτικά & είδη σπιτιού", "Γραφική Ύλη & Αναλώσιμα", "household_cleaning", "stationery", "exact_pair", None),
        ("Καθαριστικά - Χαρτικά & είδη σπιτιού", "Δώρα & Παιχνίδια", "household_cleaning", "home_goods", "exact_pair", "Temporary fallback"),
        ("Καθαριστικά - Χαρτικά & είδη σπιτιού", "Είδη οικιακής χρήσης", "household_cleaning", "home_goods", "exact_pair", None),
        ("Καθαριστικά - Χαρτικά & είδη σπιτιού", "Είδη σιδερώματος-Λευκά Είδη", "household_cleaning", "ironing_linen", "exact_pair", None),
        ("Καθαριστικά - Χαρτικά & είδη σπιτιού", "Εντομοαπωθητικά-Εντομοκτόνα", "household_cleaning", "insect_control", "exact_pair", None),
        ("Καθαριστικά - Χαρτικά & είδη σπιτιού", "Εποχιακά Είδη", "household_cleaning", "home_goods", "exact_pair", "Temporary fallback"),
        ("Καθαριστικά - Χαρτικά & είδη σπιτιού", "Καθαριστικά", "household_cleaning", "home_cleaning", "exact_pair", None),
        ("Καθαριστικά - Χαρτικά & είδη σπιτιού", "Λευκαντικά & Ενισχυτικά Πλυσίματος", "household_cleaning", "bleach_boosters", "exact_pair", None),
        ("Καθαριστικά - Χαρτικά & είδη σπιτιού", "Μαλακτικά ρούχων", "household_cleaning", "fabric_softeners", "exact_pair", None),
        ("Καθαριστικά - Χαρτικά & είδη σπιτιού", "Φύλαξη ρούχων", "household_cleaning", "clothes_storage", "exact_pair", None),
        ("Καθαριστικά - Χαρτικά & είδη σπιτιού", "Χαρτί oικιακής χρήσης", "household_cleaning", "paper_goods", "exact_pair", None),

        # Frozen
        ("Κατεψυγμένα τρόφιμα", "Κατεψυγμένα Έτοιμα Φαγητά", "frozen", "frozen_meals", "exact_pair", None),
        ("Κατεψυγμένα τρόφιμα", "Κατεψυγμένα Ψάρια & Θαλασσινά", "frozen", "frozen_meat_fish", "exact_pair", None),
        ("Κατεψυγμένα τρόφιμα", "Κατεψυγμένα φρούτα & λαχανικά", "frozen", "frozen_vegetables", "exact_pair", None),
        ("Κατεψυγμένα τρόφιμα", "Κατεψυγμένες Πίτσες & Φύλλα & Πίτες", "frozen", "frozen_pastry", "exact_pair", None),
        ("Κατεψυγμένα τρόφιμα", "Κατεψυγμένο Κρέας", "frozen", "frozen_meat_fish", "exact_pair", None),
        ("Κατεψυγμένα τρόφιμα", "Παγωτά", "frozen", "ice_cream", "exact_pair", None),

        # Breakfast / snacks
        ("Πρωινό - snacking & ροφήματα", "Βιολογικά", "snacks_breakfast", "cereals", "exact_pair", "Temporary broad mapping"),
        ("Πρωινό - snacking & ροφήματα", "Δημητριακά", "snacks_breakfast", "cereals", "exact_pair", None),
        ("Πρωινό - snacking & ροφήματα", "Κακάο-Σοκολάτα ρόφημα", "beverages", "cocoa_drinks", "exact_pair", None),
        ("Πρωινό - snacking & ροφήματα", "Καραμέλες", "beverages", "gums_candies", "exact_pair", None),
        ("Πρωινό - snacking & ροφήματα", "Καφές", "beverages", "coffee", "exact_pair", None),
        ("Πρωινό - snacking & ροφήματα", "Κράκερς", "snacks_breakfast", "crackers", "exact_pair", None),
        ("Πρωινό - snacking & ροφήματα", "Μέλι", "pantry", "spreads_honey", "exact_pair", None),
        ("Πρωινό - snacking & ροφήματα", "Μαρμελάδες", "pantry", "spreads_honey", "exact_pair", None),
        ("Πρωινό - snacking & ροφήματα", "Μπισκότα", "snacks_breakfast", "biscuits", "exact_pair", None),
        ("Πρωινό - snacking & ροφήματα", "Πραλίνα, Φυστικοβούτυρο & Ταχίνι", "snacks_breakfast", "spreads", "exact_pair", None),
        ("Πρωινό - snacking & ροφήματα", "Σνακς", "snacks_breakfast", "snacks", "exact_pair", None),
        ("Πρωινό - snacking & ροφήματα", "Σοκολάτες", "snacks_breakfast", "chocolate_sweets", "exact_pair", None),
        ("Πρωινό - snacking & ροφήματα", "Τσάι-Αφεψήματα", "beverages", "tea", "exact_pair", None),
        ("Πρωινό - snacking & ροφήματα", "Τσίχλες", "beverages", "gums_candies", "exact_pair", None),

        # Τυριά...
        ("Τυριά, Φυτικά Αναπληρώματα & Αλλαντικά", "Τυριά", "cheese_deli", "cheese", "exact_pair", None),
        ("Τυριά, Φυτικά Αναπληρώματα & Αλλαντικά", "Αλλαντικά", "cheese_deli", "cold_cuts", "exact_pair", None),
        ("Τυριά, Φυτικά Αναπληρώματα & Αλλαντικά", "Φυτικά Αναπληρώματα", "cheese_deli", "plant_substitutes", "exact_pair", None),
        ("Τυριά, Φυτικά Αναπληρώματα & Αλλαντικά", None, "cheese_deli", "cheese", "category_fallback", "AB blank subcategory fallback"),

        # Fresh meat & fish
        ("Φρέσκο Κρέας & Ψάρια", "Έτοιμες Λύσεις Κρεοπωλείου", "meat_fish", "prepared_meat", "exact_pair", None),
        ("Φρέσκο Κρέας & Ψάρια", "Αρνί - Κατσίκι", "meat_fish", "lamb_goat", "exact_pair", None),
        ("Φρέσκο Κρέας & Ψάρια", "Κιμάς", "meat_fish", "minced_meat", "exact_pair", None),
        ("Φρέσκο Κρέας & Ψάρια", "Κοτόπουλο", "meat_fish", "poultry", "exact_pair", None),
        ("Φρέσκο Κρέας & Ψάρια", "Κυνήγι", "meat_fish", "game", "exact_pair", None),
        ("Φρέσκο Κρέας & Ψάρια", "Μοσχάρι", "meat_fish", "beef", "exact_pair", None),
        ("Φρέσκο Κρέας & Ψάρια", "Φρέσκα ψάρια & θαλασσινά", "meat_fish", "fish_seafood", "exact_pair", None),
        ("Φρέσκο Κρέας & Ψάρια", "Χοιρινό", "meat_fish", "pork", "exact_pair", None),
    ],

    "sklavenitis": [
        # Έτοιμα Γεύματα
        ("Έτοιμα Γεύματα", "Έτοιμες Σαλάτες & Συνοδευτικά γευμάτων", "ready_meals", "salads", "exact_pair", None),
        ("Έτοιμα Γεύματα", "Γεύματα Ζυμαρικών & Ρυζιού", "ready_meals", "pasta_rice_meals", "exact_pair", None),
        ("Έτοιμα Γεύματα", "Γεύματα Οσπρίων & Λαχανικών", "ready_meals", "legume_veg_meals", "exact_pair", None),
        ("Έτοιμα Γεύματα", "Γεύματα με Κρέας & Πουλερικά", "ready_meals", "meat_poultry_meals", "exact_pair", None),
        ("Έτοιμα Γεύματα", "Γεύματα με Ψάρια, Θαλασσινά & Sushi", "ready_meals", "fish_sushi_meals", "exact_pair", None),
        ("Έτοιμα Γεύματα", "Λαδερά", "ready_meals", "oily_vegetable_meals", "exact_pair", None),
        ("Έτοιμα Γεύματα", "Σάντουιτς", "ready_meals", "sandwiches", "exact_pair", None),
        ("Έτοιμα Γεύματα", "Σούπες", "ready_meals", "soups", "exact_pair", None),

        # Αλλαντικά
        ("Αλλαντικά", "Αλλαντικά", "cheese_deli", "cold_cuts", "exact_pair", None),
        ("Αλλαντικά", "Αλλαντικά Γαλοπούλας & Κοτόπουλου", "cheese_deli", "cold_cuts", "exact_pair", None),
        ("Αλλαντικά", "Ζαμπόν, Μπέικον & Ωμοπλάτη", "cheese_deli", "cold_cuts", "exact_pair", None),
        ("Αλλαντικά", "Λουκάνικα", "cheese_deli", "cold_cuts", "exact_pair", None),
        ("Αλλαντικά", "Πάριζα & Μορταδέλα", "cheese_deli", "cold_cuts", "exact_pair", None),
        ("Αλλαντικά", "Παραδοσιακά αλλαντικά", "cheese_deli", "cold_cuts", "exact_pair", None),
        ("Αλλαντικά", "Σαλάμια", "cheese_deli", "cold_cuts", "exact_pair", None),
        ("Αλλαντικά", "Σετ Αλλαντικών & Τυριών", "cheese_deli", "mixed_trays", "exact_pair", None),

        # Αναψυκτικά...
        ("Αναψυκτικά, Νερά & Χυμοί", "Αναψυκτικά, Σόδες & Ενεργειακά ποτά", "beverages", "soft_drinks", "exact_pair", None),
        ("Αναψυκτικά, Νερά & Χυμοί", "Νερά", "beverages", "water", "exact_pair", None),
        ("Αναψυκτικά, Νερά & Χυμοί", "Χυμοί", "beverages", "juices", "exact_pair", None),

        # Απορρυπαντικά...
        ("Απορρυπαντικά & Είδη Καθαρισμού", "Απορρυπαντικά πιάτων", "household_cleaning", "dish_detergents", "exact_pair", None),
        ("Απορρυπαντικά & Είδη Καθαρισμού", "Απορρυπαντικά ρούχων", "household_cleaning", "laundry_detergents", "exact_pair", None),
        ("Απορρυπαντικά & Είδη Καθαρισμού", "Καθαριστικά γενικής χρήσης", "household_cleaning", "home_cleaning", "exact_pair", None),
        ("Απορρυπαντικά & Είδη Καθαρισμού", "Σύνεργα καθαρισμού", "household_cleaning", "cleaning_accessories", "exact_pair", None),

        # Αυγά...
        ("Αυγά, Βούτυρα, Νωπές Ζύμες & Ζωμοί", "Αυγά", "dairy_chilled", "eggs", "exact_pair", None),
        ("Αυγά, Βούτυρα, Νωπές Ζύμες & Ζωμοί", "Βούτυρα", "dairy_chilled", "butter_cream", "exact_pair", None),
        ("Αυγά, Βούτυρα, Νωπές Ζύμες & Ζωμοί", "Ζωμοί ψυγείου", "dairy_chilled", "fresh_dough", "exact_pair", "Προσωρινό mapping"),
        ("Αυγά, Βούτυρα, Νωπές Ζύμες & Ζωμοί", "Ζύμες νωπές", "dairy_chilled", "fresh_dough", "exact_pair", None),
        ("Αυγά, Βούτυρα, Νωπές Ζύμες & Ζωμοί", "Μαργαρίνες", "dairy_chilled", "butter_cream", "exact_pair", None),
        ("Αυγά, Βούτυρα, Νωπές Ζύμες & Ζωμοί", "Φρέσκα Ζυμαρικά & Σάλτσες", "dairy_chilled", "fresh_pasta_sauces", "exact_pair", None),

        # Βρεφικές...
        ("Βρεφικές & Παιδικές τροφές", "Βρεφικά & Παιδικά γάλατα", "baby", "baby_milk", "exact_pair", None),
        ("Βρεφικές & Παιδικές τροφές", "Βρεφικά & Παιδικά σνακ", "baby", "baby_snacks", "exact_pair", None),
        ("Βρεφικές & Παιδικές τροφές", "Βρεφικά & Παιδικά φαγητά", "baby", "baby_food", "exact_pair", None),
        ("Βρεφικές & Παιδικές τροφές", "Βρεφικές & Παιδικές κρέμες", "baby", "baby_creams", "exact_pair", None),

        # Γάλατα...
        ("Γάλατα, Ροφήματα & Χυμοί ψυγείου", "Γάλατα Σοκολατούχα ψυγείου", "dairy_chilled", "chocolate_milk", "exact_pair", None),
        ("Γάλατα, Ροφήματα & Χυμοί ψυγείου", "Γάλατα ψυγείου", "dairy_chilled", "milk", "exact_pair", None),
        ("Γάλατα, Ροφήματα & Χυμοί ψυγείου", "Φυτικά & Άλλα ροφήματα Ψυγείου", "dairy_chilled", "plant_milk", "exact_pair", None),
        ("Γάλατα, Ροφήματα & Χυμοί ψυγείου", "Χυμοί ψυγείου", "dairy_chilled", "fridge_juices", "exact_pair", None),

        # Γιαούρτια...
        ("Γιαούρτια, Κρέμες γάλακτος & Επιδόρπια ψυγείου", "Γιαούρτια", "dairy_chilled", "yogurt", "exact_pair", None),
        ("Γιαούρτια, Κρέμες γάλακτος & Επιδόρπια ψυγείου", "Γιαούρτια Βρεφικά & Παιδικά", "dairy_chilled", "kid_yogurts", "exact_pair", None),
        ("Γιαούρτια, Κρέμες γάλακτος & Επιδόρπια ψυγείου", "Επιδόρπια γιαουρτιού", "dairy_chilled", "yogurt_desserts", "exact_pair", None),
        ("Γιαούρτια, Κρέμες γάλακτος & Επιδόρπια ψυγείου", "Κρέμες γάλακτος & Σαντιγί", "dairy_chilled", "butter_cream", "exact_pair", None),
        ("Γιαούρτια, Κρέμες γάλακτος & Επιδόρπια ψυγείου", "Πρωτεϊνούχα γιαούρτια, Επιδόρπια & Γλυκίσματα ψυγείου", "dairy_chilled", "protein_desserts", "exact_pair", None),
        ("Γιαούρτια, Κρέμες γάλακτος & Επιδόρπια ψυγείου", "Ρυζόγαλα & Γλυκίσματα ψυγείου", "dairy_chilled", "rice_puddings", "exact_pair", None),
        ("Γιαούρτια, Κρέμες γάλακτος & Επιδόρπια ψυγείου", "Φυτικά επιδόρπια", "dairy_chilled", "plant_desserts", "exact_pair", None),

        # Είδη Αρτοζαχαροπλαστείου
        ("Είδη Αρτοζαχαροπλαστείου", "Γλυκά", "bakery", "pastries", "exact_pair", None),
        ("Είδη Αρτοζαχαροπλαστείου", "Κέικ, Τσουρέκια & Κρουασάν", "bakery", "pastries", "exact_pair", None),
        ("Είδη Αρτοζαχαροπλαστείου", "Κουλούρια & Βουτήματα", "bakery", "cookies_rings", "exact_pair", None),
        ("Είδη Αρτοζαχαροπλαστείου", "Κριτσίνια, Παξιμάδια & Φρυγανιές", "bakery", "breadsticks_croutons", "exact_pair", None),
        ("Είδη Αρτοζαχαροπλαστείου", "Πίτες & Τορτίγιες", "bakery", "dough", "exact_pair", None),
        ("Είδη Αρτοζαχαροπλαστείου", "Ψωμί & Αρτοσκευάσματα", "bakery", "bread", "exact_pair", None),
        ("Είδη Αρτοζαχαροπλαστείου", "Ψωμί τυποποιημένο", "bakery", "toast_bread", "exact_pair", None),

        # Είδη Οικιακής χρήσης
        ("Είδη Οικιακής χρήσης", "Αρωματικά χώρου, Συλλέκτες υγρασίας & Φίλτρα απορροφητήρα", "household_cleaning", "air_fresheners", "exact_pair", None),
        ("Είδη Οικιακής χρήσης", "Είδη Θυμιάματος", "household_cleaning", "home_goods", "exact_pair", "Temporary fallback"),
        ("Είδη Οικιακής χρήσης", "Είδη Σιδερώματος & Απλώματος", "household_cleaning", "ironing_linen", "exact_pair", None),
        ("Είδη Οικιακής χρήσης", "Είδη Υγραερίου, Αναπτήρες & Σπίρτα", "household_cleaning", "home_goods", "exact_pair", "Temporary fallback"),
        ("Είδη Οικιακής χρήσης", "Εντομοαπωθητικά & Εντομοκτόνα", "household_cleaning", "insect_control", "exact_pair", None),
        ("Είδη Οικιακής χρήσης", "Ηλεκτρικές Μικροσυσκευές", "household_cleaning", "home_goods", "exact_pair", "Temporary fallback"),
        ("Είδη Οικιακής χρήσης", "Καύσιμες ύλες", "household_cleaning", "home_goods", "exact_pair", "Temporary fallback"),
        ("Είδη Οικιακής χρήσης", "Μπαταρίες, Λάμπες, Ηλεκτρολογικά είδη & Ταινίες", "household_cleaning", "home_goods", "exact_pair", "Temporary fallback"),
        ("Είδη Οικιακής χρήσης", "Περιποίηση Υποδημάτων", "household_cleaning", "home_goods", "exact_pair", "Temporary fallback"),
        ("Είδη Οικιακής χρήσης", "Τσάντες πολλαπλών χρήσεων & Ισοθερμικές", "household_cleaning", "home_goods", "exact_pair", "Temporary fallback"),
        ("Είδη Οικιακής χρήσης", "Φύλαξη & Περιποίηση ρούχων", "household_cleaning", "clothes_storage", "exact_pair", None),

        # Είδη μιας χρήσης...
        ("Είδη μιας χρήσης & Είδη Πάρτι", "Είδη Πάρτι", "household_cleaning", "disposables_party", "exact_pair", None),
        ("Είδη μιας χρήσης & Είδη Πάρτι", "Είδη Συντήρησης & Ψησίματος τροφίμων", "household_cleaning", "disposables_party", "exact_pair", None),
        ("Είδη μιας χρήσης & Είδη Πάρτι", "Καλαμάκια & Οδοντογλυφίδες", "household_cleaning", "disposables_party", "exact_pair", None),
        ("Είδη μιας χρήσης & Είδη Πάρτι", "Σακούλες απορριμμάτων", "household_cleaning", "disposables_party", "exact_pair", None),
        ("Είδη μιας χρήσης & Είδη Πάρτι", "Σερβίτσια μιας χρήσης", "household_cleaning", "disposables_party", "exact_pair", None),

        # Είδη πρωινού & Ροφήματα
        ("Είδη πρωινού & Ροφήματα", "Γάλατα & Φυτικά ροφήματα Μακράς διαρκείας", "dairy_chilled", "plant_milk", "exact_pair", "Broad bucket incl long-life milk"),
        ("Είδη πρωινού & Ροφήματα", "Δημητριακά & Μπάρες", "snacks_breakfast", "bars", "exact_pair", None),
        ("Είδη πρωινού & Ροφήματα", "Καφέδες, Ροφήματα & Αφεψήματα", "beverages", "coffee", "exact_pair", "Broad bucket"),
        ("Είδη πρωινού & Ροφήματα", "Μέλια & Μαρμελάδες", "pantry", "spreads_honey", "exact_pair", None),
        ("Είδη πρωινού & Ροφήματα", "Πραλίνες, Ταχίνι & Φιστικοβούτυρο", "snacks_breakfast", "spreads", "exact_pair", None),
        ("Είδη πρωινού & Ροφήματα", "Πρωτεΐνες σε σκόνη", "snacks_breakfast", "protein_powders", "exact_pair", None),

        # Κάβα
        ("Κάβα", "Κρασιά & Σαμπάνιες", "alcohol", "wine", "exact_pair", None),
        ("Κάβα", "Μπίρες & Μηλίτες", "alcohol", "beer", "exact_pair", None),
        ("Κάβα", "Ποτά", "alcohol", "spirits", "exact_pair", None),

        # Καλλυντικά...
        ("Καλλυντικά & Είδη Προσωπικής υγιεινής", "Αντηλιακά", "personal_care", "body_care", "exact_pair", None),
        ("Καλλυντικά & Είδη Προσωπικής υγιεινής", "Βρεφικά & Παιδικά καλλυντικά", "personal_care", "child_care", "exact_pair", None),
        ("Καλλυντικά & Είδη Προσωπικής υγιεινής", "Είδη Ξυρίσματος & After Shave", "personal_care", "shaving", "exact_pair", None),
        ("Καλλυντικά & Είδη Προσωπικής υγιεινής", "Μακιγιάζ & Βερνίκια νυχιών", "personal_care", "makeup", "exact_pair", None),
        ("Καλλυντικά & Είδη Προσωπικής υγιεινής", "Παραφαρμακευτικά Είδη", "personal_care", "pharma", "exact_pair", None),
        ("Καλλυντικά & Είδη Προσωπικής υγιεινής", "Στοματική υγιεινή", "personal_care", "oral_care", "exact_pair", None),
        ("Καλλυντικά & Είδη Προσωπικής υγιεινής", "Υγιεινή & Περιποίηση Προσώπου", "personal_care", "face_care", "exact_pair", None),
        ("Καλλυντικά & Είδη Προσωπικής υγιεινής", "Φροντίδα Μαλλιών", "personal_care", "hair_care", "exact_pair", None),
        ("Καλλυντικά & Είδη Προσωπικής υγιεινής", "Φροντίδα Σώματος", "personal_care", "body_care", "exact_pair", None),

        # Κατεψυγμένα
        ("Κατεψυγμένα", "Κατεψυγμένα Γεύματα", "frozen", "frozen_meals", "exact_pair", None),
        ("Κατεψυγμένα", "Κατεψυγμένα Κρέατα & Πουλερικά", "frozen", "frozen_meat_fish", "exact_pair", None),
        ("Κατεψυγμένα", "Κατεψυγμένα Λαχανικά & Φρούτα", "frozen", "frozen_vegetables", "exact_pair", None),
        ("Κατεψυγμένα", "Κατεψυγμένα Φυτικά αναπληρώματα", "frozen", "frozen_plant_substitutes", "exact_pair", None),
        ("Κατεψυγμένα", "Κατεψυγμένα Ψάρια & Θαλασσινά", "frozen", "frozen_meat_fish", "exact_pair", None),
        ("Κατεψυγμένα", "Κατεψυγμένες Ζύμες, Πίτες & Πίτσες", "frozen", "frozen_pastry", "exact_pair", None),
        ("Κατεψυγμένα", "Παγωτά & Παγάκια", "frozen", "ice_icecubes", "exact_pair", None),

        # Μπισκότα...
        ("Μπισκότα, Σοκολάτες & Ζαχαρώδη", "Μπισκότα", "snacks_breakfast", "biscuits", "exact_pair", None),
        ("Μπισκότα, Σοκολάτες & Ζαχαρώδη", "Παστέλια, Μαντολάτα & Λουκούμια", "snacks_breakfast", "traditional_sweets", "exact_pair", None),
        ("Μπισκότα, Σοκολάτες & Ζαχαρώδη", "Σοκολάτες", "snacks_breakfast", "chocolate_sweets", "exact_pair", None),
        ("Μπισκότα, Σοκολάτες & Ζαχαρώδη", "Τσίχλες, Καραμέλες & Γλειφιτζούρια", "beverages", "gums_candies", "exact_pair", None),

        # Ξηροί Καρποί & Σνακ
        ("Ξηροί Καρποί & Σνακ", "Ξηροί καρποί & Αποξηραμένα φρούτα", "snacks_breakfast", "nuts_dried_fruits", "exact_pair", None),
        ("Ξηροί Καρποί & Σνακ", "Πατατάκια, Γαριδάκια & άλλα Σνακ", "snacks_breakfast", "snacks", "exact_pair", None),

        # Ορεκτικά & Delicatessen
        ("Ορεκτικά & Delicatessen", "Delicatessen θαλασσινών", "pantry", "deli", "exact_pair", "Seafood deli"),
        ("Ορεκτικά & Delicatessen", "Ελιές", "pantry", "oils_vinegars", "exact_pair", None),
        ("Ορεκτικά & Delicatessen", "Καπνιστά Ψάρια", "meat_fish", "fish_seafood", "exact_pair", None),
        ("Ορεκτικά & Delicatessen", "Πατέ & Foie gras", "pantry", "deli", "exact_pair", None),
        ("Ορεκτικά & Delicatessen", "Σαλάτες & Αλοιφές", "dairy_chilled", "spreads_salads", "exact_pair", None),
        ("Ορεκτικά & Delicatessen", "Τουρσιά & Λιαστές ντομάτες", "pantry", "canned_jarred", "exact_pair", None),
        ("Ορεκτικά & Delicatessen", "Χαλβάδες", "bakery", "halva", "exact_pair", None),
        ("Ορεκτικά & Delicatessen", "Ψάρια παστά & σε Λάδι", "meat_fish", "fish_seafood", "exact_pair", None),

        # Pets
        ("Τροφές & Είδη για Κατοικίδια", "Τροφές & Είδη για Γάτες", "pets", "cats", "exact_pair", None),
        ("Τροφές & Είδη για Κατοικίδια", "Τροφές & Είδη για Σκύλους", "pets", "dogs", "exact_pair", None),
        ("Τροφές & Είδη για Κατοικίδια", "Τροφές για Πτηνά, Ψάρια & άλλα κατοικίδια", "pets", "birds_fish_other", "exact_pair", None),

        # Τρόφιμα Παντοπωλείου
        ("Τρόφιμα Παντοπωλείου", "Όσπρια", "pantry", "pasta_rice_legumes", "exact_pair", None),
        ("Τρόφιμα Παντοπωλείου", "Αλεύρια & Σιμιγδάλια", "pantry", "flours_sugars", "exact_pair", None),
        ("Τρόφιμα Παντοπωλείου", "Ζάχαρη & Υποκατάστατα ζάχαρης", "pantry", "flours_sugars", "exact_pair", None),
        ("Τρόφιμα Παντοπωλείου", "Ζυμαρικά", "pantry", "pasta_rice_legumes", "exact_pair", None),
        ("Τρόφιμα Παντοπωλείου", "Κέτσαπ, Μουστάρδες, Μαγιονέζες & Έτοιμες σάλτσες", "pantry", "sauces_condiments", "exact_pair", None),
        ("Τρόφιμα Παντοπωλείου", "Κονσέρβες & Κομπόστες", "pantry", "canned_jarred", "exact_pair", None),
        ("Τρόφιμα Παντοπωλείου", "Λάδια & Λίπη", "pantry", "oils_vinegars", "exact_pair", None),
        ("Τρόφιμα Παντοπωλείου", "Μείγματα για Ζελέ & Γλυκά", "pantry", "baking", "exact_pair", None),
        ("Τρόφιμα Παντοπωλείου", "Μπαχαρικά, Αλάτια, Ξίδια & Ζωμοί", "pantry", "sauces_condiments", "exact_pair", None),
        ("Τρόφιμα Παντοπωλείου", "Ντοματικά", "pantry", "tomato_products", "exact_pair", None),
        ("Τρόφιμα Παντοπωλείου", "Πουρέδες, Σούπες & Noodles", "pantry", "instant_meals", "exact_pair", None),
        ("Τρόφιμα Παντοπωλείου", "Ρύζια", "pantry", "pasta_rice_legumes", "exact_pair", None),
        ("Τρόφιμα Παντοπωλείου", "Σιτάρι, Κινόα, Σόγια & άλλα Δημητριακά", "pantry", "grains", "exact_pair", None),
        ("Τρόφιμα Παντοπωλείου", "Υλικά Μαγειρικής & Ζαχαροπλαστικής", "pantry", "baking", "exact_pair", None),

        # Τυροκομικά
        ("Τυροκομικά & Φυτικά Αναπληρώματα", "Τυριά", "cheese_deli", "cheese", "exact_pair", None),
        ("Τυροκομικά & Φυτικά Αναπληρώματα", "Φυτικά Αναπληρώματα", "cheese_deli", "plant_substitutes", "exact_pair", None),
        ("Τυροκομικά & Φυτικά Αναπληρώματα", "Ημίσκληρα τυριά", "cheese_deli", "cheese", "exact_pair", None),
        ("Τυροκομικά & Φυτικά Αναπληρώματα", "Μαλακά τυριά", "cheese_deli", "cheese", "exact_pair", None),
        ("Τυροκομικά & Φυτικά Αναπληρώματα", "Σκληρά τυριά", "cheese_deli", "cheese", "exact_pair", None),
        ("Τυροκομικά & Φυτικά Αναπληρώματα", "Τυριά αλειφόμενα & Μίνι τυράκια", "cheese_deli", "cheese", "exact_pair", None),
        ("Τυροκομικά & Φυτικά Αναπληρώματα", "Φέτα & Λευκά τυριά", "cheese_deli", "cheese", "exact_pair", None),

        # Φρέσκα Φρούτα...
        ("Φρέσκα Φρούτα & Λαχανικά", "Φρούτα", "fresh_food", "fruits", "exact_pair", None),
        ("Φρέσκα Φρούτα & Λαχανικά", "Λαχανικά", "fresh_food", "vegetables", "exact_pair", None),
        ("Φρέσκα Φρούτα & Λαχανικά", "Βότανα & Μυρωδικά", "fresh_food", "herbs", "exact_pair", None),
        ("Φρέσκα Φρούτα & Λαχανικά", "Κομμένα Λαχανικά", "fresh_food", "vegetables", "exact_pair", None),

        # Φρέσκο Κρέας
        ("Φρέσκο Κρέας", "Φρέσκα Αρνιά & Κατσίκια", "meat_fish", "lamb_goat", "exact_pair", None),
        ("Φρέσκο Κρέας", "Φρέσκα Παρασκευάσματα Κρεάτων & Πουλερικών", "meat_fish", "prepared_meat", "exact_pair", None),
        ("Φρέσκο Κρέας", "Φρέσκα Πουλερικά", "meat_fish", "poultry", "exact_pair", None),
        ("Φρέσκο Κρέας", "Φρέσκο Μοσχάρι", "meat_fish", "beef", "exact_pair", None),
        ("Φρέσκο Κρέας", "Φρέσκο Χοιρινό", "meat_fish", "pork", "exact_pair", None),

        # Φρέσκο Ψάρι
        ("Φρέσκο Ψάρι & Θαλασσινά", "Οστρακοειδή", "meat_fish", "shellfish", "exact_pair", None),
        ("Φρέσκο Ψάρι & Θαλασσινά", "Χταπόδια, Καλαμάρια & Σουπιές", "meat_fish", "cephalopods", "exact_pair", None),
        ("Φρέσκο Ψάρι & Θαλασσινά", "Ψάρια Ιχθυοκαλλιέργειας", "meat_fish", "farm_fish", "exact_pair", None),

        # Χαρτικά...
        ("Χαρτικά, Πάνες & Σερβιέτες", "Βρεφικές & Παιδικές πάνες, Μωρομάντιλα", "baby", "diapers", "exact_pair", "Mixed diapers+wipes"),
        ("Χαρτικά, Πάνες & Σερβιέτες", "Σερβιέτες & Πάνες ενηλίκων", "personal_care", "hygiene", "exact_pair", None),
        ("Χαρτικά, Πάνες & Σερβιέτες", "Χαρτικά", "household_cleaning", "paper_goods", "exact_pair", None),

        # Χαρτοπωλείο
        ("Χαρτοπωλείο", "Γραφική ύλη & Οργάνωση Γραφείου", "household_cleaning", "stationery", "exact_pair", None),
        ("Χαρτοπωλείο", "Τετράδια, Μπλοκ, Φάκελοι & Χαρτί Φωτοτυπικό", "household_cleaning", "stationery", "exact_pair", None),
    ],
}


def main():
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "market_product.db")

    init_db(db_path)

    engine = create_engine(f"sqlite:///{db_path}")
    Session = sessionmaker(bind=engine)
    session = Session()

    # 1. supermarkets
    for supermarket_name in SUPERMARKETS:
        exists = session.query(Supermarket).filter_by(name=supermarket_name).first()
        if not exists:
            session.add(Supermarket(name=supermarket_name))
    session.commit()

    supermarkets_index = {
        sm.name: sm.id
        for sm in session.query(Supermarket).all()
    }

    # 2. canonical taxonomy
    for category_code, category_label, subcategory_code, subcategory_label, sort_order in CANONICAL_ROWS:
        exists = session.query(CanonicalTaxonomy).filter_by(
            category_code=category_code,
            subcategory_code=subcategory_code,
        ).first()

        if exists:
            continue

        session.add(
            CanonicalTaxonomy(
                category_code=category_code,
                category_label=category_label,
                subcategory_code=subcategory_code,
                subcategory_label=subcategory_label,
                is_active=1,
                sort_order=sort_order,
            )
        )

    session.commit()

    taxonomy_index = {
        (row.category_code, row.subcategory_code): row.id
        for row in session.query(CanonicalTaxonomy).all()
    }

    # 3. source mappings
    for supermarket_name, mappings in SOURCE_MAPPINGS.items():
        supermarket_id = supermarkets_index.get(supermarket_name)
        if not supermarket_id:
            print(f"Skipping unknown supermarket: {supermarket_name}")
            continue

        for (
            source_category,
            source_subcategory,
            canonical_category_code,
            canonical_subcategory_code,
            mapping_type,
            notes,
        ) in mappings:
            canonical_id = taxonomy_index.get(
                (canonical_category_code, canonical_subcategory_code)
            )

            if not canonical_id:
                print(
                    f"Missing canonical taxonomy row for "
                    f"{canonical_category_code}/{canonical_subcategory_code}"
                )
                continue

            exists = session.query(SourceTaxonomyMapping).filter_by(
                supermarket_id=supermarket_id,
                source_category=source_category,
                source_subcategory=source_subcategory,
            ).first()

            if exists:
                continue

            session.add(
                SourceTaxonomyMapping(
                    supermarket_id=supermarket_id,
                    source_category=source_category,
                    source_subcategory=source_subcategory,
                    canonical_taxonomy_id=canonical_id,
                    mapping_type=mapping_type,
                    is_active=1,
                    notes=notes,
                )
            )

    session.commit()
    session.close()

    print("Taxonomy seed completed.")


if __name__ == "__main__":
    main()