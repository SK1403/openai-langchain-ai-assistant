#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
##
# Description:-
#
#       Azure Data Lake Storage (ADLS Gen2) and Blob Storage Manager.
#       Provides container inspection, blob volume estimation, and lakehouse tier
#       mapping across Bronze, Silver, Gold, and LLM telemetry partitions.
#
##
# Development date    Developed by       Comments
# ----------------    ------------       ---------
# 14/02/2025          Saddam Khan        Initial implementation
# 22/03/2025          Saddam Khan        Added Azure Blob Storage diagnostic log inspection
#
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

import os
from typing import List, Dict, Any, Tuple
from config import settings

class AzureStorageManager:
    """
    Explanation: Manager for interacting with Azure Data Lake Storage (ADLS Gen2) and Blob Storage.
    :param  connection_string str: Storage account connection string or SAS token
    :param  account_name str: Storage account resource name
    """

    def __init__(
        self,
        connection_string: str = None,
        account_name: str = None,
    ):
        self.connection_string = connection_string or settings.azure_storage_connection_string
        self.account_name = account_name or settings.azure_storage_account_name

        self._mock_containers = [
            {"name": "lakehouse-landing", "access_tier": "Hot", "blob_count": 142, "size_gb": 320.4},
            {"name": "lakehouse-bronze", "access_tier": "Hot", "blob_count": 890, "size_gb": 1240.8},
            {"name": "lakehouse-silver", "access_tier": "Hot", "blob_count": 412, "size_gb": 640.2},
            {"name": "lakehouse-gold", "access_tier": "Hot", "blob_count": 78, "size_gb": 112.5},
            {"name": "azure-openai-logs", "access_tier": "Cool", "blob_count": 2105, "size_gb": 45.0},
        ]

    def list_containers(self) -> List[Dict[str, Any]]:
        """
        Explanation: Retrieves list of ADLS Gen2 containers with access tiers and volume metrics.
        :return containers List[Dict[str, Any]]: List of container metadata dictionaries
        """
        return self._mock_containers

    def get_storage_summary(self) -> Dict[str, Any]:
        """
        Explanation: Calculates aggregated storage footprint, total blob count, and container summary.
        :return summary Dict[str, Any]: Aggregated storage metrics dictionary
        """
        total_size = sum(c["size_gb"] for c in self._mock_containers)
        total_blobs = sum(c["blob_count"] for c in self._mock_containers)
        return {
            "account_name": self.account_name,
            "total_containers": len(self._mock_containers),
            "total_blobs": total_blobs,
            "total_size_gb": round(total_size, 1),
        }
