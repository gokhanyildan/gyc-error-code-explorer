import requests
import re
import os

# Source: Windows SDK Header Mirror
URL = "https://raw.githubusercontent.com/tpn/winsdk-10/master/Include/10.0.10240.0/shared/winerror.h"
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'error-db.ts')

# --- CUSTOM SCCM & SPECIAL CODES (Manual Injection) ---
CUSTOM_ERRORS = [
    {
        "code": "0x87D00669",
        "codeInt": -2016410007,
        "name": "CCM_E_APPC_CONTENT_NOT_FOUND",
        "description": "Content cannot be found.",
        "platform": "windows",
        "source": "SCCM",
        "solutionHint": "SCCM Classic: The client cannot find the content on a Distribution Point. Check Boundary Groups."
    },
    {
        "code": "0x87D00607",
        "codeInt": -2016410105,
        "name": "CCM_E_PROGRESS_TIMEOUT",
        "description": "Content download timeout.",
        "platform": "windows",
        "source": "SCCM",
        "solutionHint": "Maintenance window might be too short or content is too large."
    },
    {
        "code": "0x80070005", # Manually ensuring this exists as a fallback if regex misses specific mapping
        "codeInt": -2147024891,
        "name": "E_ACCESSDENIED",
        "description": "General access denied error.",
        "platform": "windows",
        "source": "HRESULT",
        "solutionHint": "Check NTFS permissions, Run as Administrator, or DCOM settings."
    }
]

def fetch_and_parse():
    print(f"[*] Fetching raw header from: {URL}...")
    try:
        response = requests.get(URL)
        content = response.text
    except Exception as e:
        print(f"[!] Error: {e}")
        return

    print("[*] Parsing content with Advanced Regex...")
    
    errors = []
    seen_keys = set() # To prevent duplicates (Code + Name)

    # 1. Add Custom/SCCM Errors first (High Priority)
    for err in CUSTOM_ERRORS:
        key = f"{err['code']}-{err['name']}"
        seen_keys.add(key)
        errors.append(format_ts_object(err))

    # 2. Parse Standard Defines: #define NAME 0x123
    regex_std = r"^\s*#define\s+([A-Z0-9_]+)\s+((?:0x[0-9A-Fa-f]+|\d+)L?)"
    
    # 3. Parse HRESULT Macros: #define NAME _HRESULT_TYPEDEF_(0x123)
    regex_macro = r"^\s*#define\s+([A-Z0-9_]+)\s+_HRESULT_TYPEDEF_\((0x[0-9A-Fa-f]+)L?\)"

    lines = content.splitlines()
    
    for line in lines:
        name = None
        raw_code = None

        # Try Match Standard
        match_std = re.search(regex_std, line)
        if match_std:
            name = match_std.group(1)
            raw_code = match_std.group(2).replace('L', '')

        # Try Match Macro (If std failed)
        if not name:
            match_macro = re.search(regex_macro, line)
            if match_macro:
                name = match_macro.group(1)
                raw_code = match_macro.group(2).replace('L', '')

        # Process if found
        if name and raw_code:
            # Skip if code is not numeric/hex (e.g. other macros)
            if not (raw_code.startswith('0x') or raw_code.isdigit()): continue

            try:
                # Normalization
                if raw_code.startswith('0x'):
                    int_val = int(raw_code, 16)
                    # Signed 32-bit correction
                    if int_val > 0x7FFFFFFF: int_val -= 0x100000000
                else:
                    int_val = int(raw_code)
                    raw_code = hex(int_val)

                # Skip duplicates (Prioritize Custom Errors we added first)
                key = f"{raw_code}-{name}"
                if key in seen_keys: continue
                seen_keys.add(key)

                # Heuristic Source Categorization
                source = "Win32"
                if name.startswith("RPC_"): source = "RPC"
                elif name.startswith("WSA"): source = "Winsock"
                elif name.startswith("E_") or name.startswith("CO_E_"): source = "HRESULT"
                elif name.startswith("ERROR_"): source = "Win32"

                desc = name.replace('ERROR_', '').replace('E_', '').replace('_', ' ').title()

                error_obj = {
                    "code": raw_code,
                    "codeInt": int_val,
                    "name": name,
                    "description": desc,
                    "platform": "windows",
                    "source": source,
                    "solutionHint": None
                }
                
                errors.append(format_ts_object(error_obj))

            except ValueError: continue

    print(f"[*] Total unique codes: {len(errors)}. Writing to file...")
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write("import { ErrorCode } from '../types';\n\n")
        f.write("// AUTO-GENERATED + CUSTOM INJECTED\n")
        f.write("export const errorDatabase: ErrorCode[] = [\n")
        f.write(",\n".join(errors))
        f.write("\n];\n")
    
    print("[+] Database updated successfully.")

def format_ts_object(obj):
    # Helper to format Python dict to TS string
    hint_str = f'"{obj["solutionHint"]}"' if obj.get("solutionHint") else "undefined"
    return f"""  {{
    code: "{obj['code']}",
    codeInt: {obj['codeInt']},
    name: "{obj['name']}",
    description: "{obj['description']}",
    platform: "{obj['platform']}",
    source: "{obj['source']}",
    solutionHint: {hint_str}
  }}"""

if __name__ == "__main__":
    fetch_and_parse()