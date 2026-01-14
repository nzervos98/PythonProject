# Utilizing scrapy lib for webscraping supermarket prices, tracking favorite porducts and monitoring price fluctuations on items marked as favorites.
## Run run_daily.py to start crawling proccess (~10 min).
### Every item and relevant data is saved to a database.
### If an item exists in the database and the price changed since the last run, it updates the price through triggers.
### If an item is marked as favorite, the app notes the price change for each crawl, (email notification to be implemented).
## For favorite/history functions, run app.py.
### The Flask application initially draws all the available products, with opotions for filtering.
### It provides functions for marking an item as a favorite where, through triggers, it begins monitoring the price history of the specific item and it also includes the item in the next price change report. If an item is marked as not favorite, the price monitoring is erased and it is no longer included in the price change report.
