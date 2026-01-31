# --- CURATED & PREMIUM ERROR DATA ---
# isCommon: True -> Ana sayfada en üstte çıkar.

STATIC_DATA = {
    "container": {
        "137": {"name": "SIGKILL (OOMKilled)", "desc": "Container received SIGKILL. Usually indicates Out of Memory (OOM).", "solutionHint": "Check Docker memory limits and application leaks.", "isCommon": True},
        "139": {"name": "SIGSEGV", "desc": "Segmentation Fault. Invalid memory access.", "solutionHint": "Check for null pointer dereferences.", "isCommon": True}
    },
    "network": {
        "49": {"name": "LDAP_INVALID_CREDENTIALS", "desc": "Invalid Credentials for LDAP binding.", "solutionHint": "Verify service account password.", "isCommon": True},
        "53": {"name": "ECONNABORTED", "desc": "Software caused connection abort.", "isCommon": True},
        "111": {"name": "ECONNREFUSED", "desc": "Connection refused by the server.", "solutionHint": "Check if the service is running and listening on the port.", "isCommon": True}
    },
    "web": {
        "400": {"name": "HTTP_BAD_REQUEST", "desc": "The server cannot process the request due to a client error.", "isCommon": True},
        "401": {"name": "HTTP_UNAUTHORIZED", "desc": "Authentication is required and has failed or has not been provided.", "isCommon": True},
        "403": {"name": "HTTP_FORBIDDEN", "desc": "The server understood the request but refuses to authorize it.", "isCommon": True},
        "404": {"name": "HTTP_NOT_FOUND", "desc": "The requested resource could not be found.", "isCommon": True},
        "500": {"name": "HTTP_INTERNAL_SERVER_ERROR", "desc": "A generic error message, given when an unexpected condition was encountered.", "isCommon": True},
        "502": {"name": "HTTP_BAD_GATEWAY", "desc": "The server request was invalid or the upstream server returned an invalid response.", "isCommon": True},
        "503": {"name": "HTTP_SERVICE_UNAVAILABLE", "desc": "The server is currently unavailable (overloaded or down for maintenance).", "isCommon": True},
        "504": {"name": "HTTP_GATEWAY_TIMEOUT", "desc": "The server did not receive a timely response from the upstream server.", "isCommon": True}
    },
    "windows": {
        "0x5": {"name": "ERROR_ACCESS_DENIED", "desc": "Access is denied.", "solutionHint": "Run as Administrator or check folder permissions.", "isCommon": True},
        "0x2": {"name": "ERROR_FILE_NOT_FOUND", "desc": "The system cannot find the file specified.", "isCommon": True},
        "0x80070005": {"name": "E_ACCESSDENIED", "desc": "General access denied error.", "solutionHint": "Check permissions and antivirus settings.", "isCommon": True},
        "0x800f081f": {"name": "CBS_E_SOURCE_MISSING", "desc": "The source files could not be found.", "solutionHint": "Use DISM /RestoreHealth with a valid source.", "likelySeenIn": ["DISM"], "isCommon": True},
        "0x800f0906": {"name": "CBS_E_DOWNLOAD_FAILURE", "desc": "The source files could not be downloaded.", "solutionHint": "Check Internet/WSUS.", "likelySeenIn": ["DISM"], "isCommon": True}
    },
    "sccm": {
        "0x87d00607": {"name": "CCM_E_CONTENT_NOT_FOUND", "desc": "Content not found. The client cannot find the content on the Distribution Point.", "solutionHint": "Check Boundary Groups and distribute content to DP.", "isCommon": True},
        "0x87d00664": {"name": "CCM_E_UPDATES_HANDLER_JOB_LIMIT_REACHED", "desc": "Updates handler job limit reached.", "solutionHint": "Wait for other installations to finish or restart SMS Agent Host.", "isCommon": True},
        "0x87d00668": {"name": "CCM_E_UPDATES_HANDLER_WP_FAIL", "desc": "Software update failed to install.", "solutionHint": "Check WindowsUpdate.log and WUAHandler.log.", "isCommon": True},
        "0x87d00692": {"name": "CCM_E_GRPNOTFOUND", "desc": "Group not found. Policy might be missing.", "solutionHint": "Initiate Machine Policy Retrieval & Evaluation Cycle.", "isCommon": True},
        "0x80070002": {"name": "ERROR_FILE_NOT_FOUND", "desc": "System cannot find the file specified (Task Sequence common error).", "solutionHint": "Check 'Run as' account permissions and network access account.", "isCommon": True}
    },
    "bsod": {
        "0x0000000a": {"name": "IRQL_NOT_LESS_OR_EQUAL", "desc": "Driver accessed invalid memory address.", "solutionHint": "Update drivers.", "isCommon": True},
        "0x0000003b": {"name": "SYSTEM_SERVICE_EXCEPTION", "desc": "Exception in privileged code.", "solutionHint": "Update GPU/Chipset drivers.", "isCommon": True},
        "0x00000050": {"name": "PAGE_FAULT_IN_NONPAGED_AREA", "desc": "Invalid system memory referenced.", "solutionHint": "Check RAM and Antivirus.", "isCommon": True},
        "0x00000124": {"name": "WHEA_UNCORRECTABLE_ERROR", "desc": "Fatal hardware error.", "solutionHint": "Check cooling and voltage.", "isCommon": True},
        "0xc000021a": {"name": "STATUS_SYSTEM_PROCESS_TERMINATED", "desc": "Crucial user-mode subsystem failed.", "solutionHint": "System Restore or uninstall updates.", "isCommon": True}
    }
    
}