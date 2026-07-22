import os
import uuid
import logging
from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from chatbot.agent import AgenticServiceBot
from db.firestore import (
    init_firebase, is_ready,
    save_session, save_message,
    get_session, get_messages, list_sessions,
)

load_dotenv()
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="NexSupport Web API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── In-memory session store (backup; Firestore is primary persistence) ──────
_sessions: dict[str, dict] = {}


@app.on_event("startup")
def startup():
    init_firebase()


def _get_api_key() -> str:
    key = os.getenv("GROQ_API_KEY", "")
    if not key or key == "your-api-key-here":
        raise HTTPException(status_code=503, detail="GROQ_API_KEY is not configured on the server.")
    return key


def _get_model() -> str:
    return os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")


def _make_session(session_id: str) -> dict:
    status_messages: list[str] = []

    def status_callback(msg: str):
        status_messages.append(msg)

    bot = AgenticServiceBot(
        api_key=_get_api_key(),
        model=_get_model(),
        status_callback=status_callback,
    )
    _sessions[session_id] = {"bot": bot, "status": status_messages}
    return _sessions[session_id]


# ── Request / Response Models ──────────────────────────────────────────────────

class ChatRequest(BaseModel):
    session_id: str
    message: str


class ToolCallInfo(BaseModel):
    name: str
    arguments: dict
    result: dict
    status: str


class ChatResponse(BaseModel):
    reply: str
    model: str
    status_messages: list[str]
    tool_calls: list[ToolCallInfo] = []


class SessionResponse(BaseModel):
    session_id: str
    greeting: str
    model: str


class ResetRequest(BaseModel):
    session_id: str


class ResetResponse(BaseModel):
    session_id: str
    greeting: str
    model: str


class SessionRestoreRequest(BaseModel):
    session_id: str


class SessionRestoreResponse(BaseModel):
    session_id: str
    model: str
    title: str
    message_count: int


class SessionSummary(BaseModel):
    id: str
    title: str
    model: str
    message_count: int
    created_at: str | None = None
    updated_at: str | None = None


class ConversationDetail(BaseModel):
    session: SessionSummary
    messages: list[dict]


# ── API Endpoints ──────────────────────────────────────────────────────────────

@app.get("/api/session", response_model=SessionResponse)
def create_session(user_id: str = Query(default="")):
    """Create a new chat session and return the greeting."""
    session_id = str(uuid.uuid4())
    session = _make_session(session_id)
    bot: AgenticServiceBot = session["bot"]
    status: list[str] = session["status"]

    status.clear()
    greeting = bot.get_greeting()

    save_session(session_id, bot.model, user_id=user_id)

    return SessionResponse(
        session_id=session_id,
        greeting=greeting,
        model=bot.model,
    )


@app.post("/api/session/restore", response_model=SessionRestoreResponse)
def restore_session(req: SessionRestoreRequest):
    """Restore a previous session from Firestore so the user can continue chatting."""
    session_data = get_session(req.session_id)
    if not session_data:
        raise HTTPException(status_code=404, detail="Session not found.")

    if req.session_id in _sessions:
        del _sessions[req.session_id]

    session = _make_session(req.session_id)
    bot: AgenticServiceBot = session["bot"]

    messages = get_messages(req.session_id)
    bot.messages = [bot.messages[0]]

    for msg in messages:
        role = msg.get("role", "")
        content = msg.get("content", "")
        if role in ("user", "assistant"):
            bot.messages.append({"role": role, "content": content})

    return SessionRestoreResponse(
        session_id=req.session_id,
        model=bot.model,
        title=session_data.get("title", "Untitled"),
        message_count=session_data.get("message_count", 0),
    )


@app.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    """Send a user message and get the agent's reply with tool calls."""
    if req.session_id not in _sessions:
        raise HTTPException(status_code=404, detail="Session not found. Please refresh the page.")

    session = _sessions[req.session_id]
    bot: AgenticServiceBot = session["bot"]
    status: list[str] = session["status"]

    status.clear()
    reply, tool_calls = bot.chat(req.message)
    captured_status = list(status)

    tool_calls_data = [ToolCallInfo(**tc) for tc in tool_calls]

    save_message(
        req.session_id, "user", req.message,
        model=bot.model,
    )
    save_message(
        req.session_id, "assistant", reply,
        tool_calls=[tc.model_dump() for tc in tool_calls_data] if tool_calls_data else None,
        model=bot.model,
    )

    return ChatResponse(
        reply=reply,
        model=bot.model,
        status_messages=captured_status,
        tool_calls=tool_calls_data,
    )


@app.post("/api/reset", response_model=ResetResponse)
def reset_session(req: ResetRequest):
    """Reset the current session and start fresh."""
    if req.session_id in _sessions:
        del _sessions[req.session_id]

    session_id = req.session_id
    session = _make_session(session_id)
    bot: AgenticServiceBot = session["bot"]
    status: list[str] = session["status"]

    status.clear()
    greeting = bot.get_greeting()

    save_session(session_id, bot.model)

    return ResetResponse(
        session_id=session_id,
        greeting=greeting,
        model=bot.model,
    )


@app.get("/api/conversations", response_model=list[SessionSummary])
def list_conversations(limit: int = 50, user_id: str = Query(default="")):
    """List past conversation sessions for a user."""
    sessions = list_sessions(limit, user_id=user_id)
    return [
        SessionSummary(
            id=s.get("session_id", s.get("id", "")),
            title=s.get("title", "Untitled"),
            model=s.get("model", ""),
            message_count=s.get("message_count", 0),
            created_at=s.get("created_at"),
            updated_at=s.get("updated_at"),
        )
        for s in sessions
    ]


@app.get("/api/conversations/{session_id}", response_model=ConversationDetail)
def get_conversation(session_id: str):
    """Get full conversation history including all messages."""
    session_data = get_session(session_id)
    if session_data is None:
        raise HTTPException(status_code=404, detail="Conversation not found.")

    messages = get_messages(session_id)

    summary = SessionSummary(
        id=session_data.get("session_id", session_id),
        title=session_data.get("title", "Untitled"),
        model=session_data.get("model", ""),
        message_count=session_data.get("message_count", 0),
        created_at=session_data.get("created_at"),
        updated_at=session_data.get("updated_at"),
    )

    return ConversationDetail(session=summary, messages=messages)


@app.delete("/api/conversations/{session_id}")
def delete_conversation(session_id: str):
    """Delete a conversation and all its messages."""
    from db.firestore import delete_session as fs_delete
    ok = fs_delete(session_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Conversation not found or could not be deleted.")
    return {"status": "deleted"}


@app.get("/api/status")
def server_status():
    """Returns server info and configuration."""
    return {
        "status": "online",
        "model": _get_model(),
        "active_sessions": len(_sessions),
        "firestore": is_ready(),
    }


# ── Static Files & Catch-all for SPA ──────────────────────────────────────────
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/react", StaticFiles(directory="static_react"), name="react")


@app.get("/")
def serve_index():
    return FileResponse("static_react/index.html")
