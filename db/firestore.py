import os
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

_firestore_client = None
_firebase_app = None
_Increment = None
_Descending = None
_collection = "conversations"


def init_firebase() -> bool:
    global _firestore_client, _firebase_app, _Increment, _Descending

    if _firestore_client is not None:
        return True

    cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")
    if not cred_path or not os.path.isfile(cred_path):
        logger.warning("Firebase credentials not found. Conversations will NOT be persisted.")
        return False

    try:
        import firebase_admin
        from firebase_admin import credentials, firestore

        if not firebase_admin._apps:
            cred = credentials.Certificate(cred_path)
            _firebase_app = firebase_admin.initialize_app(cred)

        _firestore_client = firestore.client()
        _Increment = firestore.Increment
        _Descending = firestore.Query.DESCENDING

        global _collection
        _collection = os.getenv("FIRESTORE_COLLECTION", "conversations")

        logger.info("Firebase initialized successfully.")
        return True
    except Exception as e:
        logger.error("Failed to initialize Firebase: %s", e)
        _firestore_client = None
        return False


def is_ready() -> bool:
    return _firestore_client is not None


def save_session(session_id: str, model: str, title: str = "", user_id: str = "") -> bool:
    if _firestore_client is None:
        return False

    try:
        now = datetime.now(timezone.utc)
        doc_ref = _firestore_client.collection(_collection).document(session_id)
        doc = doc_ref.get()

        if doc.exists:
            update_data: dict = {
                "model": model,
                "updated_at": now,
            }
            if user_id:
                update_data["user_id"] = user_id
            doc_ref.update(update_data)
        else:
            doc_data: dict = {
                "session_id": session_id,
                "title": title or f"Session {session_id[:8]}",
                "model": model,
                "created_at": now,
                "updated_at": now,
                "message_count": 0,
            }
            if user_id:
                doc_data["user_id"] = user_id
            doc_ref.set(doc_data)
        return True
    except Exception as e:
        logger.error("Failed to save session %s: %s", session_id, e)
        return False


def update_session_title(session_id: str, title: str) -> bool:
    if _firestore_client is None:
        return False

    try:
        _firestore_client.collection(_collection).document(session_id).update({"title": title})
        return True
    except Exception as e:
        logger.error("Failed to update session title %s: %s", session_id, e)
        return False


def save_message(
    session_id: str,
    role: str,
    content: str,
    tool_calls: list | None = None,
    tool_call_id: str | None = None,
    model: str | None = None,
) -> bool:
    if _firestore_client is None or _Increment is None:
        return False

    try:
        now = datetime.now(timezone.utc)
        msg_data: dict = {
            "role": role,
            "content": content,
            "created_at": now,
        }
        if tool_calls is not None:
            msg_data["tool_calls"] = tool_calls
        if tool_call_id is not None:
            msg_data["tool_call_id"] = tool_call_id
        if model is not None:
            msg_data["model"] = model

        _firestore_client.collection(_collection).document(session_id)\
            .collection("messages").add(msg_data)

        _firestore_client.collection(_collection).document(session_id).update({
            "updated_at": now,
            "message_count": _Increment(1),
        })

        return True
    except Exception as e:
        logger.error("Failed to save message for session %s: %s", session_id, e)
        return False


def get_session(session_id: str) -> dict | None:
    if _firestore_client is None:
        return None

    try:
        doc = _firestore_client.collection(_collection).document(session_id).get()
        if not doc.exists:
            return None
        data = doc.to_dict()
        if data and data.get("created_at"):
            data["created_at"] = data["created_at"].isoformat()
        if data and data.get("updated_at"):
            data["updated_at"] = data["updated_at"].isoformat()
        return data
    except Exception as e:
        logger.error("Failed to get session %s: %s", session_id, e)
        return None


def get_messages(session_id: str) -> list[dict]:
    if _firestore_client is None:
        return []

    try:
        docs = _firestore_client.collection(_collection).document(session_id)\
            .collection("messages")\
            .order_by("created_at")\
            .stream()

        messages = []
        for doc in docs:
            data = doc.to_dict()
            data["id"] = doc.id
            if data.get("created_at"):
                data["created_at"] = data["created_at"].isoformat()
            messages.append(data)
        return messages
    except Exception as e:
        logger.error("Failed to get messages for session %s: %s", session_id, e)
        return []


def list_sessions(limit: int = 50, user_id: str = "") -> list[dict]:
    if _firestore_client is None:
        return []

    try:
        query = _firestore_client.collection(_collection)
        if user_id:
            query = query.where("user_id", "==", user_id)
        docs = query\
            .order_by("updated_at", direction=_Descending)\
            .limit(limit)\
            .stream()

        sessions = []
        for doc in docs:
            data = doc.to_dict()
            data["id"] = doc.id
            if data.get("created_at"):
                data["created_at"] = data["created_at"].isoformat()
            if data.get("updated_at"):
                data["updated_at"] = data["updated_at"].isoformat()
            sessions.append(data)
        return sessions
    except Exception as e:
        logger.error("Failed to list sessions: %s", e)
        return []


def delete_session(session_id: str) -> bool:
    if _firestore_client is None:
        return False

    try:
        messages = _firestore_client.collection(_collection).document(session_id)\
            .collection("messages").stream()
        for msg in messages:
            msg.reference.delete()

        _firestore_client.collection(_collection).document(session_id).delete()
        return True
    except Exception as e:
        logger.error("Failed to delete session %s: %s", session_id, e)
        return False
