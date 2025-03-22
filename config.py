#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
##
# Description:-
#
#       Enterprise Configuration module for Azure OpenAI, ADF, and Databricks.
#       Encapsulates environment variables, authentication settings, Azure resource
#       identifiers, and model generation hyperparameters with dataclass validation.
#
##
# Development date    Developed by       Comments
# ----------------    ------------       ---------
# 14/02/2025          Saddam Khan        Initial implementation
# 22/03/2025          Saddam Khan        Added Azure OpenAI and Databricks endpoint settings
#
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class AzureOpenAISettings:
    """
    Explanation: Configuration dataclass for Azure OpenAI Service, standard OpenAI, ADF, and Databricks.
    :param  platform_mode str: Deployment mode ("azure" or "openai")
    :param  azure_openai_endpoint str: Base endpoint URL for Azure OpenAI Service
    :param  azure_openai_api_key str: API authorization key for Azure OpenAI Service
    :param  azure_openai_api_version str: REST API version date
    :param  azure_chat_deployment str: Model deployment name in Azure AI Foundry
    :param  openai_api_key str: Standard OpenAI API secret key
    :param  openai_model str: Fallback model identifier for standard OpenAI
    :param  azure_subscription_id str: Azure Subscription GUID
    :param  azure_resource_group str: Azure Resource Group name
    :param  adf_factory_name str: Azure Data Factory resource name
    :param  azure_tenant_id str: Microsoft Entra Tenant ID
    :param  azure_client_id str: Service Principal Application Client ID
    :param  azure_client_secret str: Service Principal Client Secret
    :param  databricks_host str: Azure Databricks workspace URL
    :param  databricks_token str: Databricks Personal Access Token (PAT)
    :param  databricks_cluster_id str: Target Databricks cluster identifier
    :param  azure_storage_connection_string str: ADLS Gen2 connection string
    :param  azure_storage_account_name str: Azure Storage Account name
    :param  azure_storage_container str: Primary lakehouse container name
    :param  temperature float: Default model temperature (0.0 to 1.0)
    :param  max_output_tokens int: Default maximum tokens for completion output
    :param  default_persona str: Default persona slug identifier
    """

    # Platform Mode: "azure" (Azure OpenAI Service) or "openai" (Direct OpenAI API)
    platform_mode: str = os.getenv("PLATFORM_MODE", "azure")

    # Azure OpenAI Service Configuration
    azure_openai_endpoint: str = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    azure_openai_api_key: str = os.getenv("AZURE_OPENAI_API_KEY", "")
    azure_openai_api_version: str = os.getenv("AZURE_OPENAI_API_VERSION", "2024-06-01")
    azure_chat_deployment: str = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT", "gpt-4o")

    # Standard OpenAI Fallback / Direct API
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o")

    # Azure Data Factory (ADF) Configuration
    azure_subscription_id: str = os.getenv("AZURE_SUBSCRIPTION_ID", "sub-prod-enterprise-001")
    azure_resource_group: str = os.getenv("AZURE_RESOURCE_GROUP", "rg-enterprise-data-prod")
    adf_factory_name: str = os.getenv("ADF_FACTORY_NAME", "adf-enterprise-analytics-prod")
    azure_tenant_id: str = os.getenv("AZURE_TENANT_ID", "")
    azure_client_id: str = os.getenv("AZURE_CLIENT_ID", "")
    azure_client_secret: str = os.getenv("AZURE_CLIENT_SECRET", "")

    # Azure Databricks Configuration
    databricks_host: str = os.getenv("DATABRICKS_HOST", "https://adb-enterprise-analytics.azuredatabricks.net")
    databricks_token: str = os.getenv("DATABRICKS_TOKEN", "")
    databricks_cluster_id: str = os.getenv("DATABRICKS_CLUSTER_ID", "dbw-cluster-prod-01")

    # Azure Data Lake Storage (ADLS Gen2)
    azure_storage_connection_string: str = os.getenv("AZURE_STORAGE_CONNECTION_STRING", "")
    azure_storage_account_name: str = os.getenv("AZURE_STORAGE_ACCOUNT_NAME", "adlsgen2prodstore")
    azure_storage_container: str = os.getenv("AZURE_STORAGE_CONTAINER", "lakehouse-bronze")

    # Model Hyperparameters
    temperature: float = float(os.getenv("MODEL_TEMPERATURE", "0.3"))
    max_output_tokens: int = int(os.getenv("MAX_OUTPUT_TOKENS", "2048"))
    default_persona: str = os.getenv("DEFAULT_PERSONA", "azure_architect")

settings = AzureOpenAISettings()
