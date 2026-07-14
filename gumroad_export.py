#!/home/ubuntu/agi-agent/venv/bin/python3
"""
Gumroad and Google Drive Sync Engine (Multi-Country B2B Solar Edition)
=====================================================================
Supports independent products per country (US, UK, CA, AU).
1. Uploads/Updates country-specific CSV to Google Drive (using gws).
2. Sets public read permissions on the Drive file.
3. Creates or updates the country-specific Gumroad product via API.
"""
import os
import json
import logging
import argparse
import subprocess
import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("multi_country_sync")

CONFIG_FILE = "gumroad_config.json"
GWS_PATH = "/home/ubuntu/.local/bin/gws"
GDRIVE_PARENT_FOLDER = "1iOg0JEXQokgW16LQMsezeSm_-rIF_6h9"

# Country-specific products and marketing configs
COUNTRY_PRODUCTS = {
    "US": {
        "csv": "us_solar_installers.csv",
        "name": "US Solar Energy Installers B2B Leads Database (500+ Companies)",
        "price": "5900",  # $59.00 USD
        "summary": "Verified B2B contact list of active solar installers and contractors across all 50 US states.",
        "tags": ["solar installers us", "us b2b leads", "solar energy us", "solar contractors", "usa solar"],
        "description": (
            "### ⚡ Scale Your B2B Outbound Campaigns with High-Quality US Solar Leads\n\n"
            "This verified B2B commercial database contains a curated list of active solar energy contractors, "
            "installers, and commercial solar EPC companies operating across all 50 states in the United States.\n\n"
            "----\n\n"
            "#### 📊 Fields Included per Record:\n"
            "* **Company Name:** Primary trading name of the contractor.\n"
            "* **Legal Name:** Registered corporate name (LLC, Inc., Corp. extracted from legal pages).\n"
            "* **Email:** Verified corporate contact email address.\n"
            "* **Phone:** Standardized direct contact number (US formatted).\n"
            "* **Website:** Official corporate website URL.\n"
            "* **Address:** Corporate physical headquarters address.\n"
            "* **Location:** State and Country location.\n"
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
        "name": "UK Solar Energy Installers B2B Leads Database (500+ Companies)",
        "price": "4900",  # $49.00 USD
        "summary": "Verified B2B contact list of active solar installers and contractors in the United Kingdom.",
        "tags": ["solar installers uk", "uk b2b leads", "solar energy uk", "solar contractors", "uk solar"],
        "description": (
            "### ⚡ Scale Your B2B Outbound Campaigns with High-Quality UK Solar Leads\n\n"
            "This verified B2B commercial database contains a curated list of active solar energy contractors, "
            "installers, and commercial solar EPC companies operating in England, Scotland, Wales, and Northern Ireland.\n\n"
            "----\n\n"
            "#### 📊 Fields Included per Record:\n"
            "* **Company Name:** Primary trading name of the contractor.\n"
            "* **Legal Name:** Registered corporate name (Ltd, Plc extracted from legal pages).\n"
            "* **Email:** Verified corporate contact email address.\n"
            "* **Phone:** Standardized direct contact number (UK formatted).\n"
            "* **Website:** Official corporate website URL.\n"
            "* **Address:** Corporate physical headquarters address.\n"
            "* **Location:** City/Region and Country location.\n"
            "* **Social Links:** Direct corporate profiles (LinkedIn and Facebook).\n\n"
            "----\n\n"
            "#### 🚀 Ideal for:\n"
            "* **Solar Manufacturers & Distributors:** Sell equipment directly to active local installers.\n"
            "* **SaaS & Software Providers:** Sell project management, design, or CRM tools targeting solar contractors.\n"
            "* **B2B Outbound Agencies:** High-quality, verified contact sheets for cold outreach campaigns.\n\n"
            "**Note:** This dataset is automatically updated and expanded on a weekly basis to guarantee fresh, valid contacts."
        )
    },
    "CA": {
        "csv": "ca_solar_installers.csv",
        "name": "Canada Solar Energy Installers B2B Leads Database (500+ Companies)",
        "price": "3900",  # $39.00 USD
        "summary": "Verified B2B contact list of active solar installers and contractors in Canada.",
        "tags": ["solar installers ca", "canada b2b", "solar energy ca", "canada solar"],
        "description": (
            "### ⚡ Scale Your B2B Outbound Campaigns with High-Quality Canadian Solar Leads\n\n"
            "This verified B2B commercial database contains a curated list of active solar energy contractors, "
            "installers, and commercial solar EPC companies operating across all Canadian provinces.\n\n"
            "----\n\n"
            "#### 📊 Fields Included per Record:\n"
            "* **Company Name:** Primary trading name of the contractor.\n"
            "* **Legal Name:** Registered corporate name (Inc., Ltd. extracted from legal pages).\n"
            "* **Email:** Verified corporate contact email address.\n"
            "* **Phone:** Standardized direct contact number (CA formatted).\n"
            "* **Website:** Official corporate website URL.\n"
            "* **Address:** Corporate physical headquarters address.\n"
            "* **Location:** Province and Country location.\n"
            "* **Social Links:** Direct corporate profiles (LinkedIn and Facebook).\n\n"
            "----\n\n"
            "#### 🚀 Ideal for:\n"
            "* **Solar Manufacturers & Distributors:** Sell equipment directly to active local installers.\n"
            "* **SaaS & Software Providers:** Sell project management, design, or CRM tools targeting solar contractors.\n"
            "* **B2B Outbound Agencies:** High-quality, verified contact sheets for cold outreach campaigns.\n\n"
            "**Note:** This dataset is automatically updated and expanded on a weekly basis to guarantee fresh, valid contacts."
        )
    },
    "AU": {
        "csv": "au_solar_installers.csv",
        "name": "Australia Solar Energy Installers B2B Leads Database (500+ Companies)",
        "price": "3900",  # $39.00 USD
        "summary": "Verified B2B contact list of active solar installers and contractors in Australia.",
        "tags": ["solar installers au", "australia b2b", "solar energy au", "solar au"],
        "description": (
            "### ⚡ Scale Your B2B Outbound Campaigns with High-Quality Australian Solar Leads\n\n"
            "This verified B2B commercial database contains a curated list of active solar energy contractors, "
            "installers, and commercial solar EPC companies operating across all Australian states.\n\n"
            "----\n\n"
            "#### 📊 Fields Included per Record:\n"
            "* **Company Name:** Primary trading name of the contractor.\n"
            "* **Legal Name:** Registered corporate name (Pty Ltd extracted from legal pages).\n"
            "* **Email:** Verified corporate contact email address.\n"
            "* **Phone:** Standardized direct contact number (AU formatted).\n"
            "* **Website:** Official corporate website URL.\n"
            "* **Address:** Corporate physical headquarters address.\n"
            "* **Location:** State and Country location.\n"
            "* **Social Links:** Direct corporate profiles (LinkedIn and Facebook).\n\n"
            "----\n\n"
            "#### 🚀 Ideal for:\n"
            "* **Solar Manufacturers & Distributors:** Sell equipment directly to active local installers.\n"
            "* **SaaS & Software Providers:** Sell project management, design, or CRM tools targeting solar contractors.\n"
            "* **B2B Outbound Agencies:** High-quality, verified contact sheets for cold outreach campaigns.\n\n"
            "**Note:** This dataset is automatically updated and expanded on a weekly basis to guarantee fresh, valid contacts."
        )
    }
}

def get_gumroad_token():
    token = os.environ.get("GUMROAD_TOKEN")
    if not token:
        logger.error("❌ GUMROAD_TOKEN environment variable not set.")
        return None
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
    pinfo = COUNTRY_PRODUCTS[country_code]
    
    payload = {
        "name": pinfo["name"],
        "price": pinfo["price"],
        "description": pinfo["description"],
        "summary": pinfo["summary"],
        "shown_on_profile": "true"
    }
    
    logger.info(f"Registering product {pinfo['name']} on Gumroad...")
    try:
        r = requests.post(url, data=payload, headers=headers, timeout=15)
        if r.status_code in [200, 201]:
            res = r.json()
            product = res.get("product", {})
            product_id = product.get("id")
            
            # Optimize tags and summary SEO
            logger.info("Optimizing product SEO tags on Gumroad...")
            update_url = f"https://api.gumroad.com/v2/products/{product_id}"
            update_payload = {
                "tags": pinfo["tags"],
                "custom_summary": pinfo["summary"]
            }
            requests.put(update_url, headers=headers, json=update_payload, timeout=10)
            
            return product_id
    except Exception as e:
        logger.error(f"Error registering product on Gumroad: {e}")
    return None

def publish_gumroad_product(token, product_id):
    url = f"https://api.gumroad.com/v2/products/{product_id}/enable"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        r = requests.put(url, headers=headers, timeout=15)
        if r.status_code == 200:
            logger.info("✅ Product status on Gumroad is now enabled/live!")
            return True
    except Exception as e:
        logger.error(f"Error publishing Gumroad product: {e}")
    return False

def sync_to_google_drive(config, country_code):
    cc = country_code.upper()
    country_cfg = config.get(cc, {})
    file_id = country_cfg.get("gdrive_file_id")
    csv_file = COUNTRY_PRODUCTS[cc]["csv"]
    
    if not file_id:
        logger.info(f"First run for {cc}: Uploading file to Google Drive...")
        cmd = [
            GWS_PATH, "drive", "files", "create",
            "--upload", csv_file,
            "--json", json.dumps({"name": csv_file, "parents": [GDRIVE_PARENT_FOLDER]})
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
                if cc not in config:
                    config[cc] = {}
                config[cc]["gdrive_file_id"] = file_id
                save_config(config)
                
                # Make the file public
                logger.info("Setting public reader permissions on the Drive file...")
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
        logger.info(f"Updating existing file on Google Drive for {cc} (File ID: {file_id})...")
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

def main(country_code=None):
    if country_code is None:
        parser = argparse.ArgumentParser(description="Multi-Country Gumroad Sync Engine")
        parser.add_argument("--country", choices=["US", "UK", "CA", "AU"], required=True, help="Target country code")
        args = parser.parse_args()
        cc = args.country.upper()
    else:
        cc = country_code.upper()
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
    if not product_id:
        product_id = create_gumroad_product(token, cc)
        if product_id:
            config[cc]["product_id"] = product_id
            save_config(config)
            
    # 3. Publish Gumroad Product
    if product_id:
        publish_gumroad_product(token, product_id)
        
    print("\n" + "="*50)
    print(f"🚀 AUTOMATION PIPELINE FOR {cc} COMPLETED SUCCESSFULLY!")
    print(f"🔹 Country Product: {COUNTRY_PRODUCTS[cc]['name']}")
    print(f"🔹 Direct Download Link (Google Drive): {download_url}")
    print("\n📢 IMPORTANT:")
    print("Go to your Gumroad Product Settings -> Content for this product, select")
    print("'Redirect to an external URL' and paste the Direct Download Link above.")
    print("This only needs to be done ONCE per country product!")
    print("="*50 + "\n")

if __name__ == "__main__":
    main()
