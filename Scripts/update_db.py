import requests
import re
import os
import json
import csv
import io

# --- CONFIGURATION (Windows 11 SDK 22621) ---
URL_WIN = "https://raw.githubusercontent.com/tpn/winsdk-10/master/Include/10.0.22621.0/shared/winerror.h"
URL_WU = "https://raw.githubusercontent.com/tpn/winsdk-10/master/Include/10.0.22621.0/um/wuerror.h"
URL_NT = "https://raw.githubusercontent.com/tpn/winsdk-10/master/Include/10.0.22621.0/shared/ntstatus.h"
URL_BUG = "https://raw.githubusercontent.com/tpn/winsdk-10/master/Include/10.0.22621.0/shared/bugcodes.h"

URL_LINUX = "https://raw.githubusercontent.com/torvalds/linux/master/include/uapi/asm-generic/errno-base.h"
URL_LINUX_ADV = "https://raw.githubusercontent.com/torvalds/linux/master/include/uapi/asm-generic/errno.h"
URL_HTTP = "https://www.iana.org/assignments/http-status-codes/http-status-codes-1.csv"
URL_DNS = "https://www.iana.org/assignments/dns-parameters/dns-parameters-6.csv"

BASE_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
OUTPUT_FILE = os.path.join(BASE_DIR, 'error-db.ts')
CUSTOM_FILE = os.path.join(BASE_DIR, 'custom-knowledge.json')

# --- STATIC DATA ---
STATIC_DATA = {
    "container": {
        "137": {"name": "SIGKILL (OOMKilled)", "desc": "Container received SIGKILL (Out of Memory)"},
        "139": {"name": "SIGSEGV", "desc": "Segmentation Fault"},
        "143": {"name": "SIGTERM", "desc": "Graceful shutdown"}
    },
    "database": {
        "23505": {"name": "SQL_UNIQUE_VIOLATION", "desc": "Duplicate Key Violation"},
        "40001": {"name": "SQL_SERIALIZATION_FAILURE", "desc": "Deadlock Detected"}
    },
    "network": {
        "49": {"name": "LDAP_INVALID_CREDENTIALS", "desc": "Invalid Credentials"}
    }
}

def determine_products(code_hex, name, existing_tags, platform):
    products = set()
    safe_name = name if name else ""
    code_clean = code_hex.lower().replace('0x', '')

    if platform == "linux": products.add("Linux Kernel"); return list(products)
    if platform == "web": products.add("Web/API"); return list(products)
    if platform == "smtp": products.add("Exchange/Postfix"); return list(products)
    if platform == "database": products.add("SQL/DB"); return list(products)
    if platform == "container": products.add("Docker/K8s"); return list(products)
    if platform == "bsod": products.add("BSOD/Crash"); products.add("Kernel"); return list(products)

    # Windows Logic
    if safe_name.startswith("STATUS_"): products.add("Kernel/Driver")
    if code_clean.startswith("800f") or code_clean.startswith("8024") or "wu_" in safe_name.lower() or "cbs" in safe_name.lower():
        products.add("Windows Update"); products.add("DISM/CBS")
    if safe_name.startswith("WSA") or (code_clean.startswith("27") and len(code_clean) == 4):
        products.add("Winsock/TCP"); products.add("Network")

    if not products: products.add("System")
    return list(products)

def load_custom_data():
    if not os.path.exists(CUSTOM_FILE): return {}
    with open(CUSTOM_FILE, 'r', encoding='utf-8') as f: return json.load(f)

def format_ts_object(obj):
    hint = json.dumps(obj.get("solutionHint")) if obj.get("solutionHint") else "undefined"
    seen = json.dumps(obj.get("likelySeenIn", []))
    prods = json.dumps(obj.get("products", []))
    runbook_str = "undefined"
    if "runbook" in obj:
        rb = obj["runbook"]
        causes = json.dumps(rb.get("causes", []))
        cmd = json.dumps(rb.get("fixCommand")) if rb.get("fixCommand") else "undefined"
        deep = json.dumps(rb.get("deepDive")) if rb.get("deepDive") else "undefined"
        runbook_str = f"{{ causes: {causes}, fixCommand: {cmd}, deepDive: {deep} }}"

    return f"""  {{
    code: "{obj.get('code')}",
    codeInt: {obj.get('codeInt', 0)},
    name: "{obj.get('name')}",
    description: "{obj.get('description', '').replace('"', "'").replace(chr(92), chr(92)+chr(92))}",
    platform: "{obj.get('platform', 'windows')}",
    source: "{obj.get('source', 'Custom')}",
    solutionHint: {hint},
    runbook: {runbook_str},
    likelySeenIn: {seen},
    products: {prods}
  }}"""

