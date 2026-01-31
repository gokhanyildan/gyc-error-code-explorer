import requests
import re
import csv
import io
from .config import URLS, REGEX
from .enrichment import to_unsigned_hex, title_case_name

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

def fetch_bsod():
    errors = {}
    print("    [-] Fetching BSOD data...")
    try:
        r = requests.get(URLS["MS_BSOD"], headers=HEADERS)
        matches = re.findall(REGEX["BSOD_LINK"], r.text)
        for code_hex, slug in matches:
            try:
                int_val = int(code_hex, 16)
                display_code = to_unsigned_hex(int_val, force_pad=True).lower()
                raw_name = slug.upper().replace('-', '_') if slug else f"BUGCHECK_{code_hex.upper()}"
                errors[display_code] = {"code": display_code, "codeInt": int_val, "name": raw_name, "description": title_case_name(raw_name), "platform": "bsod", "source": "Microsoft Learn", "isCommon": False}
            except: continue
    except: pass
    return errors

def fetch_windows_headers():
    errors = {}
    print("    [-] Fetching Windows Headers...")
    sources = [(URLS["WIN_WIN32"], "Win32", "windows", None), (URLS["WIN_UPDATE"], "WindowsUpdate", "windows", r"WU_E_|CBS_"), (URLS["WIN_NTSTATUS"], "NTSTATUS", "windows", r"STATUS_")]
    regex = re.compile(REGEX["WIN_DEFINE"])
    for url, source, plat, prefix_filter in sources:
        count = 0
        try:
            r = requests.get(url); text = r.text
            for line in text.splitlines():
                match = regex.search(line)
                if match:
                    name = match.group(1); raw_val = match.group(2)
                    if prefix_filter and not re.match(prefix_filter, name): continue
                    if len(name) < 4: continue
                    try:
                        raw_val = raw_val.replace('L', '')
                        int_val = int(raw_val, 16) if '0x' in raw_val else int(raw_val)
                        if int_val > 0x7FFFFFFF: int_val -= 0x100000000
                        display_code = to_unsigned_hex(int_val).lower()
                        errors[display_code] = {"code": display_code, "codeInt": int_val, "name": name, "description": name.replace('_', ' ').title(), "platform": plat, "source": source, "isCommon": False}
                        count += 1
                    except: continue
        except: pass
        print(f"        [OK] {source}: {count}")
    return errors

def fetch_postgres():
    errors = {}
    print("    [-] Fetching PostgreSQL...")
    try:
        r = requests.get(URLS["POSTGRES"])
        for line in r.text.splitlines():
            parts = line.split()
            if len(parts) >= 3 and len(parts[0]) == 5 and parts[0].isalnum():
                errors[parts[0]] = {"code": parts[0], "codeInt": 0, "name": parts[2], "description": "PostgreSQL Error", "platform": "database", "source": "PostgreSQL", "isCommon": False}
    except: pass
    return errors

def fetch_kubernetes():
    errors = {}
    print("    [-] Fetching Kubernetes (K8s)...")
    try:
        r = requests.get(URLS["K8S_TYPES"]); text = r.text
        matches = re.findall(r'const\s+([A-Z][a-zA-Z0-9]+)\s*.*=\s*"([^"]+)"', text)
        for name, val in matches:
            if len(val) < 3 or " " in val: continue
            errors[val] = {"code": val, "codeInt": 0, "name": name, "description": f"Kubernetes Pod/Container Status: {val}", "platform": "container", "source": "Kubernetes Git", "isCommon": False}
    except: pass
    try:
        r = requests.get(URLS["K8S_ERRORS"]); text = r.text
        matches = re.findall(r'const\s+(StatusReason[A-Z][a-zA-Z0-9]+)\s*StatusReason\s*=\s*"([^"]+)"', text)
        for name, val in matches:
            errors[val] = {"code": val, "codeInt": 0, "name": name, "description": f"Kubernetes API Status Reason: {val}", "platform": "container", "source": "Kubernetes Git", "isCommon": True}
    except: pass
    print(f"        [OK] Kubernetes: {len(errors)}")
    return errors

def fetch_standards():
    errors = {}
    print("    [-] Fetching Standards...")
    
    # Linux
    c_lin = 0
    try:
        for url in [URLS["LINUX_BASE"], URLS["LINUX_ADV"]]:
            r = requests.get(url)
            for line in r.text.splitlines():
                m = re.search(REGEX["LINUX_DEFINE"], line)
                if m: errors[m.group(2)] = {"code": m.group(2), "codeInt": int(m.group(2)), "name": m.group(1), "description": m.group(3), "platform": "linux", "source": "Linux Kernel", "isCommon": False}; c_lin += 1
    except: pass
    print(f"        [OK] Linux: {c_lin}")

    # HTTP
    c_http = 0
    try:
        r = requests.get(URLS["HTTP"]); r.encoding='utf-8'
        reader = csv.reader(io.StringIO(r.text)); next(reader)
        for row in reader:
            if len(row)>1 and row[0].isdigit(): errors[row[0]] = {"code": row[0], "codeInt": int(row[0]), "name": f"HTTP_{row[0]}", "description": row[1], "platform": "web", "source": "IANA", "isCommon": False}; c_http += 1
    except: pass
    print(f"        [OK] HTTP: {c_http}")

    # SMTP (ULTRA AGGRESSIVE MODE)
    c_smtp = 0
    try:
        r = requests.get(URLS["SMTP"])
        r.encoding = 'utf-8'
        raw_text = r.text
        
        # Debug: Bakalım veri geliyor mu?
        print(f"        [DEBUG] SMTP Raw Length: {len(raw_text)}")
        
        # Regex: Satırın başında "X.Y.Z" veya X.Y.Z arar.
        # Örnek satır: 2.0.0,,"Success",...
        pattern = re.compile(r'^\s*"?([245]\.\d+\.\d+)"?\s*,(.*)')
        
        for line in raw_text.splitlines():
            match = pattern.search(line)
            if match:
                code = match.group(1)
                rest = match.group(2)
                
                # Description'ı temizle (virgül sonrası ilk parça)
                # Satır: ,,"Success",[RFC...
                parts = rest.split(',')
                # Genelde açıklama 2. parçadadır (boşluktan sonra)
                desc = "SMTP Status Code"
                for p in parts:
                    clean_p = p.replace('"', '').strip()
                    if len(clean_p) > 3 and not clean_p.startswith('['):
                        desc = clean_p
                        break
                
                errors[code] = {
                    "code": code,
                    "codeInt": 0,
                    "name": f"SMTP_{code}",
                    "description": desc,
                    "platform": "smtp",
                    "source": "IANA",
                    "isCommon": False
                }
                c_smtp += 1
    except Exception as e: print(f"        [!] SMTP Error: {e}")
    print(f"        [OK] SMTP: {c_smtp}")

    return errors