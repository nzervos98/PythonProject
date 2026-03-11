import subprocess
import datetime

PROJECT_DIR  = r"C:\Users\user\Documents\Python\PythonProject\marketscraper\marketscraper"
VENV_PYTHON  = r"C:\Users\user\Documents\Python\PythonProject\.venv\Scripts\python.exe"

SPIDERS = ["sklavenitis", "ab"]


def run_spider(name):
    start = datetime.datetime.now()
    print(f"[{start:%Y-%m-%d %H:%M:%S}] ▶️  Εκκίνηση spider: {name} ...")
    subprocess.run(
        [VENV_PYTHON, "-m", "scrapy", "crawl", name],
        cwd=PROJECT_DIR
    )
    end = datetime.datetime.now()
    print(f"[{end:%Y-%m-%d %H:%M:%S}] ✅ {name} ολοκληρώθηκε — διάρκεια: {end - start}\n")


if __name__ == "__main__":
    total_start = datetime.datetime.now()
    print(f"=== Έναρξη daily crawl: {total_start:%Y-%m-%d %H:%M:%S} ===\n")

    for spider in SPIDERS:
        run_spider(spider)

    total_end = datetime.datetime.now()
    print(f"=== Ολοκλήρωση: {total_end:%Y-%m-%d %H:%M:%S} | Συνολική διάρκεια: {total_end - total_start} ===")