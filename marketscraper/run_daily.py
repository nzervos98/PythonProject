import subprocess
import datetime
#import os
#from datetime import date

# Απόλυτο path του project
PROJECT_DIR = r"C:\Users\user\Documents\Python\PythonProject\marketscraper\marketscraper"

# Path προς το python.exe του virtual environment
VENV_PYTHON = r"C:\Users\user\Documents\Python\PythonProject\.venv\Scripts\python.exe"


def run_spider():
    x = datetime.datetime.now()
    print(f"[{x}] ▶️ Εκκίνηση crawl...")

    subprocess.run(
        [VENV_PYTHON, "-m", "scrapy", "crawl", "sklspider"],
        cwd=PROJECT_DIR
    )
    y = datetime.datetime.now()
    print(f"[{y}] ✅ Ολοκληρώθηκε.\n"
          f"Διάρκεια: {y-x}\n")


if __name__ == "__main__":
    run_spider()
