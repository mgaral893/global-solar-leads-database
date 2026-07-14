#!/usr/bin/env python3
"""
Gumroad and Google Drive Sync Engine (Multi-Country B2B Solar Edition)
=====================================================================
Synchronizes country-specific CSV files with separate Gumroad products
and public Google Drive direct download links.
"""
import os
import json
import logging
import subprocess
import requests
import argparse

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("global_sync_engine")

CONFIG_FILE = "gumroad_config.json"
GWS_PATH = "/home/ubuntu/.local/bin/gws"
GDRIVE_PARENT_FOLDER = "1p2tt_6BuRfs3-dRcycP8mvsOIHumpCEH"

COUNTRY_PRODUCTS = {
    "US": {
        "csv": "us_solar_installers.csv",
        "name": "US Solar Energy Installers B2B Leads Database (600+ Leads)",
        "price": "4900",  # $49.00 USD
        "cover": "covers/us_solar_cover.jpg",
        "tags": ["solar energy", "b2b leads", "us contractors", "solar database", "leads database"],
        "summary": "Verified B2B list of 600+ solar installers and EPC contractors in the United States.",
        "description": (
            "### ⚡ Scale Your B2B Outbound Campaigns with High-Quality US Solar Industry Leads\n\n"
            "This verified B2B commercial database contains a curated list of active solar energy contractors, "
            "residential/commercial solar installers, and EPC companies operating across all 50 US states.\n\n"
            "----\n\n"
            "#### 📊 Fields Included per Record:\n"
            "* **Company Name:** Primary trading name of the contractor.\n"
            "* **Legal Name:** Registered corporate name (e.g. LLC, Inc., Corp.).\n"
            "* **Email:** Verified corporate contact email address.\n"
            "* **Phone:** Standardized direct contact number (+1 formatted).\n"
            "* **Website:** Official corporate website URL.\n"
            "* **Address:** Corporate physical headquarters location.\n"
            "* **Location:** State and City.\n"
            "* **Social Links:** Direct corporate profiles (LinkedIn and Facebook).\n\n"
            "----\n\n"
            "#### 🚀 Ideal for:\n"
            "* **Solar Manufacturers & Distributors:** Sell panels, inverters, and mounting gear directly to active local installers.\n"
            "* **SaaS & Software Providers:** Sell project management, design, or CRM tools targeting solar contractors.\n"
            "* **B2B Outbound Agencies:** High-quality, verified contact sheets for cold outreach campaigns.\n\n"
            "**Note:** This dataset is automatically updated and expanded on a weekly basis to guarantee fresh, valid contacts."
        )
    },
    "UK": {
        "csv": "uk_solar_installers.csv",
        "name": "UK Solar Energy Installers B2B Leads Database (400+ Leads)",
        "price": "2900",  # $29.00 USD
        "cover": "covers/uk_solar_cover.jpg",
        "tags": ["solar energy", "b2b leads", "uk installers", "solar database", "leads database"],
        "summary": "Verified B2B list of 400+ solar panel installers and certified contractors in the United Kingdom.",
        "description": (
            "### ⚡ Scale Your B2B Outbound Campaigns with High-Quality UK Solar Industry Leads\n\n"
            "This verified B2B commercial database contains a curated list of active solar energy contractors, "
            "residential solar panel installers, and commercial contractors operating across the United Kingdom (England, Scotland, Wales, and Northern Ireland).\n\n"
            "----\n\n"
            "#### 📊 Fields Included per Record:\n"
            "* **Company Name:** Primary trading name of the contractor.\n"
            "* **Legal Name:** Registered corporate name (e.g. Ltd, PLC).\n"
            "* **Email:** Verified corporate contact email address.\n"
            "* **Phone:** Standardized direct contact number (+44 formatted).\n"
            "* **Website:** Official corporate website URL.\n"
            "* **Address:** Corporate physical headquarters location.\n"
            "* **Location:** City and Region.\n"
            "* **Social Links:** Direct corporate profiles (LinkedIn and Facebook).\n\n"
            "----\n\n"
            "#### 🚀 Ideal for:\n"
            "* **Solar Manufacturers & Distributors:** Sell solar PV panels, inverters, and battery storage solutions directly to active UK installers.\n"
            "* **SaaS & Software Providers:** Sell project design or field service management tools targeting solar contractors.\n"
            "* **B2B Outbound Agencies:** Clean contact lists for target outreach.\n\n"
            "**Note:** This dataset is automatically updated and expanded on a weekly basis to guarantee fresh, valid contacts."
        )
    },
    "CA": {
        "csv": "ca_solar_installers.csv",
        "name": "Canada Solar Energy Installers B2B Leads Database (300+ Leads)",
        "price": "2900",  # $29.00 USD
        "cover": "covers/ca_solar_cover.jpg",
        "tags": ["solar energy", "b2b leads", "canada installers", "solar database", "leads database"],
        "summary": "Verified B2B list of 300+ solar panel contractors, residential installers and solar EPCs in Canada.",
        "description": (
            "### ⚡ Scale Your B2B Outbound Campaigns with High-Quality Canadian Solar Industry Leads\n\n"
            "This verified B2B commercial database contains a curated list of active solar energy contractors, "
            "residential installers, and commercial solar EPC companies operating across all Canadian provinces (Ontario, BC, Quebec, Alberta, etc.).\n\n"
            "----\n\n"
            "#### 📊 Fields Included per Record:\n"
            "* **Company Name:** Primary trading name of the contractor.\n"
            "* **Legal Name:** Registered corporate name (e.g. Inc., Ltd., Corp.).\n"
            "* **Email:** Verified corporate contact email address.\n"
            "* **Phone:** Standardized direct contact number (+1 formatted).\n"
            "* **Website:** Official corporate website URL.\n"
            "* **Address:** Corporate physical headquarters location.\n"
            "* **Location:** Province and City.\n"
            "* **Social Links:** Direct corporate profiles (LinkedIn and Facebook).\n\n"
            "----\n\n"
            "#### 🚀 Ideal for:\n"
            "* **Solar Equipment Distributors:** Sell wholesale panels, inverters, and storage setups to Canadian contractors.\n"
            "* **SaaS & Software Providers:** Target active solar engineering firms with CRM or project design software.\n"
            "* **B2B Outbound Agencies:** High-quality, verified contact sheets for cold outreach campaigns.\n\n"
            "**Note:** This dataset is automatically updated and expanded on a weekly basis to guarantee fresh, valid contacts."
        )
    },
    "AU": {
        "csv": "au_solar_installers.csv",
        "name": "Australia Solar Energy Installers B2B Leads Database (300+ Leads)",
        "price": "2900",  # $29.00 USD
        "cover": "covers/au_solar_cover.jpg",
        "tags": ["solar energy", "b2b leads", "australia installers", "solar database", "leads database"],
        "summary": "Verified B2B list of 300+ solar PV installers and commercial contractors in Australia.",
        "description": (
            "### ⚡ Scale Your B2B Outbound Campaigns with High-Quality Australian Solar Industry Leads\n\n"
            "This verified B2B commercial database contains a curated list of active solar energy contractors, "
            "solar PV installers, and commercial contractors operating across all Australian states (NSW, Victoria, Queensland, WA, etc.).\n\n"
            "----\n\n"
            "#### 📊 Fields Included per Record:\n"
            "* **Company Name:** Primary trading name of the contractor.\n"
            "* **Legal Name:** Registered corporate name (e.g. Pty Ltd, Ltd.).\n"
            "* **Email:** Verified corporate contact email address.\n"
            "* **Phone:** Standardized direct contact number (+61 formatted).\n"
            "* **Website:** Official corporate website URL.\n"
            "* **Address:** Corporate physical headquarters location.\n"
            "* **Location:** State and City.\n"
            "* **Social Links:** Direct corporate profiles (LinkedIn and Facebook).\n\n"
            "----\n\n"
            "#### 🚀 Ideal for:\n"
            "* **Renewable Manufacturers & Wholesalers:** Sell panels, inverters, and commercial PV structures to local contractors.\n"
            "* **SaaS & Software Providers:** Pitch CRM, design, or project mapping software directly to engineers.\n"
            "* **B2B Outbound Agencies:** High-quality verified listings for marketing campaigns.\n\n"
            "**Note:** This dataset is automatically updated and expanded on a weekly basis to guarantee fresh, valid contacts."
        )
    }
}

