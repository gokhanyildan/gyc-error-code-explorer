import requests
import re
import os
import json
import csv
import io

# --- CONFIGURATION ---
URL_WIN = "https://raw.githubusercontent.com/tpn/winsdk-10/master/Include/10.0.10240.0/shared/winerror.h"
URL_LINUX = "https://raw.githubusercontent.com/torvalds/linux/master/include/uapi/asm-generic/errno-base.h"
URL_LINUX_ADV = "https://raw.githubusercontent.com/torvalds/linux/master/include/uapi/asm-generic/errno.h"
URL_HTTP = "https://www.iana.org/assignments/http-status-codes/http-status-codes-1.csv"
URL_SMTP = "https://www.iana.org/assignments/smtp-enhanced-status-codes/smtp-enhanced-status-codes-1.csv"
URL_DNS = "https://www.iana.org/assignments/dns-parameters/dns-parameters-6.csv" 

BASE_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
OUTPUT_FILE = os.path.join(BASE_DIR, 'error-db.ts')
CUSTOM_FILE = os.path.join(BASE_DIR, 'custom-knowledge.json')

# --- STATIC DATA LAYERS ---
STATIC_DATA = {
    "container": {
        "125": {"name": "DOCKER_RUN_FAIL", "desc": "Docker daemon failed to run the command"},
        "126": {"name": "CMD_INVOKED_CANNOT_EXECUTE", "desc": "Command invoked cannot execute (Permission denied)"},
        "127": {"name": "CMD_NOT_FOUND", "desc": "Command not found"},
        "128": {"name": "INVALID_EXIT_ARG", "desc": "Invalid argument to exit"},
        "137": {"name": "SIGKILL (OOMKilled)", "desc": "Container received SIGKILL (Usually Out of Memory)"},
        "139": {"name": "SIGSEGV", "desc": "Segmentation Fault"},
        "143": {"name": "SIGTERM", "desc": "Container received SIGTERM"},
        "255": {"name": "EXIT_STATUS_OUT_OF_RANGE", "desc": "Exit status out of range"}
    },
    "database": {
        "08001": {"name": "SQL_CLIENT_UNABLE_TO_ESTABLISH_SQL_CONNECTION", "desc": "Client unable to establish connection"},
        "08003": {"name": "SQL_CONNECTION_DOES_NOT_EXIST", "desc": "Connection does not exist"},
        "08006": {"name": "SQL_CONNECTION_FAILURE", "desc": "Connection failure"},
        "23502": {"name": "SQL_NOT_NULL_VIOLATION", "desc": "Violates NOT NULL constraint"},
        "23503": {"name": "SQL_FOREIGN_KEY_VIOLATION", "desc": "Violates foreign key constraint"},
        "23505": {"name": "SQL_UNIQUE_VIOLATION", "desc": "Violates unique constraint (Duplicate Key)"},
        "40001": {"name": "SQL_SERIALIZATION_FAILURE", "desc": "Serialization failure (Deadlock)"},
        "42601": {"name": "SQL_SYNTAX_ERROR", "desc": "Syntax error"},
        "53000": {"name": "SQL_INSUFFICIENT_RESOURCES", "desc": "Insufficient resources"},
        "57014": {"name": "SQL_QUERY_CANCELED", "desc": "Query canceled due to timeout"}
    },
    "network": {
        "49": {"name": "LDAP_INVALID_CREDENTIALS", "desc": "Invalid Credentials"},
        "32": {"name": "LDAP_NO_SUCH_OBJECT", "desc": "No Such Object"},
        "50": {"name": "LDAP_INSUFFICIENT_ACCESS", "desc": "Insufficient Access Rights"},
        "52": {"name": "LDAP_UNAVAILABLE", "desc": "Server Unavailable"},
        "53": {"name": "LDAP_UNWILLING_TO_PERFORM", "desc": "Server Unwilling To Perform"}
    }
}

