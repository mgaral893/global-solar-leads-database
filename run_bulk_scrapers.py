#!/usr/bin/env python3
"""
Sequential coordinator script to run all country-specific scraping pipelines,
upload databases and covers to Google Drive, register on Gumroad, and push updates to GitHub.
"""
import subprocess
import os
import sys

venv_python = "/home/ubuntu/agi-agent/venv/bin/python3"
gumroad_token = "OhVCL5q_JLaB58owf57kMbsFhPo0Asm9nCRg4qe8C78"

# Prepare environment
env = os.environ.copy()
env["GUMROAD_TOKEN"] = gumroad_token

countries = ["US", "UK", "CA", "AU"]

print("⚡ Starting sequential Solar Leads Database Builder pipeline for US, UK, CA, AU...")
sys.stdout.flush()

for country in countries:
    print("\n" + "="*60)
    print(f"🚀 [1/2] RUNNING SCRAPER FOR: {country}")
    print("="*60)
    sys.stdout.flush()
    
    # Run Scraper with sequential queries to prevent DDG rate limit blocks
    # US uses 100 queries, UK 80, CA 80, AU 80 (since locations list is expanded to cover all major regions)
    max_queries = "100" if country == "US" else "80"
    cmd_scrape = [venv_python, "scraper.py", "--country", country, "--max-queries", max_queries]
    try:
        subprocess.run(cmd_scrape, check=True, env=env)
    except subprocess.CalledProcessError as e:
        print(f"❌ Scraper failed for {country} with exit code {e.returncode}")
        sys.stdout.flush()
        continue
        
    print("\n" + "="*60)
    print(f"📤 [2/2] RUNNING GUMROAD & DRIVE EXPORT FOR: {country}")
    print("="*60)
    sys.stdout.flush()
    
    # Run Exporter
    cmd_export = [venv_python, "gumroad_export.py", "--country", country]
    try:
        subprocess.run(cmd_export, check=True, env=env)
    except subprocess.CalledProcessError as e:
        print(f"❌ Export failed for {country} with exit code {e.returncode}")
        sys.stdout.flush()
        continue

# Consolidated Git Push
print("\n" + "="*60)
print("💾 COMMITTING AND PUSHING DATABASES TO GITHUB")
print("="*60)
sys.stdout.flush()
try:
    subprocess.run(["git", "add", "."], check=True)
    subprocess.run(["git", "commit", "-m", "feat: populate global solar databases with verified leads"], check=True)
    subprocess.run(["git", "push", "origin", "main"], check=True)
    print("✅ Successfully committed and pushed databases to GitHub!")
    sys.stdout.flush()
except Exception as e:
    print(f"⚠️ Git operations encountered an error: {e}")
    sys.stdout.flush()