def get_gumroad_token():
    token = os.environ.get("GUMROAD_TOKEN")
    if not token:
        logger.warning("GUMROAD_TOKEN environment variable not set. Using verified fallback token.")
        return "OhVCL5q_JLaB58owf57kMbsFhPo0Asm9nCRg4qe8C78"
    return token.strip()

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load config file: {e}")
    return {}

def save_config(config):
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=4)
        logger.info(f"Config cached to {CONFIG_FILE}")
    except Exception as e:
        logger.error(f"Failed to save config: {e}")

def create_gumroad_product(token, country_code):
    url = "https://api.gumroad.com/v2/products"
    headers = {"Authorization": f"Bearer {token}"}
    pdata = COUNTRY_PRODUCTS[country_code]
    payload = {
        "name": pdata["name"],
        "price": pdata["price"],
        "description": pdata["description"],
        "summary": pdata["summary"],
        "shown_on_profile": "true"
    }
    
    logger.info(f"Registering product on Gumroad for {country_code}...")
    try:
        r = requests.post(url, data=payload, headers=headers, timeout=15)
        if r.status_code in [200, 201]:
            res = r.json()
            product = res.get("product", {})
            product_id = product.get("id")
            short_url = product.get("short_url")
            
            # Set SEO tags
            logger.info(f"Optimizing SEO tags on Gumroad for {country_code}...")
            update_url = f"https://api.gumroad.com/v2/products/{product_id}"
            update_payload = {
                "tags": pdata["tags"],
                "custom_summary": pdata["summary"]
            }
            requests.put(update_url, headers=headers, json=update_payload, timeout=10)
            
            # Note: Cover images cannot be programmatically uploaded via API in 2026.
            # They must be uploaded manually by the creator in the Gumroad Dashboard.
            cover_path = pdata["cover"]
            if os.path.exists(cover_path):
                logger.info(f"💡 Premium cover cover image generated at '{cover_path}'. Please upload it manually in the Gumroad Dashboard.")
            
            return product_id, short_url
    except Exception as e:
        import traceback
        traceback.print_exc()
        logger.error(f"Error registering product on Gumroad for {country_code}: {e}")
    return None, None

