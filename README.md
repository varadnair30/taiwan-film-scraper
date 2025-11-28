Taiwan Film Scraper
A Python-based web scraper for continuously collecting Chinese film data from online databases. Built with Selenium for reliable data extraction.

Demo
Scraper Demo

Automated scraping running in continuous mode

What It Does
Opens film listing pages using Chrome browser

Extracts movie titles, years, ratings, and vote counts

Saves data locally in both JSON and CSV formats

Runs continuously with configurable intervals

Handles errors and logs each run

Requirements
Python 3.8+

Chrome browser installed

Internet connection

Setup
Clone this repository

Install dependencies:

bash
pip install -r requirements.txt
Verify Chrome is installed on your system

Usage
Single Run (Testing)
bash
python demo_scraper.py once
Continuous Mode
bash
python demo_scraper.py
Press Ctrl+C to stop.

Configuration
Edit config.json to customize behavior:

json
{
  "base_url": "http://www.dianying.com/en/users/top10",
  "run_interval_seconds": 300,
  "headless": false,
  "use_proxy": false
}
Key Settings:

base_url - Target page to scrape

run_interval_seconds - Wait time between runs (300 = 5 minutes)

headless - Set true to hide browser window

use_proxy - Enable proxy support for IP rotation

Output
All results are saved in the data/ folder:

movies_YYYYMMDD_HHMMSS.json - Timestamped JSON files

movies_YYYYMMDD_HHMMSS.csv - Timestamped CSV files

log.txt - Run history with timestamps and status

Example output:

json
{
  "rank": 1,
  "title": "In the Mood for Love",
  "year": "2000",
  "score": "7.54",
  "votes": "34",
  "detail_url": "http://www.dianying.com/en/title/hyn2000",
  "scraped_at": "2025-11-28T14:15:30"
}
Project Structure
text
taiwan_scraper/
├── demo_scraper.py      # Main scraper script
├── config.json          # Configuration file
├── requirements.txt     # Python dependencies
├── data/               # Output directory (created automatically)
│   ├── movies_*.json
│   ├── movies_*.csv
│   └── log.txt
└── README.md
How It Works
Setup Phase - Launches Chrome with anti-detection settings

Navigation - Opens the target URL and waits for page load

Extraction - Locates movie table rows and parses each field

Storage - Writes results to timestamped files

Logging - Records run summary with status

The scraper uses CSS selectors to find table rows (tbody tr) and extracts data from specific columns. Year values are parsed using regex from text like "(2000)".

Handling IP Blocks
For production deployments that run 24/7, you may encounter rate limiting or IP blocks. To handle this:

Set "use_proxy": true in config.json

Add your proxy URL: "proxy_url": "http://user:pass@proxy:port"

Consider using a rotating residential proxy service

Common providers: Bright Data, Oxylabs, Smartproxy

Deployment
For continuous 24/7 operation, deploy to a cloud server:

Option 1: Simple VPS

bash
# Run in background with nohup
nohup python demo_scraper.py > output.log 2>&1 &
Option 2: Systemd Service (Linux)

bash
# Create service file at /etc/systemd/system/scraper.service
sudo systemctl enable scraper
sudo systemctl start scraper
Option 3: Docker

bash
docker build -t taiwan-scraper .
docker run -d taiwan-scraper
Notes
First run downloads ChromeDriver automatically

Adjust page_load_delay in config.json if site is slow

Check data/log.txt for run history and errors

Use headless mode for server deployments

Troubleshooting
Browser won't start:

Verify Chrome is installed

Check ChromeDriver compatibility with your Chrome version

No data scraped:

Inspect the target page HTML - selectors may have changed

Increase page_load_delay in config.json

Target window closed error:

Site may be blocking automated access

Enable proxy or add longer delays