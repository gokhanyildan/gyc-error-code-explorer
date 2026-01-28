import requests
import re
import os
import json

# --- CONFIGURATION ---
URL = "https://raw.githubusercontent.com/tpn/winsdk-10/master/Include/10.0.10240.0/shared/winerror.h"
BASE_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
OUTPUT_FILE = os.path.join(BASE_DIR, 'error-db.ts')
CUSTOM_FILE = os.path.join(BASE_DIR, 'custom-knowledge.json')

def load_custom_data():
    """Loads the manual overrides from JSON."""
    if not os.path.exists(CUSTOM_FILE):
        print("[!] Warning: custom-knowledge.json not found. Creating empty one.")
        with open(CUSTOM_FILE, 'w') as f: json.dump({}, f)
        return {}
    
    with open(CUSTOM_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def fetch_and_parse():
    print(f"[*] Loading Custom Knowledge from: {CUSTOM_FILE}...")
    custom_data = load_custom_data()
    
    print(f"[*] Fetching raw header from: {URL}...")
    try:
        response = requests.get(URL)
        content = response.text
    except Exception as e:
        print(f"[!] Error downloading header: {e}")
        return

    print("[*] Parsing and Merging Data...")
    
    errors = {} # Use dict for deduplication (Key: HexCode)

    # 1. Parsing Regex Pattern
    # Matches: #define NAME  0x123 or 123
    regex_std = r"^\s*#define\s+([A-Z0-9_]+)\s+((?:0x[0-9A-Fa-f]+|\d+)L?)"
    regex_macro = r"^\s*#define\s+([A-Z0-9_]+)\s+_HRESULT_TYPEDEF_\((0x[0-9A-Fa-f]+)L?\)"

    lines = content.splitlines()
    for line in lines:
        name = None
        raw_code = None

        # Attempt Match
        match = re.search(regex_std, line) or re.search(regex_macro, line)
        if match:
            name = match.group(1)
            raw_code = match.group(2).replace('L', '')

        if name and raw_code:
            # Clean Code
            if not (raw_code.startswith('0x') or raw_code.isdigit()): continue
            
            try:
                # Normalize Hex/Int
                if raw_code.startswith('0x'):
                    int_val = int(raw_code, 16)
                    if int_val > 0x7FFFFFFF: int_val -= 0x100000000
                    hex_code = raw_code.lower()
                else:
                    int_val = int(raw_code)
                    hex_code = hex(int_val).lower()

                # Basic Source Logic
                source = "Win32"
                if name.startswith("RPC_"): source = "RPC"
                elif name.startswith("WSA"): source = "Winsock"
                elif name.startswith("E_") or name.startswith("CO_E_"): source = "HRESULT"

                desc = name.replace('ERROR_', '').replace('E_', '').replace('_', ' ').title()

                # Create Base Object
                errors[hex_code] = {
                    "code": hex_code,
                    "codeInt": int_val,
                    "name": name,
                    "description": desc,
                    "platform": "windows",
                    "source": source,
                    "solutionHint": None,
                    "likelySeenIn": []
                }
            except ValueError: continue

    # 2. APPLY CUSTOM OVERRIDES (The Merge)
    # This overwrites or adds new entries from JSON
    print(f"[*] Applying {len(custom_data)} custom overrides...")
    
    for code, data in custom_data.items():
        clean_code = code.lower()
        
        # If code exists in SDK, update it. If not (like SCCM), create it.
        if clean_code not in errors:
            # New entry (e.g., SCCM)
            errors[clean_code] = {
                "code": clean_code,
                "codeInt": int(clean_code, 16) if clean_code.startswith('0x') else 0,
                "name": data.get("name", "UNKNOWN_ERROR"),
                "description": data.get("description", "Custom Error"),
                "platform": "windows",
                "source": data.get("source", "Custom"),
                "solutionHint": data.get("solutionHint"),
                "likelySeenIn": data.get("likelySeenIn", [])
            }
        else:
            # Existing entry - Enrich it!
            if "solutionHint" in data:
                errors[clean_code]["solutionHint"] = data["solutionHint"]
            if "likelySeenIn" in data:
                errors[clean_code]["likelySeenIn"] = data["likelySeenIn"]
            if "overrideName" in data:
                errors[clean_code]["name"] = data["overrideName"]
            if "description" in data:
                errors[clean_code]["description"] = data["description"]

    # 3. Generate TypeScript
    print(f"[*] Total Unique Codes: {len(errors)}. Writing to file...")
    
    # Convert dict to list
    final_list = list(errors.values())
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write("import { ErrorCode } from '../src/types';\n\n")
        f.write("// AUTO-GENERATED + CUSTOM JSON OVERLAYS\n")
        f.write("export const errorDatabase: ErrorCode[] = [\n")
        
        for obj in final_list:
            f.write(format_ts_object(obj) + ",\n")
            
        f.write("];\n")
    
    print("[+] Database updated successfully.")

def format_ts_object(obj):
    # Helper to clean strings for TS
    def clean_str(s): return str(s).replace('"', '\\"').replace('\n', '\\n') if s else "undefined"
    
    hint = f'"{clean_str(obj.get("solutionHint"))}"' if obj.get("solutionHint") else "undefined"
    seen = str(obj.get("likelySeenIn", [])).replace("'", '"')

    # RUNBOOK PARSING (NEW)
    runbook_str = "undefined"
    if "runbook" in obj:
        rb = obj["runbook"]
        causes = str(rb.get("causes", [])).replace("'", '"')
        cmd = f'"{clean_str(rb.get("fixCommand"))}"' if rb.get("fixCommand") else "undefined"
        deep = f'"{clean_str(rb.get("deepDive"))}"' if rb.get("deepDive") else "undefined"
        
        runbook_str = f"""{{
        causes: {causes},
        fixCommand: {cmd},
        deepDive: {deep}
    }}"""

    return f"""  {{
    code: "{obj['code']}",
    codeInt: {obj['codeInt']},
    name: "{obj['name']}",
    description: "{obj['description']}",
    platform: "{obj['platform']}",
    source: "{obj['source']}",
    solutionHint: {hint},
    runbook: {runbook_str},
    likelySeenIn: {seen}
  }}"""

if __name__ == "__main__":
    fetch_and_parse()