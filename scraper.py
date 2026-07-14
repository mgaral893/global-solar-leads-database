#!/usr/bin/env python3
"""
Global Solar Leads Database Scraper (Resilient Enterprise Harvester v1)
=====================================================================
Multi-country engine supporting US, UK, Canada (CA), and Australia (AU).
Features:
- Country-specific normalizers, target locations, and output files.
- Resilient concurrent crawling with DuckDuckGo fallback query loops.
- Thread-safe real-time saving and incremental deduplication.
"""
import os
import csv
import re
import time
import urllib3
import logging
import requests
import html
import argparse
import threading
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Setup Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("global_leads_engine")

# Country specific target regions and file names
COUNTRY_DATA = {
    "US": {
        "csv": "us_solar_installers.csv",
        "locations": [
            "Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado", "Connecticut", "Delaware",
            "Florida", "Georgia", "Hawaii", "Idaho", "Illinois", "Indiana", "Iowa", "Kansas", "Kentucky",
            "Louisiana", "Maine", "Maryland", "Massachusetts", "Michigan", "Minnesota", "Mississippi", "Missouri",
            "Montana", "Nebraska", "Nevada", "New Hampshire", "New Jersey", "New Mexico", "New York", "North Carolina",
            "North Dakota", "Ohio", "Oklahoma", "Oregon", "Pennsylvania", "Rhode Island", "South Carolina", "South Dakota",
            "Tennessee", "Texas", "Utah", "Vermont", "Virginia", "Washington", "West Virginia", "Wisconsin", "Wyoming",
            "Los Angeles", "Houston", "Phoenix", "Philadelphia", "San Antonio", "San Diego", "Dallas", "San Jose", "Chicago"
        ]
    },
    "UK": {
        "csv": "uk_solar_installers.csv",
        "locations": [
            "London", "Manchester", "Birmingham", "Leeds", "Glasgow", "Edinburgh", "Liverpool", "Bristol", 
            "Sheffield", "Newcastle", "Leicester", "Coventry", "Belfast", "Cardiff", "Nottingham", "Southampton"
        ]
    },
    "CA": {
        "csv": "ca_solar_installers.csv",
        "locations": [
            "Ontario", "Quebec", "British Columbia", "Alberta", "Manitoba", "Saskatchewan", "Nova Scotia", 
            "Toronto", "Montreal", "Vancouver", "Calgary", "Ottawa", "Edmonton", "Winnipeg", "Quebec City"
        ]
    },
    "AU": {
        "csv": "au_solar_installers.csv",
        "locations": [
            "New South Wales", "Victoria", "Queensland", "Western Australia", "South Australia", "Tasmania", 
            "Sydney", "Melbourne", "Brisbane", "Perth", "Adelaide", "Hobart", "Canberra", "Gold Coast"
        ]
    }
}

# Defaults (overwritten dynamically via CLI arg)
OUTPUT_CSV = "us_solar_installers.csv"
LOCATIONS = COUNTRY_DATA["US"]["locations"]

MAX_WORKERS = 15
FILE_LOCK = threading.Lock()

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# Regex definitions
EMAIL_REGEX = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
PHONE_REGEX = re.compile(r"\+?\b[1-9]\d{1,14}\b|\b(?:\d{3}[-.\s]??\d{3}[-.\s]??\d{4}|\(\d{3}\)\s*\d{3}[-.\s]??\d{4})\b")

BLOCKED_DOMAINS = [
    "google.com", "duckduckgo.com", "facebook.com", "instagram.com", "linkedin.com",
    "twitter.com", "youtube.com", "wikipedia.org", "yelp.com", "tripadvisor.com",
    "angi.com", "homeadvisor.com", "yellowpages.com", "houzz.com", "groupon.com",
    "indeed.com", "monster.com", "glassdoor.com", "reddit.com", "pinterest.com",
    "solarreviews.com", "energysage.com", "solar-estimate.org", "energy.gov"
]

DUMMY_EMAILS = [
    "yourname@domain.com", "info@yourdomain.com", "email@example.com", "contact@domain.com",
    "test@test.com", "user@example.com", "admin@domain.com", "name@domain.com",
    "support@yourdomain.com", "hello@company.com"
]

def clean_company_name(name):
    """Clean company name of HTML characters, SEO tags and clutter."""
    if not name:
        return ""
    name = html.unescape(name)
    name = re.split(r"\||-|—|::", name)[0].strip()
    name = re.sub(r"<[^>]+>", "", name)
    name = name.strip("※ *•_#-()[]{}▷▶★✔")
    name = re.sub(r"\b202\d\b", "", name).strip()
    name = re.sub(r"^\d+\s*", "", name).strip()
    
    # Strip common directory prefixes
    for phrase in ["Best Solar Companies in", "Top Solar Installers in", "Best", "Top"]:
        if name.lower().startswith(phrase.lower()):
            name = name[len(phrase):].strip()
            
    name = " ".join([w.capitalize() for w in name.split()])
    return name

