#!/usr/bin/env python3
"""
Cron wrapper script to automate the full Global Solar Leads pipeline:
1. Crawl target country regions for solar installer leads.
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

from scraper import build_database
import gumroad_export

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("global_cron_pipeline")

def run_pipeline():
    parser = argparse.ArgumentParser(description="Automated Country Leads Pipeline")
    parser.add_argument("--country", choices=["US", "UK", "CA", "AU"], required=True, help="Target country code")
    args = parser.parse_args()
    
    country = args.country.upper()
    logger.info(f"⚡ Starting scheduled Solar Leads Scraping and Gumroad Sync for {country}...")
    
    # 1. Run scraper covering first 40 locations (provinces, states and major cities)
    try:
        # Override argv for scraper import argparse
        sys.argv = [sys.argv[0], "--country", country, "--max-queries", "40"]
        build_database(max_queries=40)
    except Exception as e:
        logger.error(f"❌ Error during lead scraping for {country}: {e}")
        sys.exit(1)
        
    # 2. Run Gumroad/Google Drive Sync
    try:
        # Reset argv for gumroad_export import argparse
        sys.argv = [sys.argv[0], "--country", country]
        gumroad_export.main()
        logger.info(f"✅ Scheduled pipeline run completed successfully for {country}.")
    except Exception as e:
        logger.error(f"❌ Error during Gumroad/Drive synchronization for {country}: {e}")
        sys.exit(2)

    # 3. Git push database updates inside main workspace
    try:
        logger.info(f"Syncing {country} database changes with GitHub...")
        working_dir = os.path.dirname(os.path.abspath(__file__))
        # Add local files
        subprocess.run(["git", "add", "."], cwd=working_dir, check=True)
        subprocess.run(["git", "commit", "-m", f"chore: auto-sync {country} leads database updates"], cwd=working_dir, check=True)
        # Push from main workspace
        subprocess.run(["git", "push"], cwd=os.path.dirname(working_dir), check=True)
        logger.info(f"✅ {country} leads database pushed to GitHub successfully.")
    except Exception as e:
        logger.warning(f"⚠️ Git push skipped/failed for {country}: {e}")

if __name__ == "__main__":
    run_pipeline()
