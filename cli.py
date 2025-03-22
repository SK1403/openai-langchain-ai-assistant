#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
##
# Description:-
#
#       Command Line Interface (CLI) for Azure Enterprise Conversational AI Chatbot.
#       Provides terminal-based interactive multi-turn chat, runtime persona switching,
#       Azure Data Factory pipeline status queries, and Databricks cluster metrics.
#
##
# Development date    Developed by       Comments
# ----------------    ------------       ---------
# 14/02/2025          Saddam Khan        Initial implementation
# 22/03/2025          Saddam Khan        Added interactive terminal copilot and Azure CLI checks
#
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

import sys
import argparse
from chatbot import AzureOpenAIChatbot
from personas import PERSONAS, get_persona
from utils.auth import verify_azure_openai_credentials

def print_banner(bot: AzureOpenAIChatbot) -> None:
    """
    Explanation: Prints formatted CLI banner with active LLM backend, persona, and commands.
    :param  bot AzureOpenAIChatbot: Initialized chatbot instance
    :return None: Prints directly to standard output
    """
    print("=" * 75)
    print("🔷  AZURE ENTERPRISE CONVERSATIONAL AI CHATBOT  🔷")
    print("   Azure OpenAI (GPT-4o) | LangChain | Azure Data Factory | Databricks")
    print("=" * 75)
    is_valid, msg = verify_azure_openai_credentials()
    print(f"Backend Status: {msg}")
    print(f"Active Provider: {bot.active_provider}")
    print(f"Active Persona: {bot.persona.icon} {bot.persona.name} ({bot.persona.id})")
    print(f"Tagline: {bot.persona.tagline}")
    print("\nCommands:")
    print("  /personas         - List all specialized enterprise personas")
    print("  /switch <id>      - Switch active persona (e.g. /switch adf_engineer)")
    print("  /adf              - View live Azure Data Factory pipeline statuses")
    print("  /databricks       - View Azure Databricks clusters and jobs")
    print("  /clear            - Reset conversation memory")
    print("  /exit             - Quit CLI")
    print("-" * 75)

def main() -> None:
    """
    Explanation: Parses CLI arguments and enters interactive multi-turn chat REPL loop.
    :return None: Executes CLI loop until exit command or keyboard interrupt
    """
    parser = argparse.ArgumentParser(description="Azure OpenAI & Databricks Enterprise Chatbot CLI")
    parser.add_argument(
        "--persona",
        type=str,
        default="azure_architect",
        choices=list(PERSONAS.keys()),
        help="Specialized enterprise persona",
    )
    parser.add_argument("--temperature", type=float, default=0.3, help="Model temperature (0.0 to 1.0)")
    args = parser.parse_args()

    bot = AzureOpenAIChatbot(persona_id=args.persona, temperature=args.temperature)
    print_banner(bot)

    session_id = "cli_session"

    while True:
        try:
            user_input = input(f"\n[{bot.persona.id}] 👤 You: ").strip()
            if not user_input:
                continue

            if user_input.lower() in ["/exit", "/quit", "exit", "quit"]:
                print("Exiting Azure Enterprise AI Chatbot. Goodbye!")
                break

            if user_input.lower() == "/help":
                print_banner(bot)
                continue

            if user_input.lower() == "/personas":
                print("\nAvailable Enterprise Personas:")
                for pid, p in PERSONAS.items():
                    current_flag = " (ACTIVE)" if pid == bot.persona_id else ""
                    print(f"  • {p.icon} {pid:<22} - {p.name}{current_flag}")
                    print(f"    {p.tagline}")
                continue

            if user_input.lower().startswith("/switch"):
                parts = user_input.split()
                if len(parts) > 1 and parts[1] in PERSONAS:
                    bot.set_persona(parts[1])
                    print(f"\n🔄 Switched persona to: {bot.persona.icon} {bot.persona.name}")
                    print(f"Focus: {bot.persona.tagline}")
                else:
                    print(f"Invalid persona ID. Choose from: {', '.join(PERSONAS.keys())}")
                continue

            if user_input.lower() == "/adf":
                print("\n🏭 Azure Data Factory Pipelines:")
                for p in bot.adf_client.list_pipelines():
                    print(f"  [{p['last_run_status']}] {p['name']}: {p['description']}")
                continue

            if user_input.lower() == "/databricks":
                summary = bot.databricks_client.get_workspace_summary()
                print(f"\n⚡ Databricks Workspace Summary:")
                print(f"  Clusters: {summary['running_clusters']} Running / {summary['total_clusters']} Total")
                print(f"  Active Workers: {summary['total_active_workers']} | DBU/hr: {summary['estimated_dbu_per_hour']}")
                continue

            if user_input.lower() == "/clear":
                bot.clear_history(session_id)
                print("🧹 Conversation memory cleared.")
                continue

            print(f"\n{bot.persona.icon} Assistant: ", end="", flush=True)
            for chunk in bot.stream_chat(user_input, session_id=session_id):
                print(chunk, end="", flush=True)
            print()

        except (KeyboardInterrupt, EOFError):
            print("\nSession ended.")
            break
        except Exception as e:
            print(f"\nError: {e}")

if __name__ == "__main__":
    main()
