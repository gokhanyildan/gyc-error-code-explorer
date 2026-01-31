import sys
import os
import json

# Modül yolunu ekle
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.config import OUTPUT_FILE, CUSTOM_FILE
from modules.static_data import STATIC_DATA
from modules.enrichment import determine_products, generate_doc_url, determine_severity, format_ts_object, to_unsigned_hex
from modules.scrapers import fetch_bsod, fetch_windows_headers, fetch_postgres, fetch_standards, fetch_kubernetes

def load_custom_data():
    if not os.path.exists(CUSTOM_FILE): return {}
    with open(CUSTOM_FILE, 'r', encoding='utf-8') as f: return json.load(f)

def main():
    print("[*] ORCHESTRATOR STARTED: Building Error Database...")
    
    all_errors = {}
    
    # 1. Fetching Phase
    print("[-] Phase 1: Scraping Data...")
    all_errors.update(fetch_bsod())
    all_errors.update(fetch_windows_headers())
    all_errors.update(fetch_postgres())
    all_errors.update(fetch_standards())
    all_errors.update(fetch_kubernetes()) # NEW
    
    print(f"    -> Total so far: {len(all_errors)}")
    
    # 2. Merging Static Data
    print("[-] Phase 2: Applying Premium Data...")
    for k, v in STATIC_DATA.items():
        for c, d in v.items():
            if k == "windows":
                int_val = int(c, 16)
                code_key = to_unsigned_hex(int_val).lower()
                src_label = "Microsoft Learn"
            elif k == "bsod":
                int_val = int(c, 16)
                code_key = to_unsigned_hex(int_val, force_pad=True).lower()
                src_label = "Microsoft Learn"
            else:
                code_key = c
                src_label = "Official Docs"
            
            if code_key not in all_errors:
                all_errors[code_key] = {"code": code_key, "codeInt": 0, "platform": k, "likelySeenIn": [], "products": []}
            
            all_errors[code_key].update({
                "codeInt": int(c, 16) if c.startswith("0x") else int(c) if c.isdigit() else 0,
                "name": d["name"],
                "description": d["desc"],
                "platform": k,
                "source": src_label,
                "solutionHint": d.get("solutionHint"),
                "isCommon": d.get("isCommon", False)
            })
            if "likelySeenIn" in d: all_errors[code_key]["likelySeenIn"] = d["likelySeenIn"]

    # 3. Merging Custom User Data
    custom_data = load_custom_data()
    for c, d in custom_data.items():
        cl = c.lower()
        if cl not in all_errors: 
            all_errors[cl] = {"code": cl, "codeInt": 0, "name": "CUSTOM", "description": "", "platform": "windows", "source": "Custom"}
        all_errors[cl].update(d)

    # 4. Enrichment & Tagging
    print("[-] Phase 3: Enriching Data...")
    for obj in all_errors.values():
        obj["products"] = determine_products(obj.get("code"), obj.get("name"), obj.get("likelySeenIn"), obj.get("platform", "windows"))
        obj["docUrl"] = generate_doc_url(obj.get("code"), obj.get("platform"), obj.get("name"))
        obj["severity"] = determine_severity(obj.get("code"), obj.get("name"), obj.get("platform"))

    # 5. Output
    print(f"[-] Phase 4: Writing {len(all_errors)} records to file...")
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write("import { ErrorCode } from '../src/types';\n\n// AUTO-GENERATED\nexport const errorDatabase: ErrorCode[] = [\n")
        f.write(",\n".join([format_ts_object(obj) for obj in all_errors.values()]))
        f.write("\n];\n")
    
    print("[+] SUCCESS: Database build complete.")

if __name__ == "__main__":
    main()