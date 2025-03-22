#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
##
# Description:-
#
#       Streamlit Web Application for Azure Enterprise Conversational AI Hub.
#       Integrates Azure OpenAI Service (GPT-4o) with dynamic persona switching,
#       real-time Azure Data Factory pipeline execution monitoring, Databricks
#       compute cluster exploration, and cloud lakehouse architecture diagrams.
#
##
# Development date    Developed by       Comments
# ----------------    ------------       ---------
# 14/02/2025          Saddam Khan        Initial implementation
# 22/03/2025          Saddam Khan        Enhanced Azure Copilot UI and ADF/Databricks diagnostics
#
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


"""
Explanation:
    This module implements the primary interactive Streamlit dashboard for the
    Azure Enterprise Conversational AI Hub. It manages session states, sidebars,
    authentication verifications, live telemetry injections, tabbed views for
    chat, Azure Data Factory (ADF) pipeline orchestration, Databricks compute
    cluster management, and cloud enterprise architecture diagrams.

:param None: Module level entrypoint for Streamlit application.
:return None: Renders web interface in Streamlit runtime.
"""

from typing import Any, Dict
from datetime import datetime
import streamlit as st

from config import settings
from personas import PERSONAS
from chatbot import AzureOpenAIChatbot
from utils.auth import verify_azure_openai_credentials
from utils.adf_client import AzureDataFactoryClient
from utils.databricks_client import AzureDatabricksClient
from utils.azure_storage import AzureStorageManager


def init_page_config() -> None:
    """
    Explanation:
        Configures the Streamlit page title, favicon icon, and wide layout mode.

    :param None: Reads no input parameters.
    :return None: Configures the browser tab and page display properties.
    """
    st.set_page_config(
        page_title="Azure Enterprise AI Chatbot (ADF + Databricks + OpenAI)",
        page_icon="🔷",
        layout="wide",
    )


def init_session_state() -> None:
    """
    Explanation:
        Initializes Streamlit session state variables for chat history messages
        and chatbot instance persistence across user interactions.

    :param None: Initializes state dictionary keys.
    :return None: Sets default session state keys if not already initialized.
    """
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "bot" not in st.session_state:
        st.session_state.bot = AzureOpenAIChatbot()


def render_sidebar() -> Dict[str, Any]:
    """
    Explanation:
        Renders the sidebar navigation controls, API credentials verification,
        platform selector (Azure OpenAI vs standard OpenAI), enterprise persona
        picker, model hyperparameters, and chat history export/clearing controls.

    :param None: Reads user interactive inputs from Streamlit sidebar controls.
    :return Dict[str, Any]: Dictionary containing user-configured platform settings:
        'platform_mode', 'azure_endpoint', 'azure_key', 'openai_key',
        'chat_deployment', 'selected_persona_id', 'temperature', and 'inject_telemetry'.
    """
    with st.sidebar:
        st.header("⚙️ Azure OpenAI & Platform Settings")

        is_valid, cred_status = verify_azure_openai_credentials()
        if is_valid:
            st.success(f"Status: `{cred_status}`")
        else:
            st.warning(f"⚠️ {cred_status}")

        platform_mode = st.radio(
            "Platform Mode",
            options=["Azure OpenAI Service", "Standard OpenAI API"],
            index=0 if settings.platform_mode == "azure" else 1,
        )

        azure_endpoint = ""
        azure_key = ""
        openai_key = ""

        if platform_mode == "Azure OpenAI Service":
            azure_endpoint = st.text_input(
                "Azure OpenAI Endpoint",
                value=settings.azure_openai_endpoint,
                placeholder="https://my-resource.openai.azure.com/",
            )
            azure_key = st.text_input(
                "Azure OpenAI API Key",
                value=settings.azure_openai_api_key,
                type="password",
                placeholder="Leave blank for Entra Managed Identity",
            )
            chat_deployment = st.selectbox(
                "Azure Chat Deployment",
                options=["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-35-turbo"],
                index=0,
            )
        else:
            openai_key = st.text_input(
                "OpenAI API Key",
                value=settings.openai_api_key,
                type="password",
                placeholder="sk-...",
            )
            chat_deployment = st.selectbox(
                "OpenAI Model",
                options=["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"],
                index=0,
            )

        st.markdown("---")
        st.header("🎭 Enterprise Persona")

        selected_persona_id = st.selectbox(
            "Specialized Role",
            options=list(PERSONAS.keys()),
            format_func=lambda pid: f"{PERSONAS[pid].icon} {PERSONAS[pid].name}",
            index=0,
        )

        current_persona = PERSONAS[selected_persona_id]
        st.caption(f"**Focus**: {current_persona.tagline}")

        st.markdown("---")
        st.header("🎛️ Model Parameters")

        temperature = st.slider(
            "Temperature (Creativity vs Determinism)",
            min_value=0.0,
            max_value=1.0,
            value=settings.temperature,
            step=0.05,
        )

        inject_telemetry = st.checkbox(
            "⚡ Inject Live Azure Telemetry into Context",
            value=False,
            help="Appends real-time ADF pipeline states and Databricks cluster metrics to each prompt.",
        )

        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑️ Clear Chat", use_container_width=True):
                if "bot" in st.session_state:
                    st.session_state.bot.clear_history("streamlit_session")
                st.session_state.messages = []
                st.rerun()
        with col2:
            if st.session_state.messages:
                chat_export = "\n\n".join(
                    [f"**{m['role'].upper()}**: {m['content']}" for m in st.session_state.messages]
                )
                st.download_button(
                    "📥 Export Chat",
                    data=chat_export,
                    file_name=f"azure_chat_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                    mime="text/markdown",
                    use_container_width=True,
                )

    return {
        "platform_mode": platform_mode,
        "azure_endpoint": azure_endpoint,
        "azure_key": azure_key,
        "openai_key": openai_key,
        "chat_deployment": chat_deployment,
        "selected_persona_id": selected_persona_id,
        "temperature": temperature,
        "inject_telemetry": inject_telemetry,
    }