def determine_products(code_hex, name, existing_tags, platform):
    products = set()
    # Güvenlik önlemi: name veya existing_tags None gelirse patlamasın
    safe_name = name if name else ""
    safe_tags = existing_tags if existing_tags else []
    combined = " ".join(safe_tags).lower() + " " + safe_name.lower()
    
    if platform == "linux":
        products.add("Linux Kernel")
        return list(products)
    if platform == "web":
        products.add("Web/API")
        if code_hex.startswith("5"): products.add("Server Side")
        return list(products)
    if platform == "smtp":
        products.add("Exchange/Postfix")
        return list(products)
    if platform == "database":
        products.add("PostgreSQL/SQL")
        return list(products)
    if platform == "container":
        products.add("Docker/K8s")
        return list(products)
    if platform == "network":
        if "ldap" in safe_name.lower(): products.add("Active Directory/LDAP")
        if "dns" in safe_name.lower(): products.add("DNS")
        return list(products)

    code_clean = code_hex.lower().replace('0x', '')
    if safe_name.startswith("WSA") or (code_clean.startswith("27") and len(code_clean) == 4):
        products.add("Winsock/TCP")
        products.add("Network")
    if code_clean.startswith('87d') or "sccm" in combined: products.add("SCCM")
    if code_clean.startswith('8024') or "windows update" in combined: products.add("Windows Update")
    if code_clean.startswith('8018') or "intune" in combined: products.add("Intune")
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
    code: "{obj.get('code', 'UNKNOWN')}",
    codeInt: {obj.get('codeInt', 0)},
    name: "{obj.get('name', 'UNKNOWN')}",
    description: "{obj.get('description', '')}",
    platform: "{obj.get('platform', 'windows')}",
    source: "{obj.get('source', 'Custom')}",
    solutionHint: {hint},
    runbook: {runbook_str},
    likelySeenIn: {seen},
    products: {prods}
  }}"""

def fetch_and_parse():
    print(f"[*] Custom Knowledge yükleniyor...")
    custom_data = load_custom_data()
    errors = {} 

    # 1. WINDOWS SDK
    try:
        content = requests.get(URL_WIN).text
        regex_std = r"^\s*#define\s+([A-Z0-9_]+)\s+((?:0x[0-9A-Fa-f]+|\d+)L?)"
        for line in content.splitlines():
            match = re.search(regex_std, line)
            if match:
                name, raw_code = match.groups()
                raw_code = raw_code.replace('L', '')
                try:
                    if raw_code.startswith('0x'):
                        int_val = int(raw_code, 16)
                        if int_val > 0x7FFFFFFF: int_val -= 0x100000000
                    else:
                        int_val = int(raw_code)
                    
                    display_code = hex(int_val).lower()
                    platform = "windows"
                    if name.startswith("WSA"):
                        display_code = str(int_val)
                        platform = "windows"

                    errors[display_code] = {
                        "code": display_code, "codeInt": int_val, "name": name,
                        "description": name.replace('ERROR_', '').replace('_', ' ').title(),
                        "platform": platform, "source": "Win32", "solutionHint": None, "likelySeenIn": [], "products": []
                    }
                except ValueError: continue
    except Exception: pass

    # 2. LINUX
    for url in [URL_LINUX, URL_LINUX_ADV]:
        try:
            content = requests.get(url).text
            regex_linux = r"^\s*#define\s+([A-Z0-9]+)\s+(\d+)\s*\/\*\s*(.*?)\s*\*\/"
            for line in content.splitlines():
                match = re.search(regex_linux, line)
                if match:
                    name, raw_code, desc = match.groups()
                    errors[raw_code] = {
                        "code": raw_code, "codeInt": int(raw_code), "name": name, "description": desc,
                        "platform": "linux", "source": "Errno", "solutionHint": None, "likelySeenIn": ["Linux"], "products": []
                    }
        except Exception: pass

    # 3. HTTP
    try:
        response = requests.get(URL_HTTP); response.encoding = 'utf-8'
        reader = csv.reader(io.StringIO(response.text))
        next(reader)
        for row in reader:
            if len(row) < 2 or not row[0].isdigit(): continue
            errors[row[0]] = {
                "code": row[0], "codeInt": int(row[0]), "name": f"HTTP_{row[0]}", "description": row[1],
                "platform": "web", "source": "IANA", "solutionHint": None, "likelySeenIn": ["Browser"], "products": []
            }
    except Exception: pass

    # 4. DNS
    try:
        response = requests.get(URL_DNS); response.encoding = 'utf-8'
        reader = csv.reader(io.StringIO(response.text))
        for row in reader:
            if len(row) < 2 or not row[0].isdigit(): continue
            errors[row[0]] = {
                "code": f"DNS_RCODE_{row[0]}", "codeInt": int(row[0]), "name": row[1] or f"DNS_RCODE_{row[0]}", 
                "description": row[2] if len(row) > 2 else "DNS Response Code",
                "platform": "network", "source": "IANA DNS", "solutionHint": None, "likelySeenIn": ["DNS"], "products": []
            }
    except Exception: pass

    # 5. SMTP
    smtp_basics = {
        "250": "Requested mail action okay", "421": "Service not available", "450": "Mailbox unavailable",
        "500": "Syntax error", "503": "Bad sequence", "530": "Authentication required", "550": "User Unknown", "554": "Transaction failed"
    }
    for code, desc in smtp_basics.items():
        errors[code] = {
            "code": code, "codeInt": int(code), "name": f"SMTP_{code}", "description": desc,
            "platform": "smtp", "source": "RFC 5321", "solutionHint": None, "likelySeenIn": ["Exchange"], "products": []
        }

    # 6. STATIC LAYERS
    for plat, data in STATIC_DATA.items():
        for code, info in data.items():
            try:
                int_val = int(code) if code.isdigit() else 0
                errors[code] = {
                    "code": code, "codeInt": int_val, "name": info["name"], "description": info["desc"],
                    "platform": plat, "source": "Standard", "solutionHint": None, "likelySeenIn": [], "products": []
                }
            except: pass

    # 7. MERGE CUSTOM & SAVE (DÜZELTİLDİ)
    print(f"[*] Custom veriler birleştiriliyor...")
    for code, data in custom_data.items():
        clean_code = code.lower()
        
        # Eğer bu kod daha önce bulunmadıysa (Sıfırdan Custom Error)
        # Önce boş bir iskelet oluştur ki KeyError almayalım
        if clean_code not in errors:
            errors[clean_code] = {
                "code": clean_code,
                "codeInt": 0,
                "name": data.get("name", "CUSTOM_ERROR"),
                "description": data.get("description", ""),
                "platform": data.get("platform", "windows"),
                "source": "Custom",
                "solutionHint": None,
                "likelySeenIn": [],
                "products": []
            }
        
        # Şimdi custom veriyi üstüne yaz
        errors[clean_code].update(data)
        
        # Update işleminden sonra kritik alanların (code, name) silinmediğinden/boş kalmadığından emin ol
        if "code" not in errors[clean_code]: errors[clean_code]["code"] = clean_code
        if "name" not in errors[clean_code]: errors[clean_code]["name"] = "CUSTOM_ERROR"
        if "likelySeenIn" not in errors[clean_code]: errors[clean_code]["likelySeenIn"] = []
            
    # TAGGING
    print(f"[*] Etiketleme yapılıyor...")
    for obj in errors.values():
        obj["products"] = determine_products(
            obj.get("code"), 
            obj.get("name"), 
            obj.get("likelySeenIn"), 
            obj.get("platform", "windows")
        )

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write("import { ErrorCode } from '../src/types';\n\n// AUTO-GENERATED\nexport const errorDatabase: ErrorCode[] = [\n")
        f.write(",\n".join([format_ts_object(obj) for obj in errors.values()]))
        f.write("\n];\n")
    print(f"[+] Database Güncellendi! Toplam Kayıt: {len(errors)}")

if __name__ == "__main__":
    fetch_and_parse()