def clean_phone(phone, country_code="US"):
    """Normalize phone numbers based on country code formatting rules."""
    if not phone:
        return ""
    digits = "".join(re.findall(r"\d", phone))
    
    # Filter dummy phone structures
    if digits in ["9999999999", "1234567890", "0000000000", "999999999"]:
        return ""
        
    if country_code in ["US", "CA"]:
        if len(digits) == 10:
            return f"+1 ({digits[0:3]}) {digits[3:6]}-{digits[6:10]}"
        elif len(digits) == 11 and digits.startswith("1"):
            return f"+1 ({digits[1:4]}) {digits[4:7]}-{digits[7:11]}"
    elif country_code == "UK":
        if digits.startswith("44") and len(digits) > 10:
            return f"+44 {digits[2:6]} {digits[6:]}"
        elif digits.startswith("0") and len(digits) == 11:
            return f"+44 {digits[1:5]} {digits[5:]}"
    elif country_code == "AU":
        if digits.startswith("61") and len(digits) >= 11:
            return f"+61 {digits[2]} {digits[3:7]} {digits[7:]}"
        elif digits.startswith("0") and len(digits) == 10:
            return f"+61 {digits[1]} {digits[2:6]} {digits[6:]}"
            
    if len(phone.strip()) > 7:
        return phone.strip()
    return ""

def clean_address(address):
    """Cleans addresses and discards HTML/CSS/JavaScript artifacts."""
    if not address:
        return ""
        
    address = html.unescape(address)
    code_indicators = [
        "{", "}", "[", "]", "class=", "id=", "href=", "src=", "menu-item", 
        "span", "div", "script", "function", "var ", "const ", "let ", "//#", 
        "/*", "*/", "import ", "document.", "window.", "elementor", "wpa_field",
        "margin:", "padding:", "display:", "color:", "z-index"
    ]
    address_lower = address.lower()
    if any(ind in address_lower for ind in code_indicators):
        return ""
        
    address = re.sub(r"<[^>]+>", "", address)
    address = " ".join(address.split())
    address = address.strip(" ,.-:;()[]")
    address = " ".join([w.capitalize() for w in address.split()])
    return address

def is_valid_email(email):
    """Validates B2B email is not a dummy template."""
    if not email:
        return False
    email = email.lower().strip()
    if email in DUMMY_EMAILS:
        return False
    if any(email.startswith(dummy.split("@")[0]) for dummy in DUMMY_EMAILS if "@" in dummy):
        if "domain" in email or "example" in email:
            return False
    if any(email.endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".js", ".css"]):
        return False
    return "@" in email

def search_ddg_lite(query):
    """Query DuckDuckGo Lite and extract corporate sites."""
    url = "https://lite.duckduckgo.com/lite/"
    data = {"q": query}
    links = set()
    
    retries = 3
    delay = 6
    
    for attempt in range(retries):
        try:
            r = requests.post(url, data=data, headers=HEADERS, timeout=12)
            if r.status_code == 200:
                soup = BeautifulSoup(r.text, "html.parser")
                result_elements = soup.find_all("a", class_="result-link")
                if not result_elements:
                    time.sleep(delay)
                    delay *= 2
                    continue
                    
                for a in result_elements:
                    href = a["href"]
                    parsed = urlparse(href)
                    domain = parsed.netloc.lower()
                    if domain.startswith("www."):
                        domain = domain[4:]
                        
                    if domain and not any(b in domain for b in BLOCKED_DOMAINS):
                        links.add(f"{parsed.scheme}://{parsed.netloc}")
                if links:
                    break
            else:
                time.sleep(delay)
                delay *= 2
        except Exception:
            time.sleep(delay)
            delay *= 2
            
    return links

def extract_legal_name(text, country_code="US"):
    """Extracts corporate legal names based on country-specific legal suffixes."""
    # Suffixes for English Corporate Entities
    suffixes = r"\b([A-Z0-9\s,.-]{3,45}\s(?:LLC|Inc\.?|Corp\.?|Ltd\.?|Plc\.?|Pty\s+Ltd\.?|Group|Energy|Solar))\b"
    matches = re.findall(suffixes, text, re.IGNORECASE)
    
    if matches:
        cleaned = []
        for m in matches:
            c = m.strip().replace("\n", " ")
            c = re.sub(r"\s+", " ", c)
            if len(c) > 6 and not any(k in c.lower() for k in ["for llc", "to inc", "the llc"]):
                cleaned.append(c)
        if cleaned:
            return " ".join([w.capitalize() if not w.isupper() else w for w in cleaned[0].split()])
            
    label_match = re.search(r"(?:legal|registered)\s+name:?\s*([^\n.,;]{3,45})", text, re.IGNORECASE)
    if label_match:
        return label_match.group(1).strip()
    return ""