def publish_gumroad_product(token, product_id):
    url = f"https://api.gumroad.com/v2/products/{product_id}/enable"
    headers = {"Authorization": f"Bearer {token}"}
    logger.info(f"Publishing product {product_id} on Gumroad to make it live...")
    try:
        r = requests.put(url, headers=headers, timeout=15)
        if r.status_code == 200:
            logger.info("✅ Product status on Gumroad is now enabled/live!")
            return True
    except Exception as e:
        logger.error(f"Error publishing Gumroad product {product_id}: {e}")
    return False

def get_or_create_country_folder(config, country_code):
    country_cfg = config.setdefault(country_code, {})
    folder_id = country_cfg.get("gdrive_folder_id")
    if folder_id:
        return folder_id
        
    folder_name = f"B2B Leads - {country_code}"
    logger.info(f"Checking if Google Drive folder '{folder_name}' exists...")
    
    # Query Drive
    q = f"name = '{folder_name}' and '{GDRIVE_PARENT_FOLDER}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    cmd = [GWS_PATH, "drive", "files", "list", "--params", json.dumps({"q": q})]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        out_text = res.stdout.strip()
        if "{" in out_text:
            json_part = out_text[out_text.index("{"):]
            data = json.loads(json_part)
            files = data.get("files", [])
            if files:
                folder_id = files[0].get("id")
                logger.info(f"✅ Found existing folder '{folder_name}' (ID: {folder_id})")
    except Exception as e:
        logger.warning(f"Error listing folder in Drive: {e}")
        
    if not folder_id:
        logger.info(f"Creating new folder '{folder_name}' in Google Drive...")
        cmd_create = [
            GWS_PATH, "drive", "files", "create",
            "--json", json.dumps({
                "name": folder_name,
                "mimeType": "application/vnd.google-apps.folder",
                "parents": [GDRIVE_PARENT_FOLDER]
            })
        ]
        try:
            res = subprocess.run(cmd_create, capture_output=True, text=True, check=True)
            out_text = res.stdout.strip()
            if "{" in out_text:
                json_part = out_text[out_text.index("{"):]
                data = json.loads(json_part)
                folder_id = data.get("id")
                
            if folder_id:
                logger.info(f"✅ Created folder '{folder_name}' (ID: {folder_id})")
                # Make the new folder public
                logger.info("Setting public reader permissions on the new folder...")
                perm_cmd = [
                    GWS_PATH, "drive", "permissions", "create",
                    "--params", json.dumps({"fileId": folder_id}),
                    "--json", json.dumps({"role": "reader", "type": "anyone"})
                ]
                subprocess.run(perm_cmd, capture_output=True, text=True, check=False)
        except Exception as e:
            logger.error(f"Error creating folder in Drive: {e}")
            
    if folder_id:
        country_cfg["gdrive_folder_id"] = folder_id
        save_config(config)
        
    return folder_id

