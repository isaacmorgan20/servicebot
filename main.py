# import sys
# import os
# from dotenv import load_dotenv

# load_dotenv()

# try:
#     from rich.console import Console
#     from rich.panel import Panel
#     from rich.prompt import Prompt
#     from rich.markdown import Markdown
# except ImportError:
#     print("Required: 'rich' library. Run: pip install rich")
#     sys.exit(1)

# from chatbot.engine import ServiceBot


# console = Console()


# def print_bot_message(content: str):
#     md = Markdown(content or "")
#     console.print(Panel(md, title="NexSupport", title_align="left",
#                         border_style="bright_blue", padding=(1, 2)))


# def print_user_message(content: str):
#     console.print(f"[bold green]You:[/bold green] {content}")


# def main():
#     api_key = os.getenv("GROQ_API_KEY")
#     model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

#     if not api_key or api_key == "your-api-key-here":
#         console.print("[bold red]ERROR:[/bold red] GROQ_API_KEY not set in .env file.")
#         console.print("Edit the [bold].env[/bold] file and add your Groq API key.")
#         sys.exit(1)

#     console.print("[bold bright_blue]╔══════════════════════════════════════════════╗[/]")
#     console.print("[bold bright_blue]║           NexSupport AI Assistant           ║[/]")
#     console.print("[bold bright_blue]║     Customer Service & SME Support Bot     ║[/]")
#     console.print(f"[bold bright_blue]║     Model: {model:<36s}║[/]")
#     console.print("[bold bright_blue]╚══════════════════════════════════════════════╝[/]")
#     console.print("[dim]Type [bold]'quit'[/bold], [bold]'exit'[/bold], or press Ctrl+C to end the session.[/dim]")
#     console.print()

#     def status_callback(msg: str):
#         console.print(f"[bold yellow]⚠️  {msg}[/bold yellow]")

#     bot = ServiceBot(api_key=api_key, model=model, status_callback=status_callback)

#     greeting = bot.get_greeting()
#     print_bot_message(greeting)

#     while True:
#         try:
#             user_input = Prompt.ask("[bold green]You")
#         except (KeyboardInterrupt, EOFError):
#             console.print()
#             print_bot_message(bot.get_closing())
#             sys.exit(0)

#         if user_input.lower().strip() in ("quit", "exit", "bye", "goodbye"):
#             print_bot_message(bot.get_closing())
#             break

#         if not user_input.strip():
#             continue

#         print_user_message(user_input)
#         response = bot.chat(user_input)
#         print_bot_message(response)


# if __name__ == "__main__":
#     main()

import sys
import os
import uuid
from dotenv import load_dotenv

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

load_dotenv()

# ============================================================
# RICH IMPORTS
# ============================================================

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.prompt import Prompt
    from rich.markdown import Markdown
except ImportError:
    print("Required: 'rich' library. Run: pip install rich")
    sys.exit(1)

from chatbot.engine import ServiceBot


# ============================================================
# CONFIGURATION
# ============================================================

API_KEY = os.getenv("GROQ_API_KEY")
MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

if not API_KEY or API_KEY == "your-api-key-here":
    print("ERROR: GROQ_API_KEY not set in .env file.")
    sys.exit(1)


# ============================================================
# RICH TERMINAL
# ============================================================

console = Console()


def print_bot_message(content: str):
    md = Markdown(content or "")

    console.print(
        Panel(
            md,
            title="NexSupport",
            title_align="left",
            border_style="bright_blue",
            padding=(1, 2),
        )
    )


def print_user_message(content: str):
    console.print(
        f"[bold green]You:[/bold green] {content}"
    )


def status_callback(msg: str):
    console.print(
        f"[bold yellow]⚠️  {msg}[/bold yellow]"
    )


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="NexSupport AI Assistant",
    description="AI-powered Customer Service & SME Support Assistant",
    version="1.0.0",
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# SESSION STORAGE
# ============================================================

sessions = {}


def create_bot():
    return ServiceBot(
        api_key=API_KEY,
        model=MODEL,
        status_callback=status_callback,
    )


# ============================================================
# REQUEST MODELS
# ============================================================

class ChatRequest(BaseModel):
    session_id: str
    message: str


class ResetRequest(BaseModel):
    session_id: str


