import csv
import os
import re
from urllib.parse import urlparse

files = {
    "US": {
        "path": "/home/ubuntu/agi-agent/projects/global-solar-leads-database/us_solar_installers.csv",
        "mapping": {
            "Company": "Company",
            "Email": "Email",
            "Phone": "Phone",
            "Website": "Website",
            "Address": "Address",
            "Location": "Location",
            "LinkedIn": "LinkedIn",
            "Facebook": "Facebook"
        }
    },
    "UK": {
        "path": "/home/ubuntu/agi-agent/projects/global-solar-leads-database/uk_solar_installers.csv",
        "mapping": {
            "Company": "Company",
            "Email": "Email",
            "Phone": "Phone",
            "Website": "Website",
            "Address": "Address",
            "Location": "Location",
            "LinkedIn": "LinkedIn",
            "Facebook": "Facebook"
        }
    },
    "CA": {
        "path": "/home/ubuntu/agi-agent/projects/global-solar-leads-database/ca_solar_installers.csv",
        "mapping": {
            "Company": "Company",
            "Email": "Email",
            "Phone": "Phone",
            "Website": "Website",
            "Address": "Address",
            "Location": "Location",
            "LinkedIn": "LinkedIn",
            "Facebook": "Facebook"
        }
    },
    "AU": {
        "path": "/home/ubuntu/agi-agent/projects/global-solar-leads-database/au_solar_installers.csv",
        "mapping": {
            "Company": "Company",
            "Email": "Email",
            "Phone": "Phone",
            "Website": "Website",
            "Address": "Address",
            "Location": "Location",
            "LinkedIn": "LinkedIn",
            "Facebook": "Facebook"
        }
    },
    "Spain": {
        "path": "/home/ubuntu/agi-agent/projects/spain-solar-leads-database/instaladores_solares_espana.csv",
        "mapping": {
            "Company": "Empresa",
            "Email": "Email",
            "Phone": "Teléfono",
            "Website": "Sitio Web",
            "Address": "Dirección",
            "Location": "Provincia",
            "LinkedIn": "LinkedIn",
            "Facebook": "Facebook"
        }
    }
}

def clean_domain(url):
    if not url:
        return ""
    url = url.strip().lower()
    # Remove protocol
    url = re.sub(r'^https?://', '', url)
    # Remove www.
    url = re.sub(r'^www\.', '', url)
    # Strip paths / query params
    url = url.split('/')[0]
    return url

def is_dummy_email(email):
    if not email:
        return False
    email = email.strip().lower()
    placeholders = ['example.com', 'yourdomain.com', 'test.com', 'yourname@', 'email@', 'domain.com', 'tempmail', 'mailinator']
    for p in placeholders:
        if p in email:
            return True
    return False

def is_dummy_phone(phone):
    if not phone:
        return False
    phone = phone.strip()
    # Extract digits only
    digits = re.sub(r'\D', '', phone)
    
    # Check if empty after extracting digits
    if not digits:
        return True
        
    dummy_patterns = [
        '5551234567',
        '0000000000',
        '1234567890',
        '123456789',
        '987654321',
        '1111111111',
        '2222222222',
        '3333333333',
        '4444444444',
        '5555555555',
        '6666666666',
        '7777777777',
        '8888888888',
        '9999999999'
    ]
    for pattern in dummy_patterns:
        if pattern in digits:
            return True
            
    # Also if digits are too short or repeating single digit, e.g. "0000"
    if len(set(digits)) == 1 and len(digits) > 3:
        return True
        
    return False

results = {}

for country, info in files.items():
    path = info["path"]
    mapping = info["mapping"]
    
    with open(path, mode='r', encoding='utf-8-sig', errors='ignore') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        
    total_leads = len(rows)
    
    # Counts
    companies = []
    domains = []
    
    dummy_emails_count = 0
    dummy_phones_count = 0
    low_value_count = 0
    
    field_counts = {k: 0 for k in mapping.keys()}
    
    dummy_email_list = []
    dummy_phone_list = []
    
    for row in rows:
        # Get values using mapped headers
        comp_val = row.get(mapping["Company"], "").strip()
        email_val = row.get(mapping["Email"], "").strip()
        phone_val = row.get(mapping["Phone"], "").strip()
        web_val = row.get(mapping["Website"], "").strip()
        addr_val = row.get(mapping["Address"], "").strip()
        loc_val = row.get(mapping["Location"], "").strip()
        li_val = row.get(mapping["LinkedIn"], "").strip()
        fb_val = row.get(mapping["Facebook"], "").strip()
        
        # Company Name
        if comp_val:
            companies.append(comp_val.lower().strip())
            field_counts["Company"] += 1
            
        # Email
        is_em_empty = not email_val
        is_em_dummy = is_dummy_email(email_val)
        if email_val:
            field_counts["Email"] += 1
            if is_em_dummy:
                dummy_emails_count += 1
                dummy_email_list.append(email_val)
                
        # Phone
        is_ph_empty = not phone_val
        is_ph_dummy = is_dummy_phone(phone_val)
        if phone_val:
            field_counts["Phone"] += 1
            if is_ph_dummy:
                dummy_phones_count += 1
                dummy_phone_list.append(phone_val)
                
        # Website
        if web_val:
            field_counts["Website"] += 1
            dom = clean_domain(web_val)
            if dom:
                domains.append(dom)
                
        # Address
        if addr_val:
            field_counts["Address"] += 1
            
        # Location
        if loc_val:
            field_counts["Location"] += 1
            
        # LinkedIn
        if li_val:
            field_counts["LinkedIn"] += 1
            
        # Facebook
        if fb_val:
            field_counts["Facebook"] += 1
            
        # Low value check: missing both a valid email and phone number
        has_valid_email = (not is_em_empty) and (not is_em_dummy)
        has_valid_phone = (not is_ph_empty) and (not is_ph_dummy)
        
        if (not has_valid_email) and (not has_valid_phone):
            low_value_count += 1
            
    # Duplication calculation
    # Company duplicates: Total non-empty - Unique non-empty
    unique_companies = set(companies)
    dup_companies_count = len(companies) - len(unique_companies)
    
    unique_domains = set(domains)
    dup_domains_count = len(domains) - len(unique_domains)
    
    fill_rates = {}
    for k, val in field_counts.items():
        fill_rates[k] = round((val / total_leads) * 100, 2) if total_leads > 0 else 0.0
        
    results[country] = {
        "total_leads": total_leads,
        "duplicate_companies": dup_companies_count,
        "duplicate_domains": dup_domains_count,
        "dummy_emails": dummy_emails_count,
        "dummy_phones": dummy_phones_count,
        "low_value_records": low_value_count,
        "fill_rates": fill_rates,
        "sample_dummy_emails": list(set(dummy_email_list))[:5],
        "sample_dummy_phones": list(set(dummy_phone_list))[:5]
    }

print("AUDIT RESULTS:")
import json
print(json.dumps(results, indent=2))