def get_or_create_bot(
    platform_mode: str,
    chat_deployment: str,
    azure_endpoint: str,
    azure_key: str,
    openai_key: str,
    selected_persona_id: str,
    temperature: float,
) -> AzureOpenAIChatbot:
    """
    Explanation:
        Instantiates or reconfigures the AzureOpenAIChatbot instance stored in
        Streamlit session state whenever active parameters or credentials change.

    :param platform_mode <str>: Selected platform mode ('Azure OpenAI Service' or 'Standard OpenAI API').
    :param chat_deployment <str>: Selected deployment name or OpenAI model ID.
    :param azure_endpoint <str>: Azure OpenAI endpoint URL.
    :param azure_key <str>: Azure OpenAI API key or blank for Entra token.
    :param openai_key <str>: Standard OpenAI API key.
    :param selected_persona_id <str>: Identifier of selected persona.
    :param temperature <float>: Sampling temperature for LLM responses.
    :return AzureOpenAIChatbot: Initialized chatbot instance ready for streaming.
    """
    bot_config_key = (
        f"{platform_mode}_{chat_deployment}_{azure_endpoint}_{azure_key}_{openai_key}_"
        f"{selected_persona_id}_{temperature}"
    )

    if "current_bot_key" not in st.session_state or st.session_state.current_bot_key != bot_config_key:
        st.session_state.bot = AzureOpenAIChatbot(
            persona_id=selected_persona_id,
            chat_deployment=chat_deployment,
            openai_model=chat_deployment,
            azure_endpoint=azure_endpoint if platform_mode == "Azure OpenAI Service" else "",
            azure_api_key=azure_key if platform_mode == "Azure OpenAI Service" else "",
            openai_api_key=openai_key if platform_mode == "Standard OpenAI API" else "",
            temperature=temperature,
        )
        st.session_state.current_bot_key = bot_config_key

    return st.session_state.bot

