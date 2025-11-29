import json
import csv
import time
import re
from datetime import datetime
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def load_config():
    """Read settings from config file"""
    with open('config.json', 'r') as f:
        return json.load(f)

def setup_driver(config):
    """Initialize Chrome with stronger anti-detection"""
    opts = Options()

    if config.get('headless', False):
        opts.add_argument('--headless=new')

    if config.get('use_proxy', False) and config.get('proxy_url'):
        opts.add_argument(f'--proxy-server={config["proxy_url"]}')

    opts.add_argument('--disable-blink-features=AutomationControlled')
    opts.add_argument('--disable-dev-shm-usage')
    opts.add_argument('--no-sandbox')
    opts.add_argument('--disable-gpu')
    opts.add_argument('--window-size=1920,1080')
    opts.add_argument('--start-maximized')
    opts.add_argument('--disable-extensions')
    opts.add_argument('--dns-prefetch-disable')
    opts.add_argument('--disable-browser-side-navigation')

    opts.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
    opts.add_experimental_option('useAutomationExtension', False)

    opts.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36')

    try:
        driver = webdriver.Chrome(options=opts)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        driver.set_page_load_timeout(30)
        return driver
    except Exception as e:
        print(f"Chrome startup failed: {e}")
        raise

def google_search_improved(driver, query, max_results=10):
    """Search Google and extract real URLs"""
    print(f"Searching Google for: '{query}'")

    try:
        driver.get("https://www.google.com")
        time.sleep(3)

        # Handle cookie consent
        try:
            buttons = driver.find_elements(By.TAG_NAME, "button")
            for btn in buttons:
                if any(word in btn.text.lower() for word in ['accept', 'agree', 'ok']):
                    btn.click()
                    time.sleep(1)
                    break
        except:
            pass

        # Search
        try:
            search_box = driver.find_element(By.NAME, "q")
        except:
            search_box = driver.find_element(By.CSS_SELECTOR, "textarea[name='q']")

        search_box.send_keys(query)
        search_box.send_keys(Keys.RETURN)
        time.sleep(5)

        print("  Checking page content...")

        # Try multiple selector strategies
        urls = []

        try:
            results = driver.find_elements(By.CSS_SELECTOR, "div.g a[href]")
            for result in results[:max_results * 2]:
                try:
                    url = result.get_attribute('href')
                    if url and url.startswith('http') and 'google.com' not in url and 'youtube.com' not in url:
                        if url not in urls:
                            urls.append(url)
                except:
                    continue
        except:
            pass

        if len(urls) < 3:
            try:
                links = driver.find_elements(By.CSS_SELECTOR, "a[jsname]")
                for link in links[:max_results * 2]:
                    try:
                        url = link.get_attribute('href')
                        if url and url.startswith('http') and 'google.com' not in url and 'youtube.com' not in url:
                            if url not in urls:
                                urls.append(url)
                    except:
                        continue
            except:
                pass

        if len(urls) < 3:
            try:
                all_links = driver.find_elements(By.TAG_NAME, "a")
                for link in all_links:
                    try:
                        url = link.get_attribute('href')
                        if url and url.startswith('http') and 'google.com' not in url and 'youtube.com' not in url and 'facebook.com' not in url:
                            if url not in urls:
                                urls.append(url)
                    except:
                        continue
            except:
                pass

        # Clean URLs
        clean_urls = []
        for url in urls:
            clean_url = url.split('#')[0]
            if clean_url not in clean_urls:
                clean_urls.append(clean_url)

        # Limit to max_results
        final_urls = clean_urls[:max_results]

        print(f"  Found {len(final_urls)} URLs from Google")
        for i, url in enumerate(final_urls, 1):
            print(f"    {i}. {url[:70]}...")

        return final_urls

    except Exception as e:
        print(f"  Google search error: {e}")
        return []

def extract_year(text):
    """Pull 4-digit year from strings"""
    match = re.search(r'\b(19|20)\d{2}\b', text)
    return match.group(0) if match else "N/A"

def is_valid_movie_title(title):
    """Check if title looks like a real movie"""
    if not title or len(title) < 2:
        return False

    # Blacklist junk
    junk_words = [
        'home', 'login', 'signup', 'register', 'search', 'browse', 'menu',
        'movies', 'tv shows', 'people', 'more', 'join', 'introduction',
        'donate', 'create account', 'log in', 'sign up', 'see also',
        'top', 'privacy', 'terms', 'about', 'contact', 'help', 'faq',
        'pre 1970', '1970s', '1980s', '1990s', '2000s', '2010s', '2020s'
    ]

    title_lower = title.lower().strip()

    if title_lower in junk_words:
        return False

    # Check starts with junk
    for junk in junk_words:
        if title_lower.startswith(junk + ' '):
            return False

    if len(title) < 2:
        return False

    if not re.search(r'[a-zA-Z]', title):
        return False

    return True

