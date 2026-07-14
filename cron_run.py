#!/usr/bin/env python3
"""
Cron wrapper script to automate the full Global Solar Leads pipeline:
1. Crawl US, UK, CA, AU regions for solar installer leads.
2. Synchronize the database with Google Drive and Gumroad.
3. Commit and push database updates to GitHub.
"""
import os
import sys
import logging
import subprocess

# Ensure project path is in python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scraper import build_database
import gumroad_export

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("global_cron_pipeline")

def run_pipeline():
    logger.info("⚡ Starting scheduled Global Solar Leads Scraping and Gumroad Sync...")
    
    # 1. Run scraper covering first 40 locations (provinces, states and major cities)
    try:
        build_database(max_queries=40)
    except Exception as e:
        logger.error(f"❌ Error during global lead scraping: {e}")
        sys.exit(1)
        
    # 2. Run Gumroad/Google Drive Sync
    try:
        gumroad_export.main()
        logger.info("✅ Scheduled global pipeline run completed successfully.")
    except Exception as e:
        logger.error(f"❌ Error during Gumroad/Drive synchronization: {e}")
        sys.exit(2)

    # 3. Git push database updates inside main workspace
    try:
        logger.info("Syncing global database changes with GitHub...")
        working_dir = os.path.dirname(os.path.abspath(__file__))
        # Add local files
        subprocess.run(["git", "add", "."], cwd=working_dir, check=True)
        subprocess.run(["git", "commit", "-m", "chore: auto-sync global leads database updates"], cwd=working_dir, check=True)
        # Push from main workspace
        subprocess.run(["git", "push"], cwd=os.path.dirname(working_dir), check=True)
        logger.info("✅ Global leads database pushed to GitHub successfully.")
    except Exception as e:
        logger.warning(f"⚠️ Git push skipped/failed: {e}")

if __name__ == "__main__":
    run_pipeline()
