# Taiwan Movie Scraper - Demo

Simple continuous web scraper for Taiwanese film websites using Selenium.

## Setup

1. Install Python 3.8 or higher

2. Create virtual environment (optional but recommended):
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

## Configuration

Edit `config.json` to adjust:

- `base_url`: Target website
- `movie_selector`, `title_selector`, `year_selector`: CSS selectors (update after inspecting the site)
- `headless`: Set to `true` to run browser in background
- `use_proxy`: Set to `true` and add `proxy_url` for IP rotation
- `run_interval_seconds`: Time between scraping runs (default: 300 = 5 minutes)

## Usage

### Single Run (for testing):
```
python demo_scraper.py once
```

### Continuous Mode:
```
python demo_scraper.py
```

Press `Ctrl+C` to stop.

## Output

All results saved in `data/` folder:

- `movies_YYYYMMDD_HHMMSS.json` - Scraped data in JSON format
- `movies_YYYYMMDD_HHMMSS.csv` - Scraped data in CSV format
- `log.txt` - Run history with timestamps and status

## Next Steps for Production

1. Inspect actual website and update CSS selectors in config.json
2. Add rotating proxy service for IP rotation
3. Handle pagination if needed
4. Add more robust error handling
5. Deploy to cloud server for 24/7 operation
6. Set up monitoring/alerts

## Notes

- First run will auto-download ChromeDriver
- Selectors in config.json are placeholders - inspect the target site and update them
- For production, connect a rotating proxy provider to avoid IP blocks