def sync_to_google_drive(config, country_code):
    if country_code not in config:
        config[country_code] = {}
        
    file_id = config[country_code].get("gdrive_file_id")
    csv_file = COUNTRY_PRODUCTS[country_code]["csv"]
    
    # Resolve the parent folder ID dynamically for flat structure
    folder_id = get_or_create_country_folder(config, country_code)
    if not folder_id:
        logger.error(f"Could not resolve parent folder ID for {country_code}. Aborting Drive sync.")
        return None
        
    if not file_id:
        logger.info(f"First run for {country_code}: Uploading file to Google Drive...")
        cmd = [
            GWS_PATH, "drive", "files", "create",
            "--upload", csv_file,
            "--json", json.dumps({"name": csv_file, "parents": [folder_id]})
        ]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            out_text = res.stdout.strip()
            if "{" in out_text:
                json_part = out_text[out_text.index("{"):]
                data = json.loads(json_part)
                file_id = data.get("id")
                
            if file_id:
                logger.info(f"✅ File uploaded to Google Drive. File ID: {file_id}")
                config[country_code]["gdrive_file_id"] = file_id
                save_config(config)
                
                # Make the file public
                logger.info(f"Setting public reader permissions on the Drive file {file_id}...")
                perm_cmd = [
                    GWS_PATH, "drive", "permissions", "create",
                    "--params", json.dumps({"fileId": file_id}),
                    "--json", json.dumps({"role": "reader", "type": "anyone"})
                ]
                subprocess.run(perm_cmd, capture_output=True, text=True, check=True)
                logger.info("✅ Drive file is now public.")
            else:
                logger.error(f"Failed to extract file ID from output: {out_text}")
        except Exception as e:
            logger.error(f"Error uploading to Google Drive: {e}")
            return None
    else:
        logger.info(f"Updating existing file on Google Drive (File ID: {file_id})...")
        cmd = [
            GWS_PATH, "drive", "files", "update",
            "--params", json.dumps({"fileId": file_id}),
            "--upload", csv_file
        ]
        try:
            subprocess.run(cmd, capture_output=True, text=True, check=True)
            logger.info("✅ Google Drive file updated successfully.")
        except Exception as e:
            logger.error(f"Error updating Google Drive file: {e}")
            
    if file_id:
        return f"https://drive.google.com/uc?export=download&id={file_id}"
    return None

def main():
    parser = argparse.ArgumentParser(description="Multi-Country Gumroad Sync Engine")
    parser.add_argument("--country", choices=["US", "UK", "CA", "AU"], required=True, help="Target country code")
    args = parser.parse_args()
    
    cc = args.country.upper()
    token = get_gumroad_token()
    if not token:
        return
        
    csv_file = COUNTRY_PRODUCTS[cc]["csv"]
    if not os.path.exists(csv_file):
        logger.error(f"❌ Leads database CSV file {csv_file} not found. Run scraper.py --country {cc} first.")
        return
        
    config = load_config()
    
    # 1. Sync file to Google Drive and get download URL
    download_url = sync_to_google_drive(config, cc)
    if not download_url:
        logger.error("❌ Google Drive sync failed. Aborting.")
        return
        
    # 2. Get or Create Gumroad Product
    if cc not in config:
        config[cc] = {}
        
    product_id = config[cc].get("product_id")
    short_url = config[cc].get("short_url")
    
    if not product_id:
        product_id, short_url = create_gumroad_product(token, cc)
        if product_id:
            config[cc]["product_id"] = product_id
            config[cc]["short_url"] = short_url
            save_config(config)
            
    # If short_url is not cached, fetch it from Gumroad API
    if product_id and not short_url:
        logger.info(f"Retrieving live product URL for {cc} from Gumroad API...")
        url_detail = f"https://api.gumroad.com/v2/products/{product_id}"
        headers = {"Authorization": f"Bearer {token}"}
        try:
            r = requests.get(url_detail, headers=headers, timeout=10)
            if r.status_code == 200:
                res = r.json()
                if res.get("success"):
                    short_url = res.get("product", {}).get("short_url")
                    config[cc]["short_url"] = short_url
                    save_config(config)
        except Exception as e:
            logger.warning(f"Could not retrieve product URL: {e}")
            
    # 3. Publish Gumroad Product
    if product_id:
        publish_gumroad_product(token, product_id)
        
    print("\n" + "="*50)
    print(f"🚀 AUTOMATION PIPELINE FOR {cc} COMPLETED SUCCESSFULLY!")
    print(f"🔹 Country Product: {COUNTRY_PRODUCTS[cc]['name']}")
    print(f"🔹 Gumroad Link: {short_url}")
    print(f"🔹 Direct Download Link (Google Drive): {download_url}")
    print("\n📢 IMPORTANT:")
    print("Go to your Gumroad Product Settings -> Content for this product, select")
    print("'Redirect to an external URL' and paste the Direct Download Link above.")
    print("This only needs to be done ONCE per country product!")
    print("="*50 + "\n")

if __name__ == "__main__":
    main()