def render_chat_tab(
    bot: AzureOpenAIChatbot,
    current_persona: Any,
    inject_telemetry: bool,
) -> None:
    """
    Explanation:
        Renders the interactive conversational interface including suggested prompts,
        chat message history, input box, and real-time streaming response container
        with optional live telemetry context injection.

    :param bot <AzureOpenAIChatbot>: Chatbot instance used for inference.
    :param current_persona <Persona>: Selected enterprise persona metadata.
    :param inject_telemetry <bool>: Flag indicating whether live ADF/Databricks telemetry is injected.
    :return None: Renders interactive chat elements to Streamlit DOM.
    """
    # Suggested Prompts Bar
    if not st.session_state.messages:
        st.markdown(f"##### 💡 Suggested Questions for **{current_persona.name}**:")
        suggested_cols = st.columns(len(current_persona.suggested_prompts))
        for idx, prompt_text in enumerate(current_persona.suggested_prompts):
            if suggested_cols[idx].button(prompt_text, key=f"sug_{idx}", use_container_width=True):
                st.session_state.messages.append({"role": "user", "content": prompt_text})
                st.rerun()

    # Message History Rendering
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Chat Input Box
    prompt_input = st.chat_input(f"Ask {current_persona.name} about Azure, ADF, Databricks, or cloud strategy...")
    pending_query = None

    if prompt_input:
        pending_query = prompt_input
        st.session_state.messages.append({"role": "user", "content": prompt_input})
        with st.chat_message("user"):
            st.markdown(prompt_input)
    elif st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
        # Check if last user message hasn't been answered yet
        if len(st.session_state.messages) >= 2 and st.session_state.messages[-2]["role"] == "user":
            pass
        else:
            pending_query = st.session_state.messages[-1]["content"]

    if pending_query and (len(st.session_state.messages) % 2 == 1):
        with st.chat_message("assistant"):
            response_box = st.empty()
            full_response = ""

            try:
                for chunk in bot.stream_chat(
                    user_input=pending_query,
                    session_id="streamlit_session",
                    include_platform_context=inject_telemetry,
                ):
                    full_response += chunk
                    response_box.markdown(full_response + "▌")

                if full_response:
                    response_box.markdown(full_response)
                    st.session_state.messages.append({"role": "assistant", "content": full_response})
                else:
                    response_box.warning("No response generated.")
            except Exception as e:
                err_msg = str(e)
                if "api_key" in err_msg.lower() or "authentication" in err_msg.lower():
                    response_box.error(
                        f"🔑 **Authentication Required**\n\n"
                        f"Please enter your **Azure OpenAI Endpoint & API Key** (or standard OpenAI API Key) "
                        f"in the sidebar under **⚙️ Azure OpenAI & Platform Settings**.\n\n"
                        f"Details: `{err_msg}`"
                    )
                else:
                    response_box.error(f"⚠️ Error: {err_msg}")


def render_adf_tab(adf_client: AzureDataFactoryClient) -> None:
    """
    Explanation:
        Renders the Azure Data Factory (ADF) monitoring tab displaying on-demand
        pipeline trigger controls, recent execution run status, and detailed activity runs.

    :param adf_client <AzureDataFactoryClient>: Client for interacting with Azure Data Factory APIs.
    :return None: Renders ADF pipeline dashboard in Streamlit.
    """
    st.subheader("🏭 Azure Data Factory Ingestion & Pipeline Orchestration")
    st.caption(f"Connected to Factory: `{adf_client.factory_name}` in RG `{adf_client.resource_group}`")

    # Trigger Pipeline Action Card
    with st.expander("⚡ Trigger On-Demand ADF Pipeline Run", expanded=True):
        p_col1, p_col2 = st.columns([3, 1])
        all_pipelines = adf_client.list_pipelines()
        pipe_names = [p["name"] for p in all_pipelines]
        selected_pipe = p_col1.selectbox("Select Pipeline to Execute", pipe_names)
        if p_col2.button("🚀 Trigger Run", use_container_width=True):
            run_info = adf_client.trigger_pipeline(selected_pipe)
            st.success(f"Pipeline Run Started! Run ID: `{run_info['run_id']}`")
            st.rerun()

    # Recent Pipeline Runs Table
    st.markdown("#### ⏱️ Recent Pipeline Execution Runs")
    runs = adf_client.list_recent_runs()
    runs_display = []
    for r in runs:
        runs_display.append({
            "Run ID": r["run_id"],
            "Pipeline": r["pipeline_name"],
            "Status": "🟢 Succeeded" if r["status"] == "Succeeded" else ("🔵 InProgress" if r["status"] == "InProgress" else "🔴 Failed"),
            "Start Time": r["run_start"],
            "Duration (s)": f"{r['duration_seconds']}s",
            "Invoker": r["invoker"],
        })
    st.dataframe(runs_display, use_container_width=True)

    # Activity Breakdown Viewer
    st.markdown("#### 🔍 Activity Run Telemetry")
    selected_run_id = st.selectbox("Inspect Activities for Run", [r["run_id"] for r in runs])
    activities = adf_client.get_activity_runs(selected_run_id)
    st.table(activities)


