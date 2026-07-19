#!/usr/bin/env python3
import sys
import os
import requests

# Import components from existing export script
sys.path.append("/home/ubuntu/agi-agent/projects/global-solar-leads-database")
from gumroad_export import COUNTRY_PRODUCTS, load_config, get_gumroad_token

def main():
    token = get_gumroad_token()
    config = load_config()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    print("🔄 Syncing metadata on Gumroad for US, UK, CA, AU...")
    for country, pdata in COUNTRY_PRODUCTS.items():
        product_id = config.get(country, {}).get("product_id")
        if not product_id:
            print(f"⚠️ Skipping {country} - no product_id found in config.")
            continue
            
        print(f"📝 Updating {country} (ID: {product_id}) on Gumroad...")
        url = f"https://api.gumroad.com/v2/products/{product_id}"
        payload = {
            "name": pdata["name"],
            "price": int(pdata["price"]),
            "description": pdata["description"],
            "custom_summary": pdata["summary"],
            "tags": pdata["tags"]
        }
        
        try:
            r = requests.put(url, headers=headers, json=payload, timeout=15)
            if r.status_code == 200:
                print(f"✅ Successfully updated metadata for {country}!")
            else:
                print(f"❌ Failed to update {country}: {r.status_code} - {r.text}")
        except Exception as e:
            print(f"❌ Error updating {country}: {e}")

if __name__ == "__main__":
    main()
