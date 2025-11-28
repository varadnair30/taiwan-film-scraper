import json
import csv
import time
import re
from datetime import datetime
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def load_config():
    """Read settings from config file"""
    with open('config.json', 'r') as f:
        return json.load(f)

def setup_driver(config):
    """Initialize Chrome with custom options to avoid detection"""
    opts = Options()

    if config.get('headless', False):
        opts.add_argument('--headless=new')

    # Proxy config if needed
    if config.get('use_proxy', False) and config.get('proxy_url'):
        opts.add_argument(f'--proxy-server={config["proxy_url"]}')

    # These help avoid being flagged as a bot
    opts.add_argument('--disable-blink-features=AutomationControlled')
    opts.add_argument('--no-sandbox')
    opts.add_argument('--disable-dev-shm-usage')
    opts.add_argument('--disable-gpu')
    opts.add_argument('--window-size=1920,1080')
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option('useAutomationExtension', False)

    # Real user agent
    opts.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

    # Prevent crash popups
    opts.add_argument('--disable-crash-reporter')
    opts.add_argument('--disable-in-process-stack-traces')

    try:
        driver = webdriver.Chrome(options=opts)
        driver.set_page_load_timeout(30)  # 30 sec max wait
        return driver
    except Exception as e:
        print(f"Chrome startup failed: {e}")
        raise

def extract_year(text):
    """Pull 4-digit year from strings like 'Movie Title (2000)'"""
    match = re.search(r'\((\d{4})\)', text)
    return match.group(1) if match else "N/A"

def scrape_once():
    """Main scraping logic - runs once and saves results"""
    config = load_config()
    driver = None
    results = []

    try:
        print("Starting browser...")
        driver = setup_driver(config)
        target = config['base_url']

        print(f"Loading {target}...")
        driver.get(target)

        # Wait for table to actually load
        print("Waiting for content...")
        wait = WebDriverWait(driver, 15)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "tbody")))

        # Give it a bit more time to fully render
        time.sleep(config.get('page_load_delay', 3))

        print("Extracting movie data...")

        # Grab all table rows
        rows = driver.find_elements(By.CSS_SELECTOR, config['movie_selector'])

        print(f"Found {len(rows)} entries")

        for i, row in enumerate(rows, 1):
            try:
                cells = row.find_elements(By.TAG_NAME, 'td')

                if len(cells) < 4:
                    continue  # Skip incomplete rows

                # Title is a link in the 2nd column
                link_elem = cells[1].find_element(By.TAG_NAME, 'a')
                movie_title = link_elem.text.strip()
                url = link_elem.get_attribute('href')

                # Year is in parentheses after title
                full_text = cells[1].text.strip()
                movie_year = extract_year(full_text)

                # Score and vote count
                rating = cells[2].text.strip() if len(cells) > 2 else "N/A"
                vote_count = cells[3].text.strip() if len(cells) > 3 else "N/A"

                entry = {
                    'rank': i,
                    'title': movie_title,
                    'year': movie_year,
                    'score': rating,
                    'votes': vote_count,
                    'detail_url': url,
                    'scraped_at': datetime.now().isoformat()
                }

                results.append(entry)
                print(f"  #{i}: {movie_title} ({movie_year}) - {rating}/10")

            except Exception as e:
                print(f"Skipped row {i}: {e}")
                continue

        # Write to disk
        if results:
            save_data(results, config)
            write_log(len(results), "SUCCESS")
            print(f"\n✓ Done! Scraped {len(results)-1} movies")
        else:
            print("\n✗ Nothing scraped")
            write_log(0, "NO DATA")

    except Exception as e:
        err = str(e)
        print(f"\n✗ Scraping failed: {err}")
        write_log(0, f"ERROR: {err}")

    finally:
        if driver:
            print("Closing browser...")
            try:
                driver.quit()
            except:
                pass  # Already closed

    return len(results)

def save_data(data, config):
    """Write scraped data to JSON and CSV files"""
    if not data:
        return

    # Make sure data folder exists
    Path('data').mkdir(exist_ok=True)

    ts = datetime.now().strftime('%Y%m%d_%H%M%S')

    # JSON format
    if config.get('save_json', True):
        json_path = f"data/movies_{ts}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"  → {json_path}")

    # CSV format
    if config.get('save_csv', True):
        csv_path = f"data/movies_{ts}.csv"
        fields = data[0].keys()
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            writer.writerows(data)
        print(f"  → {csv_path}")

def write_log(count, status):
    """Append run summary to log file"""
    Path('data').mkdir(exist_ok=True)
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    line = f"{ts} | Movies: {count} | Status: {status}\n"

    with open('data/log.txt', 'a', encoding='utf-8') as f:
        f.write(line)

def continuous_mode():
    """Keep running scraper at regular intervals"""
    config = load_config()
    run_num = 0

    print("Starting continuous mode...")
    print(f"Interval: {config['run_interval_seconds']} seconds")
    print("Press Ctrl+C to stop\n")

    while True:
        run_num += 1
        print(f"\n{'='*60}")
        print(f"Run #{run_num} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print('='*60)

        try:
            scrape_once()
        except KeyboardInterrupt:
            print("\n\nStopped by user")
            break
        except Exception as e:
            print(f"Run failed: {e}")

        wait_time = config['run_interval_seconds']
        print(f"\nNext run in {wait_time} seconds...")
        try:
            time.sleep(wait_time)
        except KeyboardInterrupt:
            print("\n\nStopped by user")
            break

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "once":
        print("=" * 60)
        print("SINGLE RUN MODE")
        print("=" * 60)
        scrape_once()
    else:
        continuous_mode()