def render_databricks_tab(
    databricks_client: AzureDatabricksClient,
    db_summary: Dict[str, Any],
) -> None:
    """
    Explanation:
        Renders the Azure Databricks analytics workspace tab displaying cluster health,
        worker nodes, DBU burn rate, active clusters table, and PySpark job executions.

    :param databricks_client <AzureDatabricksClient>: Client for Azure Databricks workspace management.
    :param db_summary <Dict[str, Any]>: Aggregated workspace compute metrics dictionary.
    :return None: Renders Databricks workspace dashboard in Streamlit.
    """
    st.subheader("⚡ Azure Databricks Analytics & Compute Workspace")
    st.caption(f"Workspace Host: `{databricks_client.host}`")

    w1, w2, w3, w4 = st.columns(4)
    w1.metric("Active Clusters", f"{db_summary['running_clusters']} / {db_summary['total_clusters']}")
    w2.metric("Active Compute Workers", db_summary["total_active_workers"])
    w3.metric("DBU Burn Rate", f"{db_summary['estimated_dbu_per_hour']} DBU/hr")
    w4.metric("Configured Jobs", db_summary["total_jobs"])

    st.markdown("#### 🖥️ Databricks Compute Clusters")
    clusters = databricks_client.list_clusters()
    clusters_data = []
    for c in clusters:
        clusters_data.append({
            "Cluster Name": c["cluster_name"],
            "State": "🟢 RUNNING" if c["state"] == "RUNNING" else "⚪ TERMINATED",
            "Workers": c["current_num_workers"],
            "Node Type": c["node_type_id"],
            "DBU/hr": c["dbu_rate_per_hour"],
            "Spark Runtime": c["spark_version"],
        })
    st.dataframe(clusters_data, use_container_width=True)

    st.markdown("#### ⚙️ Configured Databricks PySpark & Delta Jobs")
    jobs = databricks_client.list_jobs()
    j_cols = st.columns(len(jobs))
    for idx, j in enumerate(jobs):
        with j_cols[idx]:
            st.markdown(f"**{j['name']}**")
            st.caption(f"Schedule: `{j['schedule']}`")
            st.caption(f"Last Status: `{j['last_run_status']}`")
            if st.button(f"▶️ Run Job", key=f"btn_job_{idx}", use_container_width=True):
                res = databricks_client.run_job(j["job_id"])
                st.success(f"Job triggered: `{res['run_id']}`")
                st.rerun()


