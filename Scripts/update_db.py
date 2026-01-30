import requests
import re
import os
import json
import csv
import io

# --- CONFIGURATION ---
URL_MS_BSOD = "https://learn.microsoft.com/en-us/windows-hardware/drivers/debugger/bug-check-code-reference2"

# Windows Legacy Headers
URL_WIN = "https://raw.githubusercontent.com/tpn/winsdk-10/master/Include/10.0.10240.0/shared/winerror.h"
URL_WU = "https://raw.githubusercontent.com/tpn/winsdk-10/master/Include/10.0.10240.0/um/wuerror.h"
URL_NT = "https://raw.githubusercontent.com/tpn/winsdk-10/master/Include/10.0.10240.0/shared/ntstatus.h"

# Linux & Standards (RESTORED)
URL_LINUX = "https://raw.githubusercontent.com/torvalds/linux/master/include/uapi/asm-generic/errno-base.h"
URL_LINUX_ADV = "https://raw.githubusercontent.com/torvalds/linux/master/include/uapi/asm-generic/errno.h"
URL_HTTP = "https://www.iana.org/assignments/http-status-codes/http-status-codes-1.csv"
URL_DNS = "https://www.iana.org/assignments/dns-parameters/dns-parameters-6.csv"
URL_SMTP = "https://www.iana.org/assignments/smtp-enhanced-status-codes/smtp-enhanced-status-codes-1.csv"

BASE_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
OUTPUT_FILE = os.path.join(BASE_DIR, 'error-db.ts')
CUSTOM_FILE = os.path.join(BASE_DIR, 'custom-knowledge.json')