def extract_social_links(soup, base_url):
    """Finds LinkedIn and Facebook profile pages."""
    socials = {"linkedin": "", "facebook": ""}
    for a in soup.find_all("a", href=True):
        href = a["href"].lower()
        if "linkedin.com/company/" in href or "linkedin.com/in/" in href:
            socials["linkedin"] = a["href"]
        elif "facebook.com/" in href and not any(k in href for k in ["sharer", "share", "plugins"]):
            socials["facebook"] = a["href"]
    return socials

def crawl_company_site(base_url, location_name="", country_code="US"):
    """Crawls corporate site and extracts B2B contact info."""
    lead = {
        "name": "",
        "legal_name": "",
        "email": "",
        "phone": "",
        "website": base_url,
        "address": "",
        "location": location_name.capitalize(),
        "linkedin": "",
        "facebook": ""
    }
    
    try:
        r = requests.get(base_url, headers=HEADERS, verify=False, timeout=8)
        if r.status_code != 200:
            return None
            
        r.encoding = r.apparent_encoding or "utf-8"
        soup = BeautifulSoup(r.text, "html.parser")
        
        # Extrapolate company name
        title_tag = soup.find("title")
        if title_tag:
            lead["name"] = clean_company_name(title_tag.text)
            
        html_text = r.text
        
        # Social profiles
        socials = extract_social_links(soup, base_url)
        lead.update(socials)
        
        # Phone and Email
        emails = EMAIL_REGEX.findall(html_text)
        phones = PHONE_REGEX.findall(html_text)
        
        valid_emails = [e for e in set(emails) if is_valid_email(e)]
        if valid_emails:
            lead["email"] = valid_emails[0].lower().strip()
            
        if phones:
            lead["phone"] = clean_phone(phones[0], country_code)
            
        # Scan standard legal pages
        subpages = []
        for a in soup.find_all("a", href=True):
            href = a["href"].lower()
            text = a.text.lower()
            if any(k in href or k in text for k in ["contact", "about", "privacy", "legal", "terms", "policy"]):
                sub_url = urljoin(base_url, a["href"])
                subpages.append(sub_url)
                
        subpages = list(set(subpages))[:3]
        
        # Define country specific postal/zip regexes
        zip_regexes = {
            "US": re.compile(r"\b\d{5}(?:-\d{4})?\b"),
            "UK": re.compile(r"\b[A-Z]{1,2}\d[A-Z\d]?\s*\d[A-Z]{2}\b", re.IGNORECASE),
            "CA": re.compile(r"\b[A-Z]\d[A-Z]\s*\d[A-Z]\d\b", re.IGNORECASE),
            "AU": re.compile(r"\b\d{4}\b")
        }
        zip_regex = zip_regexes.get(country_code, zip_regexes["US"])
        
        for sub_url in subpages:
            try:
                sub_r = requests.get(sub_url, headers=HEADERS, verify=False, timeout=5)
                if sub_r.status_code == 200:
                    sub_r.encoding = sub_r.apparent_encoding or "utf-8"
                    sub_text = sub_r.text
                    
                    if not lead["email"]:
                        sub_emails = EMAIL_REGEX.findall(sub_text)
                        valid_sub_emails = [e for e in set(sub_emails) if is_valid_email(e)]
                        if valid_sub_emails:
                            lead["email"] = valid_sub_emails[0].lower().strip()
                            
                    if not lead["phone"]:
                        sub_phones = PHONE_REGEX.findall(sub_text)
                        if sub_phones:
                            lead["phone"] = clean_phone(sub_phones[0], country_code)
                            
                    if not lead["legal_name"]:
                        ln = extract_legal_name(sub_text, country_code)
                        if ln:
                            lead["legal_name"] = ln
                            
                    if not lead["address"]:
                        match_code = zip_regex.search(sub_text)
                        if match_code:
                            code_idx = sub_text.find(match_code.group(0))
                            start = max(0, code_idx - 65)
                            end = min(len(sub_text), code_idx + 65)
                            snippet = sub_text[start:end].replace("\n", " ").strip()
                            lead["address"] = clean_address(snippet)
            except Exception:
                pass
                
    except Exception:
        return None
        
    if not lead["name"]:
        parsed = urlparse(base_url)
        domain = parsed.netloc.lower().replace("www.", "").split(".")[0]
        lead["name"] = domain.capitalize()
        
    return lead

