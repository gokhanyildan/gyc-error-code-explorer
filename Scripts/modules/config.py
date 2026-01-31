import os

# --- PATHS ---
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'data'))
OUTPUT_FILE = os.path.join(BASE_DIR, 'error-db.ts')
CUSTOM_FILE = os.path.join(BASE_DIR, 'custom-knowledge.json')

# --- SOURCE URLS ---
URLS = {
    "MS_BSOD": "https://learn.microsoft.com/en-us/windows-hardware/drivers/debugger/bug-check-code-reference2",
    "WIN_WIN32": "https://raw.githubusercontent.com/tpn/winsdk-10/master/Include/10.0.10240.0/shared/winerror.h",
    "WIN_UPDATE": "https://raw.githubusercontent.com/tpn/winsdk-10/master/Include/10.0.10240.0/um/wuerror.h",
    "WIN_NTSTATUS": "https://raw.githubusercontent.com/tpn/winsdk-10/master/Include/10.0.10240.0/shared/ntstatus.h",
    "LINUX_BASE": "https://raw.githubusercontent.com/torvalds/linux/master/include/uapi/asm-generic/errno-base.h",
    "LINUX_ADV": "https://raw.githubusercontent.com/torvalds/linux/master/include/uapi/asm-generic/errno.h",
    "HTTP": "https://www.iana.org/assignments/http-status-codes/http-status-codes-1.csv",
    "DNS": "https://www.iana.org/assignments/dns-parameters/dns-parameters-6.csv",
    "SMTP": "https://www.iana.org/assignments/smtp-enhanced-status-codes/smtp-enhanced-status-codes-1.csv",
    "POSTGRES": "https://raw.githubusercontent.com/postgres/postgres/master/src/backend/utils/errcodes.txt",
    
    # NEW SOURCES (PHASE 1)
    "K8S_TYPES": "https://raw.githubusercontent.com/kubernetes/api/master/core/v1/types.go",
    "K8S_ERRORS": "https://raw.githubusercontent.com/kubernetes/apimachinery/master/pkg/api/errors/errors.go",
    "NODEJS": "https://nodejs.org/dist/latest-v20.x/docs/api/all.json"
}

# --- REGEX PATTERNS ---
REGEX = {
    "BSOD_LINK": r'bug-check-(0x[0-9a-fA-F]+)(?:-+([a-zA-Z0-9-]+))?',
    "WIN_DEFINE": r'^\s*#define\s+([A-Z0-9_]+)\s+.*?((?:0x[0-9A-Fa-f]+|\-?\d+)L?)',
    "LINUX_DEFINE": r'^\s*#define\s+([A-Z0-9]+)\s+(\d+)\s*\/\*\s*(.*?)\s*\*\/'
    # K8s ve Node.js için özel parser yazacağımız için buraya regex eklemiyoruz.
}