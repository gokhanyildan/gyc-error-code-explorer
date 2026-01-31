import json

def to_unsigned_hex(int_val, force_pad=False):
    """Sayıyı Hex stringe çevirir (Negatifleri düzeltir)."""
    if force_pad:
        return "0x" + format(int_val & 0xFFFFFFFF, '08x')
    return "0x" + format(int_val & 0xFFFFFFFF, 'x')

def title_case_name(name):
    return name.replace('_', ' ').title()

def generate_doc_url(code, platform, name):
    """Her platform için en doğru resmi doküman kaynağına link üretir."""
    if platform == "bsod":
        clean = code.replace('0x', '').lstrip('0')
        return f"https://learn.microsoft.com/en-us/windows-hardware/drivers/debugger/bug-check-0x{clean}"
    elif platform == "linux":
        return "https://man7.org/linux/man-pages/man3/errno.3.html"
    elif platform == "web":
        return f"https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/{code}"
    elif platform == "database" and "POSTGRES" in name.upper():
        return "https://www.postgresql.org/docs/current/errcodes-appendix.html"
    elif platform == "windows":
        return f"https://learn.microsoft.com/en-us/search/?terms={code}"
    # Kubernetes için genel arama, çünkü sabit bir hata listesi sayfası yok
    elif platform == "container":
        return f"https://kubernetes.io/search/?q={code}"
    return None

def determine_severity(code, name, platform):
    """Hata ismine ve koduna göre kritiklik seviyesi belirler."""
    name_u = name.upper()
    if "SUCCESS" in name_u or "OK" in name_u or "INFO" in name_u: return "Info"
    if "WARNING" in name_u or "PENDING" in name_u: return "Warning"
    if "FATAL" in name_u or "CRITICAL" in name_u or "PANIC" in name_u or platform == "bsod": return "Critical"
    return "Error"

def determine_products(code_hex, name, existing_tags, platform):
    products = set()
    safe_name = name if name else ""
    code_clean = code_hex.lower().replace('0x', '')
    
    if platform == "linux": products.add("Linux Kernel"); return list(products)
    if platform == "web": products.add("Web/API"); return list(products)
    if platform == "smtp": products.add("Exchange/Postfix"); return list(products)
    if platform == "database": products.add("PostgreSQL/SQL"); return list(products)
    if platform == "container": products.add("Docker/K8s"); return list(products)
    if platform == "bsod": products.add("BSOD/Crash"); products.add("Kernel"); return list(products)

    if safe_name.startswith("STATUS_") or safe_name.startswith("BUGCODE_"): products.add("Kernel/Driver")
    if code_clean.startswith("800f") or code_clean.startswith("8024") or "cbs" in safe_name.lower() or "wu_" in safe_name.lower():
        products.add("Windows Update"); products.add("DISM/CBS")
    if safe_name.startswith("WSA") or (code_clean.startswith("27") and len(code_clean) == 4):
        products.add("Winsock/TCP"); products.add("Network")

    if not products: products.add("System")
    return list(products)

def format_ts_object(obj):
    desc = obj.get('description', '').replace('"', "'").replace('\\', '\\\\').replace('\n', ' ')
    hint = json.dumps(obj.get("solutionHint")) if obj.get("solutionHint") else "undefined"
    doc_url = json.dumps(obj.get("docUrl")) if obj.get("docUrl") else "undefined"
    severity = json.dumps(obj.get("severity", "Error"))
    is_common = "true" if obj.get("isCommon") else "false"
    
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
    docUrl: {doc_url},
    severity: {severity},
    isCommon: {is_common},
    runbook: {runbook_str},
    likelySeenIn: {seen},
    products: {prods}
  }}"""