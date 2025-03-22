#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
##
# Description:-
#
#       Enterprise Conversational AI Chatbot Engine for Azure OpenAI & OpenAI.
#       Provides dynamic persona switching, multi-turn conversation memory,
#       live Azure telemetry context injection (ADF pipelines & Databricks clusters),
#       and streaming token generation using LangChain.
#
##
# Development date    Developed by       Comments
# ----------------    ------------       ---------
# 14/02/2025          Saddam Khan        Initial implementation
# 22/03/2025          Saddam Khan        Added Azure OpenAI tool routing and multi-turn memory
#
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

import os
from typing import Generator, Dict, Any, List, Optional
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.chat_history import InMemoryChatMessageHistory, BaseChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.messages import BaseMessage

from config import settings
from personas import get_persona, Persona
from utils.adf_client import AzureDataFactoryClient
from utils.databricks_client import AzureDatabricksClient

class AzureOpenAIChatbot:
    """
    Explanation: Enterprise Conversational AI Engine using Azure OpenAI Service & OpenAI with LangChain.
                 Supports multi-turn memory, dynamic persona switching, real-time platform context
                 injection from ADF and Databricks, and token streaming.
    :param  persona_id str: Identifier slug of the active enterprise persona
    :param  chat_deployment Optional[str]: Azure OpenAI model deployment identifier
    :param  openai_model Optional[str]: Standard OpenAI fallback model name
    :param  azure_endpoint Optional[str]: Azure OpenAI Service endpoint URL
    :param  azure_api_key Optional[str]: Azure OpenAI Service API key
    :param  openai_api_key Optional[str]: Direct OpenAI API authorization key
    :param  temperature Optional[float]: Sampling temperature controlling response creativity
    :param  max_tokens Optional[int]: Maximum generation tokens per completion
    :param  system_instruction Optional[str]: Custom override for the persona system instruction
    """

    def __init__(
        self,
        persona_id: str = "azure_architect",
        chat_deployment: Optional[str] = None,
        openai_model: Optional[str] = None,
        azure_endpoint: Optional[str] = None,
        azure_api_key: Optional[str] = None,
        openai_api_key: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        system_instruction: Optional[str] = None,
    ):
        self.persona_id = persona_id
        self.persona: Persona = get_persona(persona_id)
        self.chat_deployment = chat_deployment or settings.azure_chat_deployment
        self.openai_model = openai_model or settings.openai_model
        self.azure_endpoint = azure_endpoint.strip() if azure_endpoint else settings.azure_openai_endpoint
        self.azure_api_key = azure_api_key.strip() if azure_api_key else settings.azure_openai_api_key
        self.openai_api_key = openai_api_key.strip() if openai_api_key else settings.openai_api_key
        self.temperature = temperature if temperature is not None else settings.temperature
        self.max_tokens = max_tokens or settings.max_output_tokens
        self.custom_system_instruction = system_instruction

        # In-memory session store: session_id -> InMemoryChatMessageHistory
        self._session_store: Dict[str, InMemoryChatMessageHistory] = {}

        # Azure Platform Clients
        self.adf_client = AzureDataFactoryClient()
        self.databricks_client = AzureDatabricksClient()

        self.llm = None
        self.active_provider = "Uninitialized"
        self.conversational_chain = None

        self._init_llm()
        self._build_chain()

    def _init_llm(self):
        """
        Explanation: Initializes LLM client using Azure OpenAI Service or standard OpenAI API.
                     Falls back cleanly to an uninitialized state if credentials are missing.
        :return None: Updates internal llm instance and active_provider label
        """
        ep = self.azure_endpoint or os.getenv("AZURE_OPENAI_ENDPOINT", settings.azure_openai_endpoint)
        az_key = self.azure_api_key or os.getenv("AZURE_OPENAI_API_KEY", settings.azure_openai_api_key)
        oai_key = self.openai_api_key or os.getenv("OPENAI_API_KEY", settings.openai_api_key)

        # 1. Try Azure OpenAI Service
        if ep and az_key:
            try:
                from langchain_openai import AzureChatOpenAI
                self.llm = AzureChatOpenAI(
                    azure_deployment=self.chat_deployment,
                    azure_endpoint=ep,
                    api_key=az_key,
                    api_version=settings.azure_openai_api_version,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                )
                self.active_provider = f"Azure OpenAI ({self.chat_deployment})"
                return
            except Exception:
                pass

        # 2. Try Standard OpenAI API
        if oai_key:
            try:
                from langchain_openai import ChatOpenAI
                self.llm = ChatOpenAI(
                    model=self.openai_model,
                    api_key=oai_key,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                )
                self.active_provider = f"OpenAI ({self.openai_model})"
                return
            except Exception:
                pass

        # Unconfigured state (UI will prompt cleanly)
        self.llm = None
        self.active_provider = "Pending API Credentials"

    def _build_chain(self):
        """
        Explanation: Builds the ChatPromptTemplate and binds RunnableWithMessageHistory for conversational state.
        :return None: Configures internal conversational_chain
        """
        if self.llm is None:
            self.conversational_chain = None
            return

        active_instruction = self.custom_system_instruction or self.persona.system_instruction

        self.prompt = ChatPromptTemplate.from_messages([
            ("system", active_instruction),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{input}"),
        ])

        self.chain = self.prompt | self.llm

        self.conversational_chain = RunnableWithMessageHistory(
            self.chain,
            self._get_session_history,
            input_messages_key="input",
            history_messages_key="history",
        )

    def _get_session_history(self, session_id: str) -> BaseChatMessageHistory:
        """
        Explanation: Retrieves or creates an in-memory session history buffer for a given session ID.
        :param  session_id str: Unique identifier of the conversation session
        :return history BaseChatMessageHistory: In-memory chat message history
        """
        if session_id not in self._session_store:
            self._session_store[session_id] = InMemoryChatMessageHistory()
        return self._session_store[session_id]

    def set_persona(self, persona_id: str) -> None:
        """
        Explanation: Switches active persona dynamically and rebuilds prompt template.
        :param  persona_id str: Key for the target persona
        :return None: Updates persona and chain
        """
        self.persona_id = persona_id
        self.persona = get_persona(persona_id)
        self.custom_system_instruction = None
        self._build_chain()

    def set_temperature(self, temp: float) -> None:
        """
        Explanation: Updates temperature hyperparameter and re-initializes LLM client.
        :param  temp float: New temperature value (0.0 to 1.0)
        :return None: Re-initializes LLM and chain
        """
        self.temperature = temp
        self._init_llm()
        self._build_chain()

    def chat(self, user_input: str, session_id: str = "default_session") -> str:
        """
        Explanation: Synchronously submits user message and returns complete answer string.
        :param  user_input str: Natural language question or command
        :param  session_id str: Session identifier for multi-turn history
        :return response str: Assistant response content
        """
        if self.conversational_chain is None:
            return (
                "🔑 **API Credentials Required**\n\n"
                "Please configure your **Azure OpenAI Endpoint & API Key** (or standard OpenAI Key) "
                "in the sidebar or in your `.env` file to start chatting."
            )

        response = self.conversational_chain.invoke(
            {"input": user_input},
            config={"configurable": {"session_id": session_id}},
        )
        return response.content

    def stream_chat(
        self,
        user_input: str,
        session_id: str = "default_session",
        include_platform_context: bool = False,
    ) -> Generator[str, None, None]:
        """
        Explanation: Streams token chunks in real time, optionally injecting Azure platform telemetry snapshot.
        :param  user_input str: Natural language input prompt
        :param  session_id str: Session identifier for multi-turn history
        :param  include_platform_context bool: Whether to append live ADF/Databricks telemetry
        :return generator Generator[str, None, None]: Token stream chunks
        """
        if self.conversational_chain is None:
            yield (
                "🔑 **API Credentials Required**\n\n"
                "Please provide your **Azure OpenAI Endpoint & API Key** (or standard OpenAI API Key) "
                "in the sidebar under **⚙️ Azure OpenAI & Platform Settings** to chat with the assistant."
            )
            return

        final_input = user_input
        if include_platform_context:
            telemetry = self.get_platform_telemetry_snapshot()
            context_block = (
                f"\n\n[Live Azure Telemetry Context: "
                f"ADF Factory={telemetry['adf']['factory_name']}, "
                f"Recent Pipeline Runs={len(telemetry['adf']['recent_runs'])}, "
                f"Databricks Active Clusters={telemetry['databricks']['running_clusters']}/{telemetry['databricks']['total_clusters']}, "
                f"Active Workers={telemetry['databricks']['total_active_workers']}]"
            )
            final_input = f"{user_input}{context_block}"

        for chunk in self.conversational_chain.stream(
            {"input": final_input},
            config={"configurable": {"session_id": session_id}},
        ):
            if chunk.content:
                yield chunk.content

    def get_platform_telemetry_snapshot(self) -> Dict[str, Any]:
        """
        Explanation: Captures real-time metrics from Azure Data Factory and Databricks.
        :return snapshot Dict[str, Any]: Dictionary containing ADF and Databricks states
        """
        return {
            "adf": {
                "factory_name": self.adf_client.factory_name,
                "recent_runs": self.adf_client.list_recent_runs(limit=4),
            },
            "databricks": self.databricks_client.get_workspace_summary(),
        }

    def get_history(self, session_id: str = "default_session") -> List[BaseMessage]:
        """
        Explanation: Returns all historical chat messages stored for the given session.
        :param  session_id str: Conversation session identifier
        :return messages List[BaseMessage]: Historical list of messages
        """
        return self._get_session_history(session_id).messages

    def clear_history(self, session_id: str = "default_session") -> None:
        """
        Explanation: Resets conversation message history for a given session ID.
        :param  session_id str: Conversation session identifier
        :return None: Empties session memory
        """
        if session_id in self._session_store:
            self._session_store[session_id].clear()
