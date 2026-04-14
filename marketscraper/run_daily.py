import subprocess
import datetime

PROJECT_DIR  = r"C:\Users\user\Documents\Python\PythonProject\marketscraper\marketscraper"
VENV_PYTHON  = r"C:\Users\user\Documents\Python\PythonProject\.venv\Scripts\python.exe"

SPIDERS = ["sklavenitis", "ab"]


def run_spider(name):
    start = datetime.datetime.now()

    subprocess.run(
        [VENV_PYTHON, "-m", "scrapy", "crawl", name],
        cwd=PROJECT_DIR
    )
    end = datetime.datetime.now()

    return start, end, end-start


if __name__ == "__main__":
    total_start = datetime.datetime.now()

    spiderlist = []

    for spider in SPIDERS:
        start,end, duration = run_spider(spider)
        dict = {
            "spider": spider,
            "start": start,
            "end": end,
            "duration": duration
        }
        spiderlist.append(dict.copy())

    total_end = datetime.datetime.now()
    print("Αποτελέσματα ανά spider:")
    for s in spiderlist:
        print(f"Spider: {s['spider']}\nΈναρξη: {s['start']:%Y-%m-%d %H:%M:%S}\nΟλοκλήρωση: {s['end']:%Y-%m-%d %H:%M:%S}\nΔιάρκεια: {s['duration']}\n")
    print(f"Εκκίνηση: {total_start:%Y-%m-%d %H:%M:%S}\nΟλοκλήρωση: {total_end:%Y-%m-%d %H:%M:%S}\nΣυνολική διάρκεια: {total_end - total_start}")