# --- PREMIUM STATIC DATA ---
STATIC_DATA = {
    "container": {
        "137": {"name": "SIGKILL (OOMKilled)", "desc": "Container received SIGKILL. Usually indicates the container ran out of memory (OOM). Check Docker memory limits.", "solutionHint": "Increase memory limit or optimize app memory usage."},
        "139": {"name": "SIGSEGV", "desc": "Segmentation Fault. The application tried to access memory it doesn't own.", "solutionHint": "Check for null pointer dereferences or buffer overflows in code."}
    },
    "database": {
        "23505": {"name": "SQL_UNIQUE_VIOLATION", "desc": "Duplicate Key Violation. You tried to insert a record with a key that already exists.", "solutionHint": "Check your INSERT query or use ON CONFLICT DO UPDATE."}
    },
    "network": {
        "49": {"name": "LDAP_INVALID_CREDENTIALS", "desc": "Invalid Credentials. The password or username provided for LDAP binding is incorrect.", "solutionHint": "Verify service account password and account status."}
    },
    "windows": {
        "0x800f081f": {
            "name": "CBS_E_SOURCE_MISSING", 
            "desc": "The source files could not be found. DISM cannot find the files required to restore the feature.",
            "solutionHint": "Use: DISM /Online /Cleanup-Image /RestoreHealth /Source:wim:D:\\sources\\install.wim:1 /LimitAccess",
            "likelySeenIn": ["DISM", "Windows Update"]
        },
        "0x800f0906": {
            "name": "CBS_E_DOWNLOAD_FAILURE", 
            "desc": "The source files could not be downloaded. Often caused by WSUS settings or Firewall.",
            "solutionHint": "Check internet connection or bypass WSUS via Group Policy temporarily.",
            "likelySeenIn": ["DISM", "Windows Update"]
        }
    },
    "bsod": {
        # TOP CRITICAL BSODs (Manual Override for Better Descriptions)
        "0x0000000a": {"name": "IRQL_NOT_LESS_OR_EQUAL", "desc": "A driver accessed a memory address that is invalid or at an IRQL that is too high.", "solutionHint": "Update all drivers. Run Windows Memory Diagnostic.", "likelySeenIn": ["Drivers", "RAM"]},
        "0x0000001a": {"name": "MEMORY_MANAGEMENT", "desc": "A severe memory management error occurred. Could be physical RAM corruption.", "solutionHint": "Reseat RAM sticks. Run MemTest86.", "likelySeenIn": ["RAM", "VRAM"]},
        "0x0000003b": {"name": "SYSTEM_SERVICE_EXCEPTION", "desc": "Exception in privileged code. Often caused by graphic drivers.", "solutionHint": "Update GPU and Chipset drivers.", "likelySeenIn": ["GPU Driver", "System"]},
        "0x00000050": {"name": "PAGE_FAULT_IN_NONPAGED_AREA", "desc": "Invalid system memory was referenced. Faulty AV or RAM.", "solutionHint": "Run chkdsk /f /r. Disable 3rd party Antivirus.", "likelySeenIn": ["RAM", "Antivirus"]},
        "0x0000007e": {"name": "SYSTEM_THREAD_EXCEPTION_NOT_HANDLED", "desc": "System thread exception not handled.", "solutionHint": "Check Event Viewer for failing driver.", "likelySeenIn": ["Drivers"]},
        "0x000000ef": {"name": "CRITICAL_PROCESS_DIED", "desc": "A critical system process died unexpectedly.", "solutionHint": "Run sfc /scannow and DISM restore health.", "likelySeenIn": ["System Core"]},
        "0x00000116": {"name": "VIDEO_TDR_FAILURE", "desc": "Display driver failed to recover from timeout.", "solutionHint": "Clean install GPU drivers with DDU.", "likelySeenIn": ["Nvidia/AMD"]},
        "0x00000124": {"name": "WHEA_UNCORRECTABLE_ERROR", "desc": "Fatal hardware error (Voltage/Heat).", "solutionHint": "Check CPU temps and PSU voltages.", "likelySeenIn": ["Hardware"]},
        "0x00000133": {"name": "DPC_WATCHDOG_VIOLATION", "desc": "DPC watchdog detected prolonged runtime.", "solutionHint": "Update SSD Firmware and WiFi drivers.", "likelySeenIn": ["SSD", "WiFi"]},
        "0xc000021a": {"name": "STATUS_SYSTEM_PROCESS_TERMINATED", "desc": "Crucial user-mode subsystem failed.", "solutionHint": "Uninstall recent updates or System Restore.", "likelySeenIn": ["Windows Update"]}
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

    if safe_name.startswith("STATUS_") or safe_name.startswith("BUGCODE_"): products.add("Kernel/Driver")
    if code_clean.startswith("800f") or code_clean.startswith("8024") or "cbs" in safe_name.lower() or "wu_" in safe_name.lower():
        products.add("Windows Update"); products.add("DISM/CBS")
    if safe_name.startswith("WSA") or (code_clean.startswith("27") and len(code_clean) == 4):
        products.add("Winsock/TCP"); products.add("Network")

    if not products: products.add("System")
    return list(products)

def load_custom_data():
    if not os.path.exists(CUSTOM_FILE): return {}
    with open(CUSTOM_FILE, 'r', encoding='utf-8') as f: return json.load(f)

def format_ts_object(obj):
    desc = obj.get('description', '').replace('"', "'").replace('\\', '\\\\').replace('\n', ' ')
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
    description: "{desc}",
    platform: "{obj.get('platform', 'windows')}",
    source: "{obj.get('source', 'Custom')}",
    solutionHint: {hint},
    runbook: {runbook_str},
    likelySeenIn: {seen},
    products: {prods}
  }}"""

def to_unsigned_hex(int_val, force_pad=False):
    if force_pad: return "0x" + format(int_val & 0xFFFFFFFF, '08x')
    return "0x" + format(int_val & 0xFFFFFFFF, 'x')

def title_case_name(name):
    return name.replace('_', ' ').title()

def fetch_and_parse():
    print(f"[*] Veri tabanı oluşturuluyor (FULL REPAIR)...")
    custom_data = load_custom_data()
    errors = {} 

    # --- 1. BSOD SCRAPER (Microsoft Learn) ---
    print(f"[*] BSOD Kodları çekiliyor...")
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(URL_MS_BSOD, headers=headers)
        regex_link = r'bug-check-(0x[0-9a-fA-F]+)(?:-+([a-zA-Z0-9-]+))?'
        matches = re.findall(regex_link, r.text)
        for code_hex, slug in matches:
            try:
                int_val = int(code_hex, 16)
                display_code = to_unsigned_hex(int_val, force_pad=True).lower()
                raw_name = slug.upper().replace('-', '_') if slug else f"BUGCHECK_{code_hex.upper()}"
                errors[display_code] = {
                    "code": display_code, "codeInt": int_val, "name": raw_name,
                    "description": f"{title_case_name(raw_name)}. See Microsoft Docs for details.",
                    "platform": "bsod", "source": "Microsoft Learn", "solutionHint": "Use 'analyze -v' in WinDbg.", "likelySeenIn": ["BSOD", "Kernel"], "products": []
                }
            except: continue
        print(f"    [+] {len(matches)} BSOD kodu işlendi.")
    except Exception as e: print(f"    [!] BSOD Fetch Error: {e}")

    # --- 2. WINDOWS LEGACY HEADERS ---
    print(f"[*] Windows Headers taranıyor...")
    windows_sources = [(URL_WIN, "Win32", "windows", None), (URL_WU, "WindowsUpdate", "windows", r"WU_E_|CBS_"), (URL_NT, "NTSTATUS", "windows", r"STATUS_")]
    regex_aggressive = re.compile(r'^\s*#define\s+([A-Z0-9_]+)\s+.*?(0x[0-9A-Fa-f]+)')
    for url, source, plat, prefix_filter in windows_sources:
        try:
            content = requests.get(url).text
            for line in content.splitlines():
                match = regex_aggressive.search(line)
                if match:
                    name = match.group(1); raw_code = match.group(2)
                    if prefix_filter and not re.match(prefix_filter, name): continue
                    if len(name) < 4: continue
                    try:
                        int_val = int(raw_code, 16)
                        if int_val > 0x7FFFFFFF: int_val -= 0x100000000
                        display_code = to_unsigned_hex(int_val, force_pad=False).lower()
                        if display_code not in errors or errors[display_code]["platform"] != "bsod":
                            errors[display_code] = {
                                "code": display_code, "codeInt": int_val, "name": name,
                                "description": name.replace('_', ' ').title(),
                                "platform": plat, "source": source, "solutionHint": None, "likelySeenIn": [], "products": []
                            }
                    except: continue
        except: pass

    # --- 3. LINUX KERNEL (RESTORED) ---
    print(f"[*] Linux Kernel Headers taranıyor...")
    for url in [URL_LINUX, URL_LINUX_ADV]:
        try:
            content = requests.get(url).text
            for line in content.splitlines():
                m = re.search(r"^\s*#define\s+([A-Z0-9]+)\s+(\d+)\s*\/\*\s*(.*?)\s*\*\/" , line)
                if m: errors[m.group(2)] = {"code": m.group(2), "codeInt": int(m.group(2)), "name": m.group(1), "description": m.group(3), "platform": "linux", "source": "Errno", "solutionHint": None, "likelySeenIn": ["Linux"], "products": []}
        except Exception as e: print(f"    [!] Linux Fetch Error: {e}")

    # --- 4. HTTP CODES (RESTORED) ---
    print(f"[*] HTTP Kodları çekiliyor...")
    try:
        r = requests.get(URL_HTTP); r.encoding='utf-8'
        reader = csv.reader(io.StringIO(r.text)); next(reader)
        for row in reader:
            if len(row)>1 and row[0].isdigit(): errors[row[0]] = {"code": row[0], "codeInt": int(row[0]), "name": f"HTTP_{row[0]}", "description": row[1], "platform": "web", "source": "IANA", "solutionHint": None, "likelySeenIn": [], "products": []}
    except: pass

    # --- 5. DNS RCODES (RESTORED) ---
    print(f"[*] DNS Kodları çekiliyor...")
    try:
        r = requests.get(URL_DNS); r.encoding='utf-8'
        reader = csv.reader(io.StringIO(r.text))
        for row in reader:
             if len(row)>1 and row[0].isdigit(): errors[row[0]] = {"code": f"DNS_RCODE_{row[0]}", "codeInt": int(row[0]), "name": row[1] or "DNS", "description": row[2] if len(row)>2 else "", "platform": "network", "source": "IANA", "solutionHint": None, "likelySeenIn": [], "products": []}
    except: pass

    # --- 6. SMTP CODES (RESTORED) ---
    print(f"[*] SMTP Kodları çekiliyor...")
    try:
        r = requests.get(URL_SMTP); r.encoding='utf-8'
        reader = csv.reader(io.StringIO(r.text))
        for row in reader:
             # CSV Format: Code, Sample, Description...
             if len(row)>1 and re.match(r'^\d\.\d\.\d+$', row[0]):
                  code_clean = row[0]
                  errors[code_clean] = {"code": code_clean, "codeInt": 0, "name": f"SMTP_{code_clean}", "description": row[1] if len(row)>1 else "SMTP Error", "platform": "smtp", "source": "IANA", "solutionHint": None, "likelySeenIn": ["Exchange", "Postfix"], "products": []}
    except: pass

    # --- 7. MERGE PREMIUM STATIC DATA ---
    print(f"[*] Premium Veriler Entegre Ediliyor...")
    for k, v in STATIC_DATA.items():
        for c, d in v.items(): 
            if k == "bsod":
                 val = int(c, 16)
                 clean_code = to_unsigned_hex(val, force_pad=True).lower()
            else:
                 clean_code = c.lower()
            errors[clean_code] = {"code": clean_code, "codeInt": int(c, 16) if c.startswith("0x") else int(c) if c.isdigit() else 0, "name": d["name"], "description": d["desc"], "platform": k, "source": "Manual (Premium)", "solutionHint": d.get("solutionHint"), "likelySeenIn": d.get("likelySeenIn", []), "products": []}

    # Custom Data Merge
    for c, d in custom_data.items():
        cl = c.lower()
        if cl not in errors: errors[cl] = {"code": cl, "codeInt": 0, "name": "CUSTOM", "description": "", "platform": "windows", "source": "Custom", "solutionHint": None, "likelySeenIn": [], "products": []}
        errors[cl].update(d)

    # Tagging
    for obj in errors.values():
        obj["products"] = determine_products(obj.get("code"), obj.get("name"), obj.get("likelySeenIn"), obj.get("platform", "windows"))

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write("import { ErrorCode } from '../src/types';\n\n// AUTO-GENERATED\nexport const errorDatabase: ErrorCode[] = [\n")
        f.write(",\n".join([format_ts_object(obj) for obj in errors.values()]))
        f.write("\n];\n")
    print(f"[+] TAMAMLANDI! Toplam Kayıt: {len(errors)}")

if __name__ == "__main__":
    fetch_and_parse()