# ============================================================
# BASIC ROUTES
# ============================================================

@app.get("/")
def home():
    return {
        "name": "NexSupport AI Assistant",
        "status": "online",
        "model": MODEL,
        "message": "NexSupport API is running."
    }


@app.get("/api/status")
def status():
    return {
        "status": "online",
        "service": "NexSupport",
        "model": MODEL
    }


# ============================================================
# CREATE SESSION
# ============================================================

@app.get("/api/session")
def create_session():

    session_id = str(uuid.uuid4())

    bot = create_bot()

    sessions[session_id] = bot

    return {
        "session_id": session_id,
        "model": MODEL,
        "greeting": bot.get_greeting()
    }


# ============================================================
# CHAT
# ============================================================

@app.post("/api/chat")
def chat(request: ChatRequest):

    if not request.message.strip():
        return {
            "reply": "Please enter a message.",
            "model": MODEL,
            "tool_calls": [],
            "status_messages": []
        }

    bot = sessions.get(request.session_id)

    if bot is None:
        return {
            "reply": "Your session has expired. Please refresh the page.",
            "model": MODEL,
            "tool_calls": [],
            "status_messages": []
        }

    response = bot.chat(request.message)

    return {
        "reply": response,
        "model": MODEL,
        "tool_calls": [],
        "status_messages": []
    }


# ============================================================
# RESET SESSION
# ============================================================

@app.post("/api/reset")
def reset_session(request: ResetRequest):

    old_session_id = request.session_id

    # Remove old session
    sessions.pop(old_session_id, None)

    # Create new session
    new_session_id = str(uuid.uuid4())

    bot = create_bot()

    sessions[new_session_id] = bot

    return {
        "session_id": new_session_id,
        "model": MODEL,
        "greeting": bot.get_greeting()
    }


# ============================================================
# CLOSING
# ============================================================

@app.get("/api/closing")
def closing():

    # Create a temporary bot just to get the closing message
    bot = create_bot()

    return {
        "response": bot.get_closing()
    }


# ============================================================
# TERMINAL CHATBOT
# ============================================================

def run_terminal():

    console.print(
        "[bold bright_blue]"
        "╔══════════════════════════════════════════════╗"
        "[/]"
    )

    console.print(
        "[bold bright_blue]"
        "║           NexSupport AI Assistant           ║"
        "[/]"
    )

    console.print(
        "[bold bright_blue]"
        "║     Customer Service & SME Support Bot      ║"
        "[/]"
    )

    console.print(
        f"[bold bright_blue]"
        f"║     Model: {MODEL:<36}║"
        "[/]"
    )

    console.print(
        "[bold bright_blue]"
        "╚══════════════════════════════════════════════╝"
        "[/]"
    )

    console.print(
        "[dim]Type [bold]'quit'[/bold], "
        "[bold]'exit'[/bold], or press Ctrl+C "
        "to end the session.[/dim]"
    )

    console.print()

    terminal_bot = create_bot()

    greeting = terminal_bot.get_greeting()

    print_bot_message(greeting)

    while True:

        try:
            user_input = Prompt.ask("[bold green]You")

        except (KeyboardInterrupt, EOFError):

            console.print()

            print_bot_message(
                terminal_bot.get_closing()
            )

            break

        if user_input.lower().strip() in (
            "quit",
            "exit",
            "bye",
            "goodbye",
        ):
            print_bot_message(
                terminal_bot.get_closing()
            )
            break

        if not user_input.strip():
            continue

        print_user_message(user_input)

        response = terminal_bot.chat(user_input)

        print_bot_message(response)


# ============================================================
# START APPLICATION
# ============================================================

if __name__ == "__main__":

    if len(sys.argv) > 1 and sys.argv[1].lower() == "web":

        port = int(os.getenv("PORT", "8010"))

        uvicorn.run(
            app,
            host="0.0.0.0",
            port=port,
        )

    elif len(sys.argv) > 1 and sys.argv[1].lower() == "chat":

        run_terminal()

    else:

        console.print("[bold yellow]Usage:[/bold yellow]")

        console.print(
            "  python main.py web   → Start FastAPI server"
        )

        console.print(
            "  python main.py chat  → Start terminal chatbot"
        )