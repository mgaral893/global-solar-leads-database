#!/home/ubuntu/agi-agent/venv/bin/python3
"""
Cron wrapper script to automate the country-specific B2B Solar Leads pipeline:
1. Crawl targeted regions for solar installer leads.
2. Synchronize the database with Google Drive and Gumroad.
3. Commit and push database updates to GitHub.
"""
import os
import sys
import logging
import argparse
import subprocess

# Ensure project path is in python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import scraper
from scraper import build_database
import gumroad_export

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("cron_pipeline")

def run_pipeline():
    parser = argparse.ArgumentParser(description="Automated Country Leads Pipeline")
    parser.add_argument("--country", choices=["US", "UK", "CA", "AU"], required=True, help="Target country code")
    parser.add_argument("--max-queries", type=int, default=100, help="Max query locations")
    args = parser.parse_args()
    
    cc = args.country.upper()
    logger.info(f"⚡ Starting scheduled Solar Leads Scraping & Gumroad Sync for country: {cc}...")
    
    # 1. Setup country-specific variables in scraper module
    if cc in scraper.COUNTRY_DATA:
        scraper.OUTPUT_CSV = scraper.COUNTRY_DATA[cc]["csv"]
        scraper.LOCATIONS = scraper.COUNTRY_DATA[cc]["locations"]
    else:
        logger.error(f"❌ Invalid country code: {cc}")
        sys.exit(1)
        
    # 2. Run scraper covering target locations
    try:
        build_database(max_queries=args.max_queries)
    except Exception as e:
        logger.error(f"❌ Error during lead scraping: {e}")
        sys.exit(1)
        
    # 3. Run Gumroad/Google Drive Sync for specific country
    try:
        gumroad_export.main(country_code=cc)
        logger.info(f"✅ Scheduled pipeline run for {cc} completed successfully.")
    except Exception as e:
        logger.error(f"❌ Error during Gumroad/Drive synchronization: {e}")
        sys.exit(2)

    # 4. Git push database updates inside main workspace
    try:
        logger.info(f"Syncing {cc} database changes with GitHub...")
        working_dir = os.path.dirname(os.path.abspath(__file__))
        # Add local files
        subprocess.run(["git", "add", "."], cwd=working_dir, check=True)
        subprocess.run(["git", "commit", "-m", f"chore: auto-sync leads database for {cc}"], cwd=working_dir, check=True)
        # Push from main workspace
        subprocess.run(["git", "push"], cwd=os.path.dirname(working_dir), check=True)
        logger.info(f"✅ Leads database for {cc} pushed to GitHub successfully.")
    except Exception as e:
        logger.warning(f"⚠️ Git push skipped/failed: {e}")

if __name__ == "__main__":
    run_pipeline()
