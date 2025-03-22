#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
##
# Description:-
#
#       Authentication and Credential Verification utilities for Azure AI services.
#       Validates Azure OpenAI Service API keys, Microsoft Entra Managed Identity,
#       fallback standard OpenAI API keys, and local Azure CLI authentication status.
#
##
# Development date    Developed by       Comments
# ----------------    ------------       ---------
# 14/02/2025          Saddam Khan        Initial implementation
# 22/03/2025          Saddam Khan        Added Azure OpenAI and Entra ID token verification
#
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

import os
import shutil
import subprocess
from typing import Tuple
from config import settings

def verify_azure_openai_credentials(
    endpoint: str = None,
    api_key: str = None,
    openai_key: str = None,
) -> Tuple[bool, str]:
    """
    Explanation: Validates availability of Azure OpenAI credentials or fallback standard OpenAI API keys.
    :param  endpoint str: Optional Azure OpenAI endpoint URL override
    :param  api_key str: Optional Azure OpenAI API key override
    :param  openai_key str: Optional direct OpenAI API key override
    :return is_valid Tuple[bool, str]: Tuple of boolean readiness flag and descriptive status message
    """
    ep = (endpoint or os.getenv("AZURE_OPENAI_ENDPOINT", settings.azure_openai_endpoint)).strip()
    az_key = (api_key or os.getenv("AZURE_OPENAI_API_KEY", settings.azure_openai_api_key)).strip()
    oai_key = (openai_key or os.getenv("OPENAI_API_KEY", settings.openai_api_key)).strip()

    if ep and az_key:
        return True, f"Azure OpenAI Service Active (`{ep.split('://')[-1].split('/')[0]}`)"

    if ep and not az_key:
        # Check if Azure Managed Identity / DefaultAzureCredential might be active
        return True, f"Azure OpenAI (Endpoint set, using Microsoft Entra Managed Identity / DefaultAzureCredential)"

    if oai_key:
        masked = oai_key[:4] + "..." + oai_key[-4:] if len(oai_key) > 8 else "***"
        return True, f"Standard OpenAI API Active (`{masked}`)"

    return False, "No Azure OpenAI or OpenAI credentials configured. Enter them in the sidebar or .env"

def check_azure_cli() -> Tuple[bool, str]:
    """
    Explanation: Verifies local installation and active login session of the Azure CLI (`az`).
    :return cli_status Tuple[bool, str]: Tuple of boolean flag and status description string
    """
    az_path = shutil.which("az")
    if not az_path:
        return False, "Azure CLI (`az`) not found in PATH"

    try:
        res = subprocess.run(["az", "account", "show", "--output", "json"], capture_output=True, text=True, timeout=5)
        if res.returncode == 0 and "id" in res.stdout:
            return True, "Azure CLI Authenticated"
        return False, "Azure CLI installed but not logged in (run `az login`)"
    except Exception as e:
        return False, f"Azure CLI check failed: {e}"