def render_architecture_tab() -> None:
    """
    Explanation:
        Renders the enterprise cloud architecture diagram and zero-trust security
        governance tables detailing end-to-end ADF, Databricks, and Azure OpenAI integration.

    :param None: Takes no input arguments.
    :return None: Renders Mermaid diagrams and markdown tables in Streamlit.
    """
    st.subheader("🏛️ Enterprise Architecture: Azure OpenAI + ADF + Databricks")

    st.markdown("""
    ```mermaid
    graph LR
        subgraph Ingestion ["1. Data Movement & Ingestion"]
            Sources["Enterprise Sources (SAP, SQL, Logs, Files)"] --> SHIR["Self-Hosted Integration Runtime"]
            SHIR --> ADF["Azure Data Factory (ADF Pipelines)"]
            ADF --> ADLS["ADLS Gen2 (Bronze Lakehouse)"]
        end

        subgraph Lakehouse ["2. Databricks Delta Lakehouse"]
            ADLS --> DBW["Azure Databricks (PySpark)"]
            DBW --> DeltaSilver["Delta Lake Silver (Cleansed)"]
            DeltaSilver --> DeltaGold["Delta Lake Gold & Unity Catalog"]
        end

        subgraph Intelligence ["3. Azure OpenAI & LangChain Hub"]
            DeltaGold --> AOAI_Embed["Azure OpenAI Embeddings"]
            AOAI_Embed --> Index["Hybrid Semantic Store"]
            AOAI_Chat["Azure OpenAI (GPT-4o)"] <--> LC["LangChain Conversational Engine"]
            Index --> LC
            LC <--> UI["Streamlit Enterprise Chatbot Hub"]
        end
    ```
    """)

    st.markdown("### 🔐 Zero-Trust Security & Production Best Practices")
    st.markdown("""
    | Component | Security & Governance Pattern | Best Practice Recommendation |
    | :--- | :--- | :--- |
    | **Azure OpenAI** | Private Endpoints & Customer Managed Keys (CMK) | Place behind Azure VNet; disable public access; route via API Management. |
    | **Entra ID (Azure AD)** | Managed Identities & RBAC | Use System-Assigned Managed Identity for ADF and Databricks service-to-service calls. |
    | **ADF Ingestion** | Self-Hosted IR in secure subnet | Restrict egress via NSG rules; store linked service credentials in Azure Key Vault. |
    | **Databricks** | Unity Catalog & Single-User Clusters | Implement table and column-level access controls; enforce audit logging to Log Analytics. |
    | **ADLS Gen2** | Hierarchical Namespace & ACLs | Enforce TLS 1.3, Storage Account firewalls, and periodic lifecycle tiering (Hot -> Cool -> Archive). |
    """)


def main() -> None:
    """
    Explanation:
        Main application orchestration function coordinating configuration,
        sidebar controls, client initialization, header metrics, and tab navigation.

    :param None: Reads execution configuration and coordinates Streamlit application lifecycle.
    :return None: Coordinates application lifecycle.
    """
    init_page_config()
    init_session_state()
    sidebar_params = render_sidebar()

    bot = get_or_create_bot(
        platform_mode=sidebar_params["platform_mode"],
        chat_deployment=sidebar_params["chat_deployment"],
        azure_endpoint=sidebar_params["azure_endpoint"],
        azure_key=sidebar_params["azure_key"],
        openai_key=sidebar_params["openai_key"],
        selected_persona_id=sidebar_params["selected_persona_id"],
        temperature=sidebar_params["temperature"],
    )

    adf_client = bot.adf_client
    databricks_client = bot.databricks_client
    _ = AzureStorageManager()

    # Top Header & Platform Metrics
    st.title("🔷 Azure Enterprise Conversational AI Hub")
    st.caption("Intelligent Multi-Turn Assistant with **Azure OpenAI (GPT-4o)**, **LangChain**, **ADF**, & **Azure Databricks**.")

    current_persona = PERSONAS[sidebar_params["selected_persona_id"]]
    db_summary = databricks_client.get_workspace_summary()

    mcol1, mcol2, mcol3, mcol4 = st.columns(4)
    mcol1.metric("Active LLM Backend", bot.active_provider.split(" ")[0])
    mcol2.metric("Active Persona", current_persona.name.split(" ")[0])
    mcol3.metric("ADF Factory", adf_client.factory_name.split("-")[-2].upper() if "-" in adf_client.factory_name else adf_client.factory_name)
    mcol4.metric("Databricks Clusters", f"{db_summary['running_clusters']}/{db_summary['total_clusters']} Active")

    st.markdown("---")

    # Tabbed Navigation
    tab_chat, tab_adf, tab_databricks, tab_arch = st.tabs([
        "💬 Enterprise AI Assistant",
        "🏭 Azure Data Factory (ADF) Monitor",
        "⚡ Azure Databricks Workspace",
        "🏛️ System Architecture & Best Practices",
    ])

    with tab_chat:
        render_chat_tab(
            bot=bot,
            current_persona=current_persona,
            inject_telemetry=sidebar_params["inject_telemetry"],
        )

    with tab_adf:
        render_adf_tab(adf_client=adf_client)

    with tab_databricks:
        render_databricks_tab(databricks_client=databricks_client, db_summary=db_summary)

    with tab_arch:
        render_architecture_tab()


if __name__ == "__main__":
    main()

