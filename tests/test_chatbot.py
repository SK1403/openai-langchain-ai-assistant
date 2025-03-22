#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
##
# Description:-
#
#       Automated Unit Test Suite for Azure OpenAI Assistant.
#       Validates bot initialization, persona switching, ADF and Databricks mocks.
#
##
# Development date    Developed by       Comments
# ----------------    ------------       ---------
# 14/02/2025          Saddam Khan        Initial implementation
# 22/03/2025          Saddam Khan        Added unit tests for Azure tool invocation and memory
#
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

"""
Explanation:
    This test module validates the core functional capabilities of the
    AzureOpenAIChatbot, persona management, and Azure client integrations.

:param None: Test module.
:return None: Test case suite execution.
"""

import unittest
from chatbot import AzureOpenAIChatbot
from personas import PERSONAS, get_persona
from utils.adf_client import AzureDataFactoryClient
from utils.databricks_client import AzureDatabricksClient
from utils.auth import verify_azure_openai_credentials


class TestAzureChatbot(unittest.TestCase):
    """
    Explanation:
        Unit test cases exercising AzureOpenAIChatbot state and client methods.

    :return None: Test runner verification.
    """

    def test_initialization_without_crash(self):
        """Chatbot should initialize cleanly even before API credentials are provided."""
        bot = AzureOpenAIChatbot()
        self.assertIsNotNone(bot)
        self.assertEqual(bot.persona_id, "azure_architect")
        self.assertIn(bot.active_provider, ["Azure OpenAI (gpt-4o)", "OpenAI (gpt-4o)", "Pending API Credentials"])

    def test_persona_switching(self):
        """Verify dynamic switching between specialized enterprise personas."""
        bot = AzureOpenAIChatbot(persona_id="azure_architect")
        self.assertEqual(bot.persona.name, "Azure Cloud Solutions Architect")

        bot.set_persona("adf_engineer")
        self.assertEqual(bot.persona.name, "Azure Data Factory (ADF) Specialist")

        bot.set_persona("databricks_engineer")
        self.assertEqual(bot.persona.name, "Azure Databricks & Spark Engineer")

        bot.set_persona("analytics_advisor")
        self.assertEqual(bot.persona.name, "Azure Lakehouse & AI Strategist")

    def test_adf_client_pipeline_operations(self):
        """Verify ADF pipeline listing, execution triggering, and telemetry."""
        client = AzureDataFactoryClient()
        pipelines = client.list_pipelines()
        self.assertGreaterEqual(len(pipelines), 3)

        pipe_names = [p["name"] for p in pipelines]
        self.assertIn("PL_Raw_To_Bronze_Ingest", pipe_names)

        # Trigger a test run
        res = client.trigger_pipeline("PL_Raw_To_Bronze_Ingest")
        self.assertTrue(res["run_id"].startswith("adf-run-"))
        self.assertEqual(res["status"], "InProgress")

        # Verify recent runs contains the new run
        recent = client.list_recent_runs()
        self.assertEqual(recent[0]["run_id"], res["run_id"])

    def test_databricks_client_clusters_and_jobs(self):
        """Verify Databricks cluster listing and job execution."""
        client = AzureDatabricksClient()
        clusters = client.list_clusters()
        self.assertGreaterEqual(len(clusters), 3)

        summary = client.get_workspace_summary()
        self.assertGreaterEqual(summary["running_clusters"], 1)
        self.assertGreaterEqual(summary["total_active_workers"], 2)

        jobs = client.list_jobs()
        self.assertGreaterEqual(len(jobs), 2)

        run_res = client.run_job(jobs[0]["job_id"])
        self.assertEqual(run_res["status"], "RUNNING")

    def test_graceful_stream_chat_fallback(self):
        """Verify that streaming yields a clear message when credentials are not configured."""
        bot = AzureOpenAIChatbot(azure_endpoint="", azure_api_key="", openai_api_key="")
        chunks = list(bot.stream_chat("What is an Azure Landing Zone?", session_id="test_session"))
        full_msg = "".join(chunks)
        self.assertIn("API Credentials Required", full_msg)

if __name__ == "__main__":
    unittest.main()
