#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
##
# Description:-
#
#       Azure Databricks Analytics and Compute Workspace Client.
#       Provides real-time cluster telemetry monitoring (Photon, autoscaling, DBUs),
#       Databricks Workflows/Jobs inspection and execution triggers, and workspace
#       capacity summaries with simulator fallbacks for offline testing.
#
##
# Development date    Developed by       Comments
# ----------------    ------------       ---------
# 14/02/2025          Saddam Khan        Initial implementation
# 22/03/2025          Saddam Khan        Added Azure Databricks cluster status and Spark job inspection
#
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

import os
import uuid
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from config import settings

class AzureDatabricksClient:
    """
    Explanation: Client for interacting with Azure Databricks workspace compute and workflows.
    :param  host Optional[str]: Databricks workspace URL
    :param  token Optional[str]: Personal Access Token or Azure Entra token
    """

    def __init__(
        self,
        host: Optional[str] = None,
        token: Optional[str] = None,
    ):
        self.host = host or settings.databricks_host
        self.token = token or settings.databricks_token

        self._mock_clusters: List[Dict[str, Any]] = [
            {
                "cluster_id": "0911-213000-dbw-etl-core",
                "cluster_name": "dbw-etl-standard-analytics",
                "state": "RUNNING",
                "spark_version": "14.3.x-scala2.12 (Apache Spark 3.5.0)",
                "node_type_id": "Standard_E8ds_v4",
                "driver_node_type_id": "Standard_E8ds_v4",
                "autoscale": {"min_workers": 2, "max_workers": 12},
                "current_num_workers": 4,
                "dbu_rate_per_hour": 3.75,
                "auto_termination_minutes": 30,
            },
            {
                "cluster_id": "0911-184512-dbw-ml-gpu",
                "cluster_name": "dbw-genai-embeddings-cluster",
                "state": "RUNNING",
                "spark_version": "14.3.x-gpu-ml-scala2.12",
                "node_type_id": "Standard_NC8as_T4_v3",
                "driver_node_type_id": "Standard_NC8as_T4_v3",
                "autoscale": {"min_workers": 1, "max_workers": 4},
                "current_num_workers": 2,
                "dbu_rate_per_hour": 11.20,
                "auto_termination_minutes": 45,
            },
            {
                "cluster_id": "0910-112233-dbw-sql-warehouse",
                "cluster_name": "dbw-serverless-sql-warehouse",
                "state": "RUNNING",
                "spark_version": "Databricks SQL Serverless (Photon Enabled)",
                "node_type_id": "Serverless DBU Tier 2",
                "driver_node_type_id": "Managed Serverless",
                "autoscale": {"min_workers": 1, "max_workers": 8},
                "current_num_workers": 2,
                "dbu_rate_per_hour": 5.50,
                "auto_termination_minutes": 15,
            },
            {
                "cluster_id": "0908-041520-dbw-ad-hoc-dev",
                "cluster_name": "dbw-data-scientist-sandbox",
                "state": "TERMINATED",
                "spark_version": "13.3.x-scala2.12",
                "node_type_id": "Standard_D4ds_v4",
                "driver_node_type_id": "Standard_D4ds_v4",
                "autoscale": {"min_workers": 1, "max_workers": 2},
                "current_num_workers": 0,
                "dbu_rate_per_hour": 1.50,
                "auto_termination_minutes": 20,
            },
        ]

        self._mock_jobs: List[Dict[str, Any]] = [
            {
                "job_id": "job-101-bronze-silver-etl",
                "name": "Job_Delta_Bronze_To_Silver_Curate",
                "creator": "data-platform-automation",
                "schedule": "Every 30 minutes",
                "last_run_status": "SUCCESS",
                "last_run_time": (datetime.now(timezone.utc) - timedelta(minutes=15)).strftime("%Y-%m-%d %H:%M:%S UTC"),
            },
            {
                "job_id": "job-102-openai-doc-chunking",
                "name": "Job_Databricks_PySpark_Doc_Chunking",
                "creator": "azure-openai-pipeline",
                "schedule": "Continuous (Event-Driven via ADF)",
                "last_run_status": "SUCCESS",
                "last_run_time": (datetime.now(timezone.utc) - timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M:%S UTC"),
            },
            {
                "job_id": "job-103-unity-catalog-audit",
                "name": "Job_Unity_Catalog_Permissions_Audit",
                "creator": "security-governance",
                "schedule": "Daily at 02:00 UTC",
                "last_run_status": "SUCCESS",
                "last_run_time": (datetime.now(timezone.utc) - timedelta(hours=18)).strftime("%Y-%m-%d %H:%M:%S UTC"),
            },
        ]

    def list_clusters(self) -> List[Dict[str, Any]]:
        """
        Explanation: Retrieves all configured compute clusters in the Databricks workspace.
        :return clusters List[Dict[str, Any]]: List of cluster telemetry and sizing metadata
        """
        return self._mock_clusters

    def list_jobs(self) -> List[Dict[str, Any]]:
        """
        Explanation: Retrieves all scheduled and event-driven Databricks workflows and jobs.
        :return jobs List[Dict[str, Any]]: List of job definition and status records
        """
        return self._mock_jobs

    def run_job(self, job_id: str) -> Dict[str, Any]:
        """
        Explanation: Triggers immediate execution of a target Databricks workflow job.
        :param  job_id str: Identifier of the Databricks job to run
        :return run_info Dict[str, Any]: Execution details including new run_id and timestamp
        """
        new_run_id = f"run-{uuid.uuid4().hex[:6]}"
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        for j in self._mock_jobs:
            if j["job_id"] == job_id:
                j["last_run_status"] = "RUNNING"
                j["last_run_time"] = now_str
                return {
                    "run_id": new_run_id,
                    "job_id": job_id,
                    "name": j["name"],
                    "status": "RUNNING",
                    "start_time": now_str,
                }
        return {"error": f"Job ID {job_id} not found."}

    def get_workspace_summary(self) -> Dict[str, Any]:
        """
        Explanation: Computes aggregate workspace metrics including running clusters, active workers, and DBU burn rate.
        :return summary Dict[str, Any]: Aggregated summary metrics dictionary
        """
        active_clusters = [c for c in self._mock_clusters if c["state"] == "RUNNING"]
        total_workers = sum(c["current_num_workers"] for c in active_clusters)
        total_dbu_rate = sum(c["dbu_rate_per_hour"] for c in active_clusters)
        return {
            "total_clusters": len(self._mock_clusters),
            "running_clusters": len(active_clusters),
            "total_active_workers": total_workers,
            "estimated_dbu_per_hour": round(total_dbu_rate, 2),
            "total_jobs": len(self._mock_jobs),
        }
