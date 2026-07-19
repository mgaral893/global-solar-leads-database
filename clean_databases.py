#!/usr/bin/env python3
import os
import csv
import re

files_to_clean = [
    "/home/ubuntu/agi-agent/projects/global-solar-leads-database/us_solar_installers.csv",
    "/home/ubuntu/agi-agent/projects/global-solar-leads-database/uk_solar_installers.csv",
    "/home/ubuntu/agi-agent/projects/global-solar-leads-database/ca_solar_installers.csv",
    "/home/ubuntu/agi-agent/projects/global-solar-leads-database/au_solar_installers.csv",
    "/home/ubuntu/agi-agent/projects/spain-solar-leads-database/instaladores_solares_espana.csv"
]

dummy_email_patterns = [
    "example.com", "domain.com", "test.com", "email.com", "yourdomain.com", 
    "exemple.com", "yourname@", "email@", "admin@", "test@", "wordpress@",
    "no-reply@", "noreply@"
]

def clean_file(path):
    print(f"Cleaning {path}...")
    if not os.path.exists(path):
        print(f"File not found: {path}")
        return
        
    cleaned_rows = []
    headers = []
    
    with open(path, mode="r", encoding="utf-8") as f:
        reader = csv.reader(f)
        headers = next(reader, None)
        if not headers:
            return
            
        for row in reader:
            if len(row) < len(headers):
                row += [""] * (len(headers) - len(row))
                
            # Clean email (index 2 in standard structure)
            email = row[2].strip().lower()
            if any(p in email for p in dummy_email_patterns) or email in [
                "email@exemple.com", "yourname@domain.com", "info@yourdomain.com", 
                "email@example.com", "contact@domain.com", "test@test.com", 
                "user@example.com", "admin@domain.com", "name@domain.com", 
                "support@yourdomain.com", "hello@company.com"
            ]:
                row[2] = ""
                
            # Clean phone (index 3 in standard structure)
            phone = row[3].strip()
            digits = "".join(re.findall(r"\d", phone))
            if "5551234" in digits or "1234567890" in digits or "0000000000" in digits or len(digits) < 7:
                row[3] = ""
                
            cleaned_rows.append(row)
            
    with open(path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(cleaned_rows)
        
    print(f"✅ Cleaned {len(cleaned_rows)} rows in {path}")

def main():
    for f in files_to_clean:
        clean_file(f)

if __name__ == "__main__":
    main()