def fetch_and_parse():
    print(f"[*] Veri tabanı oluşturuluyor...")
    custom_data = load_custom_data()
    errors = {} 

    # --- 1. SMART WINDOWS PARSER (REGEX UPDATE) ---
    # Bu regex, C castinglerini ((NTSTATUS)...) ve makroları (_HRESULT_TYPEDEF_) görmezden gelir
    # Sadece satırın içindeki "0x123AB" formatını çeker.
    windows_sources = [
        (URL_WIN, "Win32", "windows", r"ERROR_"),
        (URL_WU, "WindowsUpdate", "windows", r"WU_E_|CBS_"),
        (URL_NT, "NTSTATUS", "windows", r"STATUS_"),
        (URL_BUG, "BugCheck", "bsod", r"[A-Z0-9_]+")
    ]

    for url, source, plat, prefix in windows_sources:
        print(f"[*] Taraniyor: {source}...")
        try:
            content = requests.get(url).text
            # Adım 1: #define SATIRINI bul
            for line in content.splitlines():
                if not line.strip().startswith("#define"): continue
                
                parts = line.split(maxsplit=2)
                if len(parts) < 3: continue
                
                name = parts[1]
                rest = parts[2] # Değer kısmı (karmaşık olabilir)

                # Prefix kontrolü (Gürültüyü azaltmak için)
                if prefix != r"[A-Z0-9_]+" and not re.match(prefix, name):
                    continue

                # Adım 2: Satırın içinde HEX kodu ara (0x...)
                hex_match = re.search(r"(0x[0-9A-Fa-f]+)", rest)
                if hex_match:
                    raw_code = hex_match.group(1)
                    try:
                        int_val = int(raw_code, 16)
                        if int_val > 0x7FFFFFFF: int_val -= 0x100000000 # Signed 32-bit fix
                        
                        display_code = hex(int_val).lower()
                        # BugCheck kodları bazen 0x0000001A gelir, bazen 0x1A.
                        # Biz her zaman full hex saklayalım.
                        
                        errors[display_code] = {
                            "code": display_code, "codeInt": int_val, "name": name,
                            "description": name.replace('_', ' ').title(),
                            "platform": plat, "source": source, "solutionHint": None, "likelySeenIn": [], "products": []
                        }
                    except: continue
        except Exception as e: print(f"[!] Hata ({source}): {e}")

    # --- 2. LINUX & WEB (Standart) ---
    print(f"[*] Standartlar taranıyor...")
    # Linux
    for url in [URL_LINUX, URL_LINUX_ADV]:
        try:
            content = requests.get(url).text
            for line in content.splitlines():
                m = re.search(r"^\s*#define\s+([A-Z0-9]+)\s+(\d+)\s*\/\*\s*(.*?)\s*\*\/", line)
                if m:
                    errors[m.group(2)] = {"code": m.group(2), "codeInt": int(m.group(2)), "name": m.group(1), "description": m.group(3), "platform": "linux", "source": "Errno", "solutionHint": None, "likelySeenIn": ["Linux"], "products": []}
        except: pass
    
    # HTTP
    try:
        r = requests.get(URL_HTTP); r.encoding='utf-8'
        reader = csv.reader(io.StringIO(r.text))
        next(reader)
        for row in reader:
            if len(row)>1 and row[0].isdigit(): errors[row[0]] = {"code": row[0], "codeInt": int(row[0]), "name": f"HTTP_{row[0]}", "description": row[1], "platform": "web", "source": "IANA", "solutionHint": None, "likelySeenIn": [], "products": []}
    except: pass

    # DNS
    try:
        r = requests.get(URL_DNS); r.encoding='utf-8'
        reader = csv.reader(io.StringIO(r.text))
        for row in reader:
             if len(row)>1 and row[0].isdigit(): errors[row[0]] = {"code": f"DNS_RCODE_{row[0]}", "codeInt": int(row[0]), "name": row[1] or "DNS", "description": row[2] if len(row)>2 else "", "platform": "network", "source": "IANA", "solutionHint": None, "likelySeenIn": [], "products": []}
    except: pass

    # --- 3. MERGE ---
    for k, v in STATIC_DATA.items():
        for c, d in v.items(): errors[c] = {"code": c, "codeInt": int(c) if c.isdigit() else 0, "name": d["name"], "description": d["desc"], "platform": k, "source": "Static", "solutionHint": None, "likelySeenIn": [], "products": []}

    for c, d in custom_data.items():
        cl = c.lower()
        if cl not in errors: errors[cl] = {"code": cl, "codeInt": 0, "name": "CUSTOM", "description": "", "platform": "windows", "source": "Custom", "solutionHint": None, "likelySeenIn": [], "products": []}
        errors[cl].update(d)
        if "products" not in errors[cl]: errors[cl]["products"] = []

    # Tagging
    for obj in errors.values():
        obj["products"] = determine_products(obj.get("code"), obj.get("name"), obj.get("likelySeenIn"), obj.get("platform", "windows"))

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write("import { ErrorCode } from '../src/types';\n\n// AUTO-GENERATED\nexport const errorDatabase: ErrorCode[] = [\n")
        f.write(",\n".join([format_ts_object(obj) for obj in errors.values()]))
        f.write("\n];\n")
    print(f"[+] TAMAMLANDI! Toplam: {len(errors)}")

if __name__ == "__main__":
    fetch_and_parse()