def load_existing_leads():
    """Loads existing leads from CSV to skip redundant crawls on restart."""
    seen_websites = set()
    seen_contacts = set()
    
    if os.path.exists(OUTPUT_CSV):
        try:
            with open(OUTPUT_CSV, mode="r", encoding="utf-8") as f:
                reader = csv.reader(f)
                header = next(reader, None)
                if header:
                    for row in reader:
                        if len(row) >= 6:
                            email = row[2].lower().strip()
                            phone = row[3].strip()
                            web = row[4].lower().strip()
                            
                            seen_websites.add(web)
                            if email:
                                seen_contacts.add(email)
                            if phone:
                                seen_contacts.add(phone)
            logger.info(f"Loaded {len(seen_websites)} existing lead websites from {OUTPUT_CSV}")
        except Exception as e:
            logger.warning(f"Could not parse existing CSV: {e}")
            
    return seen_websites, seen_contacts

def append_lead_to_csv(lead):
    """Appends a single lead row to the CSV file in a thread-safe manner."""
    with FILE_LOCK:
        file_exists = os.path.exists(OUTPUT_CSV)
        with open(OUTPUT_CSV, mode="a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow([
                    "Company", "Legal Name", "Email", "Phone", "Website", 
                    "Address", "Location", "LinkedIn", "Facebook"
                ])
            writer.writerow([
                lead["name"], lead["legal_name"], lead["email"], lead["phone"], lead["website"],
                lead["address"], lead["location"], lead["linkedin"], lead["facebook"]
            ])

def build_database(max_queries=20, country_code="US"):
    """Gathers global B2B leads from search engine and crawls them concurrently."""
    global OUTPUT_CSV, LOCATIONS
    
    OUTPUT_CSV = COUNTRY_DATA[country_code]["csv"]
    LOCATIONS = COUNTRY_DATA[country_code]["locations"]
    
    logger.info(f"Initializing Global B2B Leads Engine for {country_code}...")
    
    seen_websites, seen_contacts = load_existing_leads()
    all_domains = {}
    
    # 2. Gather domains by global locations
    queries_to_run = LOCATIONS[:max_queries]
    for idx, loc in enumerate(queries_to_run):
        # We loop through 2 targeted B2B query types per region
        for query_type in ["solar installers", "solar energy contractors"]:
            q = f"{query_type} {loc}"
            logger.info(f"[{idx+1}/{len(queries_to_run)}] Querying DuckDuckGo: {q!r}")
            found_urls = search_ddg_lite(q)
            for url in found_urls:
                parsed = urlparse(url)
                domain = parsed.netloc.lower()
                if domain.startswith("www."):
                    domain = domain[4:]
                
                clean_url = f"{parsed.scheme}://{parsed.netloc}"
                if clean_url.lower().strip() not in seen_websites and domain not in all_domains:
                    all_domains[domain] = (clean_url, loc)
            time.sleep(7.0) # Respectful delay to prevent rate limit blocks
        
    logger.info(f"Target NEW unique domains collected for {country_code}: {len(all_domains)}")
    if not all_domains:
        logger.info("No new domains to crawl. Database is up to date!")
        return
        
    # 3. Crawl domains concurrently
    logger.info(f"Launching parallel crawler with {MAX_WORKERS} workers...")
    new_leads_count = 0
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_url = {
            executor.submit(crawl_company_site, url, loc, country_code): url
            for domain, (url, loc) in all_domains.items()
        }
        
        for future in as_completed(future_to_url):
            url = future_to_url[future]
            try:
                lead = future.result()
                if lead and (is_valid_email(lead["email"]) or lead["phone"]):
                    lead["name"] = clean_company_name(lead["name"])
                    
                    if len(lead["name"]) > 2:
                        contact_key = lead["email"] if lead["email"] else lead["phone"]
                        
                        if contact_key not in seen_contacts:
                            seen_contacts.add(contact_key)
                            
                            # Append to CSV in real-time
                            append_lead_to_csv(lead)
                            new_leads_count += 1
                            logger.info(f"✅ Lead saved ({new_leads_count} new): {lead['name']} | Email: {lead['email']} | Tel: {lead['phone']}")
            except Exception as e:
                logger.error(f"Error crawling worker result for {url}: {e}")
                
    logger.info(f"🥇 CRAWL COMPLETE FOR {country_code}! Added {new_leads_count} new leads directly to {OUTPUT_CSV}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Global B2B Leads Harvester")
    parser.add_argument("--country", choices=["US", "UK", "CA", "AU"], default="US", help="Target country code")
    parser.add_argument("--max-queries", type=int, default=15, help="Number of locations to query")
    args = parser.parse_args()
    
    build_database(max_queries=args.max_queries, country_code=args.country.upper())
