# 🛒 SuperMarket Price Tracker

Εφαρμογή παρακολούθησης τιμών supermarket με web scraping, αποθήκευση σε βάση δεδομένων και Flask UI.

---

## Αρχιτεκτονική

```
marketscraper/   ← Scrapy project (spiders, pipeline, models)
UI/              ← Flask εφαρμογή (routes, templates, static)
run_daily.py     ← Entry point για daily crawl
```

---

## Spiders

### Σκλαβενίτης (`sklavenitis`)
- Ξεκινά από τη σελίδα κατηγοριών του `sklavenitis.gr`
- Ανακαλύπτει δυναμικά κατηγορίες & υποκατηγορίες
- Χειρίζεται pagination (εντοπισμός συνολικών προϊόντων, υπολογισμός σελίδων)
- Αντλεί: όνομα, τιμή, τιμή/κιλό

### ΑΒ Βασιλόπουλος (`ab`)
- Χρησιμοποιεί το GraphQL API (`persistedQuery`) του `ab.gr`
- Αντλεί navigation tree για να ανακαλύψει κατηγορίες
- Pagination μέσω `pageNumber` / `totalPages`
- Εξάγει υποκατηγορία από το URL κάθε προϊόντος
- Συνδυάζει `manufacturerName` + `manufacturerSubBrandName` + `name` για πλήρες όνομα προϊόντος

---

## Βάση δεδομένων (SQLite / SQLAlchemy)

**Πίνακες:**
- `canonical_taxonomy` — Το κοινό μοντέλο αναφοράς για κατηγορίες και υποκατηγορίες. Γίνεται ανάθεση αυτών σε κάθε προϊόν μέσω mapping για καλύτερη οργάνωση.
- `source_taxonomy_mapping` — Χάρτης μεταξύ των κατηγοριών/υποκατηγοριών των spiders και του `canonical_taxonomy` για ομογενοποίηση δεδομένων.
- `supermarkets` — ένα record ανά spider (`sklavenitis`, `ab`)
- `products` — όλα τα προϊόντα με τιμή, κατηγορία, last_seen, favorite flag (δέχεται πλέον και στήλες με τις κανονικοποιημένες κατηγορίες)
- `price_history` — ιστορικό αλλαγών τιμής για αγαπημένα προϊόντα

**Λογική pipeline:**
- Αν το προϊόν δεν υπάρχει → insert
- Αν υπάρχει και η τιμή άλλαξε **και** είναι αγαπημένο → καταγράφεται η παλιά τιμή στο `price_history` πριν το update

---

## Εκτέλεση crawl

```bash
python run_daily.py
```

Τρέχει σειριακά  τους spiders (2 spiders, ~45 λεπτά συνολικά). 
Καταγράφει χρόνο έναρξης/λήξης για κάθε spider.

---

## Flask UI

```bash
python UI/app.py
```

**Σελίδες:**
- `/` — Αρχική
- `/skl` => `/products/skl` — Προϊόντα Σκλαβενίτη (old)
- `/ab` => `/products/ab` — Προϊόντα ΑΒ Βασιλόπουλος (old)

**Λειτουργίες:**
- Φιλτράρισμα βάσει ονόματος, κατηγορίας, υποκατηγορίας, αγαπημένων
- Toggle αγαπημένου (POST `/toggle-favorite/<id>`)
- Εμφάνιση ιστορικού τιμών για αγαπημένα προϊόντα (GET `/history/<id>`)

---

## TODO
- [ ] Email notification για αλλαγές τιμής σε αγαπημένα, πλέον βάσει supermarket.
- [ ] Προγραμματισμός αυτόματης εκτέλεσης (π.χ. Task Scheduler / cron).
- [ ] Migrate από Flask σε FastAPI για καλύτερη απόδοση και async υποστήριξη.
- [ ] Migrate από SQLite σε PostgreSQL για καλύτερη διαχείριση δεδομένων και scalability.
- [x] Μέθοδος merging κατηγοριών - υποκατηγοριών - προϊόντων για καλύτερη οργάνωση, αναζήτηση και σύγκριση.
- [ ] Μέθοδος κανονικοποίησης ονομάτων προϊόντων (π.χ. αφαίρεση περιττών λέξεων, standardization) για καλύτερη σύγκριση τιμών (Στόχος: Matching ίδιων προϊόντων).
- [ ] Feature καλαθιού για καλύτερο track αγορών (στοχευμένες επισκέψεις σε supermarket)