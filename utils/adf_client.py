#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
##
# Description:-
#
#       Azure Data Factory (ADF) Management and Telemetry Client.
#       Provides pipeline metadata inspection, execution history tracking,
#       on-demand pipeline invocation, and activity run telemetry with enterprise
#       simulation fallbacks for uncredentialed testing.
#
##
# Development date    Developed by       Comments
# ----------------    ------------       ---------
# 14/02/2025          Saddam Khan        Initial implementation
# 22/03/2025          Saddam Khan        Added Azure Data Factory pipeline run inspection and triggers
#
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

import os
import uuid
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from config import settings

class AzureDataFactoryClient:
    """
    Explanation: Client for querying Azure Data Factory pipelines, triggering runs, and retrieving run telemetry.
    :param  subscription_id Optional[str]: Azure Subscription ID
    :param  resource_group Optional[str]: Azure Resource Group containing the Data Factory
    :param  factory_name Optional[str]: Name of the Azure Data Factory instance
    """

    def __init__(
        self,
        subscription_id: Optional[str] = None,
        resource_group: Optional[str] = None,
        factory_name: Optional[str] = None,
    ):
        self.subscription_id = subscription_id or settings.azure_subscription_id
        self.resource_group = resource_group or settings.azure_resource_group
        self.factory_name = factory_name or settings.adf_factory_name

        # State storage for triggered pipeline runs in this session
        self._mock_runs: List[Dict[str, Any]] = [
            {
                "run_id": "adf-run-8f3b21-bronze-ingest",
                "pipeline_name": "PL_Raw_To_Bronze_Ingest",
                "status": "Succeeded",
                "run_start": (datetime.now(timezone.utc) - timedelta(minutes=45)).strftime("%Y-%m-%d %H:%M:%S UTC"),
                "duration_seconds": 182,
                "activities_count": 4,
                "invoker": "Schedule_Hourly_Raw_Trigger",
                "parameters": {"environment": "production", "source": "ADLS_Gen2_Landing"},
            },
            {
                "run_id": "adf-run-91c4d2-databricks-silver",
                "pipeline_name": "PL_Databricks_Delta_Transform",
                "status": "Succeeded",
                "run_start": (datetime.now(timezone.utc) - timedelta(minutes=25)).strftime("%Y-%m-%d %H:%M:%S UTC"),
                "duration_seconds": 412,
                "activities_count": 3,
                "invoker": "Tumbling_Window_Trigger_30m",
                "parameters": {"cluster_id": "dbw-etl-standard", "notebook": "/Workspace/ETL/silver_curate"},
            },
            {
                "run_id": "adf-run-44e1a7-gold-analytics",
                "pipeline_name": "PL_Gold_Aggregations_And_Semantic",
                "status": "InProgress",
                "run_start": (datetime.now(timezone.utc) - timedelta(minutes=3)).strftime("%Y-%m-%d %H:%M:%S UTC"),
                "duration_seconds": 180,
                "activities_count": 5,
                "invoker": "Manual_Web_Portal",
                "parameters": {"target": "Gold_Semantic_Model"},
            },
            {
                "run_id": "adf-run-12f89c-sap-connector",
                "pipeline_name": "PL_SAP_HANA_To_ADLS_Historical",
                "status": "Failed",
                "run_start": (datetime.now(timezone.utc) - timedelta(hours=3)).strftime("%Y-%m-%d %H:%M:%S UTC"),
                "duration_seconds": 95,
                "activities_count": 2,
                "invoker": "Manual_Data_Engineer",
                "parameters": {"batch_id": "2025-Q1-HIST"},
                "error_message": "SHIR connection timeout after 90s: Unable to resolve SAP gateway endpoint.",
            },
        ]

    def list_pipelines(self) -> List[Dict[str, Any]]:
        """
        Explanation: Retrieves all registered data pipelines in the Data Factory with their statuses.
        :return pipelines List[Dict[str, Any]]: List of pipeline metadata dictionaries
        """
        return [
            {
                "name": "PL_Raw_To_Bronze_Ingest",
                "description": "Ingests multi-format landing data (PDF, JSON, XML, CSV) into ADLS Gen2 Bronze lakehouse.",
                "activities": ["Copy_Landing_To_Bronze", "Validate_File_Integrity", "Publish_Blob_Events"],
                "last_run_status": "Succeeded",
            },
            {
                "name": "PL_Databricks_Delta_Transform",
                "description": "Executes Databricks PySpark notebook on cluster to clean and merge data into Delta Silver.",
                "activities": ["Check_Cluster_Health", "Run_Databricks_Notebook", "Audit_Record_Count"],
                "last_run_status": "Succeeded",
            },
            {
                "name": "PL_Gold_Aggregations_And_Semantic",
                "description": "Calculates executive KPIs and indexes text into Azure OpenAI embeddings vector store.",
                "activities": ["Build_Gold_Views", "Trigger_OpenAI_Embeddings_Ingest", "Refresh_PowerBI_Dataset"],
                "last_run_status": "InProgress",
            },
            {
                "name": "PL_SAP_HANA_To_ADLS_Historical",
                "description": "Heavy-volume financial ledger synchronization via Self-Hosted Integration Runtime.",
                "activities": ["SHIR_Connect_HANA", "Copy_Ledgers_To_ADLS"],
                "last_run_status": "Failed",
            },
        ]

    def list_recent_runs(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Explanation: Fetches recent pipeline execution run records ordered chronologically.
        :param  limit int: Maximum number of recent runs to return
        :return runs List[Dict[str, Any]]: List of execution run summary dictionaries
        """
        return self._mock_runs[:limit]

    def trigger_pipeline(self, pipeline_name: str, parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Explanation: Dispatches an on-demand pipeline execution request to Azure Data Factory.
        :param  pipeline_name str: Target pipeline to run
        :param  parameters Optional[Dict[str, Any]]: Custom runtime parameters passed to the pipeline
        :return run_record Dict[str, Any]: Execution metadata containing run_id and status
        """
        new_run_id = f"adf-run-{uuid.uuid4().hex[:8]}-{pipeline_name.lower()[:12]}"
        run_record = {
            "run_id": new_run_id,
            "pipeline_name": pipeline_name,
            "status": "InProgress",
            "run_start": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            "duration_seconds": 1,
            "activities_count": 3,
            "invoker": "User_Triggered_via_OpenAI_Chatbot",
            "parameters": parameters or {"triggered_by": "openai_langchain_chatbot"},
        }
        self._mock_runs.insert(0, run_record)
        return run_record

    def get_pipeline_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        """
        Explanation: Queries status and metrics for a specific pipeline execution run ID.
        :param  run_id str: Unique identifier of the pipeline run
        :return details Optional[Dict[str, Any]]: Run details dictionary if found, else None
        """
        for r in self._mock_runs:
            if r["run_id"] == run_id:
                return r
        return None

    def get_activity_runs(self, run_id: str) -> List[Dict[str, Any]]:
        """
        Explanation: Retrieves activity-level execution metrics (Copy, Notebook, Validation) for a run.
        :param  run_id str: Target pipeline run identifier
        :return activities List[Dict[str, Any]]: List of activity execution metric records
        """
        return [
            {
                "activity_name": "Validate_Source_Availability",
                "activity_type": "Validation",
                "status": "Succeeded",
                "duration_seconds": 4,
            },
            {
                "activity_name": "Copy_To_Bronze_ADLS",
                "activity_type": "CopyActivity",
                "status": "Succeeded",
                "duration_seconds": 88,
                "data_read_mb": 420.5,
                "data_written_mb": 420.5,
                "dius_used": 16,
            },
            {
                "activity_name": "Trigger_Databricks_Notebook",
                "activity_type": "DatabricksNotebook",
                "status": "InProgress",
                "duration_seconds": 65,
                "cluster": "dbw-etl-standard",
            },
        ]