def scrape_imdb_list(driver, max_items):
    """Scrape IMDb movie lists"""
    movies = []

    try:
        time.sleep(3)

        items = driver.find_elements(By.CSS_SELECTOR, "div.lister-item")

        if not items:
            items = driver.find_elements(By.CSS_SELECTOR, "li.ipc-metadata-list-summary-item")

        print(f"    Found {len(items)} IMDb items")

        for idx, item in enumerate(items[:max_items], 1):
            try:
                # Get title
                try:
                    title_elem = item.find_element(By.CSS_SELECTOR, "h3.lister-item-header a")
                    title = title_elem.text.strip()
                    detail_url = title_elem.get_attribute('href')
                except:
                    try:
                        title_elem = item.find_element(By.CSS_SELECTOR, "a.ipc-title-link-wrapper")
                        title = title_elem.text.strip()
                        detail_url = title_elem.get_attribute('href')
                    except:
                        continue

                if not title or not is_valid_movie_title(title):
                    continue

                # Get year
                try:
                    year_elem = item.find_element(By.CSS_SELECTOR, "span.lister-item-year")
                    year = extract_year(year_elem.text)
                except:
                    year = extract_year(item.text)

                # Get rating
                try:
                    rating = item.find_element(By.CSS_SELECTOR, "div.ipc-rating-star").text.split()[0]
                except:
                    try:
                        rating = item.find_element(By.CSS_SELECTOR, "span.ipc-rating-star--rating").text
                    except:
                        rating = "N/A"

                entry = {
                    'source_url': driver.current_url.split('#')[0],
                    'title': title,
                    'year': year,
                    'score': rating,
                    'votes': "N/A",
                    'detail_url': detail_url if detail_url.startswith('http') else f"https://www.imdb.com{detail_url}",
                    'scraped_at': datetime.now().isoformat()
                }

                movies.append(entry)

            except:
                continue

        return movies

    except Exception as e:
        print(f"    IMDb scraping error: {e}")
        return []

def scrape_movie_site(driver, url, max_items):
    """Try to scrape movie data from a given URL"""
    movies = []

    try:
        print(f"  Visiting: {url[:70]}...")
        driver.get(url)
        time.sleep(4)

        # Only scrape if it's IMDb
        if 'imdb.com' in url:
            movies = scrape_imdb_list(driver, max_items)
        else:
            print(f"    ⊘ Skipped (not IMDb)")

        if movies:
            print(f"    ✓ Extracted {len(movies)} movies")
        else:
            if 'imdb.com' in url:
                print(f"    ✗ No movies extracted")

    except Exception as e:
        print(f"    ✗ Failed: {str(e)[:50]}")

    return movies

def scrape_once():
    """Main scraping logic - Google search then scrape"""
    config = load_config()
    driver = None
    all_results = []
    max_movies_per_site = config.get('max_movies_per_site', 30)

    try:
        print("Starting browser...")
        driver = setup_driver(config)

        # Step 1: Search Google
        search_query = config.get('search_keyword', 'Taiwanese film')
        urls = google_search_improved(driver, search_query, max_results=config.get('max_google_results', 10))

        if not urls:
            print("\n✗ No URLs found from Google search")
            write_log(0, "NO URLS")
            return 0

        # Step 2: Scrape each URL
        print(f"\nScraping {len(urls)} websites from Google results...\n")
        for idx, url in enumerate(urls, 1):
            print(f"Site {idx}/{len(urls)}:")
            movies = scrape_movie_site(driver, url, max_movies_per_site)
            all_results.extend(movies)

            time.sleep(config.get('delay_between_sites', 3))

        # Remove duplicates
        unique_movies = []
        seen = set()
        for movie in all_results:
            key = (movie['title'].lower(), movie['year'])
            if key not in seen:
                seen.add(key)
                unique_movies.append(movie)

        # Save combined results
        if unique_movies:
            save_data(unique_movies, config)
            write_log(len(unique_movies), "SUCCESS")
            print(f"\n{'='*60}")
            print(f"✓ SUCCESS: Scraped {len(unique_movies)} movies")
            print(f"  Sites with data: {len(set([m['source_url'] for m in unique_movies]))}")
            print(f"{'='*60}")
        else:
            print(f"\n{'='*60}")
            print("✗ No movies scraped from any site")
            print(f"{'='*60}")
            write_log(0, "NO DATA")

    except Exception as e:
        err = str(e)
        print(f"\n✗ Scraping failed: {err}")
        write_log(0, f"ERROR: {err}")

    finally:
        if driver:
            print("\nClosing browser...")
            try:
                driver.quit()
            except:
                pass

    return len(unique_movies) if unique_movies else 0

def save_data(data, config):
    """Write scraped data to JSON and CSV files"""
    if not data:
        return

    Path('data').mkdir(exist_ok=True)

    ts = datetime.now().strftime('%Y%m%d_%H%M%S')

    # JSON format
    if config.get('save_json', True):
        json_path = f"data/movies_{ts}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"  → Saved: {json_path}")

    # CSV format
    if config.get('save_csv', True):
        csv_path = f"data/movies_{ts}.csv"
        fields = data[0].keys()
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            writer.writerows(data)
        print(f"  → Saved: {csv_path}")

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
        print("GOOGLE SEARCH + SCRAPE MODE")
        print("=" * 60)
        scrape_once()
    else:
        continuous_mode()