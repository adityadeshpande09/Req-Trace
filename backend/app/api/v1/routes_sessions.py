from fastapi import APIRouter, HTTPException, Body, Query
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import os
import uuid

router = APIRouter(prefix="/api/sessions", tags=["sessions"])

# Simple file-based storage for sessions (can be upgraded to database later)
SESSIONS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "sessions")
os.makedirs(SESSIONS_DIR, exist_ok=True)

class ConversationMessage(BaseModel):
    id: str
    sender: str
    text: str
    timestamp: Optional[str] = None

class SessionData(BaseModel):
    session_id: str
    name: str
    description: Optional[str] = None
    conversation_id: Optional[str] = None
    transcript_id: Optional[str] = None
    messages: List[ConversationMessage] = Field(default_factory=list)
    graph_data: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: str
    updated_at: str
    version: int = 1

class SessionCreate(BaseModel):
    name: str
    description: Optional[str] = None
    conversation_id: Optional[str] = None
    transcript_id: Optional[str] = None
    messages: List[ConversationMessage] = Field(default_factory=list)
    graph_data: Optional[Dict[str, Any]] = None

class SessionUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    messages: Optional[List[ConversationMessage]] = None
    graph_data: Optional[Dict[str, Any]] = None

def _get_session_path(session_id: str) -> str:
    return os.path.join(SESSIONS_DIR, f"{session_id}.json")

def _load_session(session_id: str) -> Optional[SessionData]:
    path = _get_session_path(session_id)
    if not os.path.exists(path):
        return None
    try:
        with open(path, 'r') as f:
            data = json.load(f)
            return SessionData(**data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading session: {str(e)}")

def _save_session(session: SessionData):
    path = _get_session_path(session.session_id)
    try:
        with open(path, 'w') as f:
            json.dump(session.dict(), f, indent=2)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving session: {str(e)}")

def _list_sessions() -> List[SessionData]:
    sessions = []
    if not os.path.exists(SESSIONS_DIR):
        return sessions
    for filename in os.listdir(SESSIONS_DIR):
        if filename.endswith('.json'):
            session_id = filename[:-5]
            session = _load_session(session_id)
            if session:
                sessions.append(session)
    return sorted(sessions, key=lambda s: s.updated_at, reverse=True)

@router.post("/", response_model=SessionData)
def create_session(session_data: SessionCreate):
    """Create a new conversation session"""
    session_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    
    session = SessionData(
        session_id=session_id,
        name=session_data.name,
        description=session_data.description,
        conversation_id=session_data.conversation_id,
        transcript_id=session_data.transcript_id,
        messages=session_data.messages,
        graph_data=session_data.graph_data,
        created_at=now,
        updated_at=now,
        version=1
    )
    
    _save_session(session)
    return session

@router.get("/", response_model=List[SessionData])
def list_sessions():
    """List all saved sessions"""
    return _list_sessions()

@router.get("/{session_id}", response_model=SessionData)
def get_session(session_id: str):
    """Get a specific session by ID"""
    session = _load_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session

@router.put("/{session_id}", response_model=SessionData)
def update_session(session_id: str, update: SessionUpdate):
    """Update an existing session"""
    session = _load_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if update.name is not None:
        session.name = update.name
    if update.description is not None:
        session.description = update.description
    if update.messages is not None:
        session.messages = update.messages
    if update.graph_data is not None:
        session.graph_data = update.graph_data
    
    session.updated_at = datetime.utcnow().isoformat()
    session.version += 1
    
    _save_session(session)
    return session

@router.post("/{session_id}/version", response_model=SessionData)
def create_version(session_id: str):
    """Create a new version of a session (snapshot)"""
    session = _load_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Store version in metadata
    if "versions" not in session.metadata:
        session.metadata["versions"] = []
    
    version_snapshot = {
        "version": session.version,
        "created_at": session.updated_at,
        "messages": [msg.dict() for msg in session.messages],
        "graph_data": session.graph_data
    }
    session.metadata["versions"].append(version_snapshot)
    session.version += 1
    session.updated_at = datetime.utcnow().isoformat()
    
    _save_session(session)
    return session

@router.get("/{session_id}/versions", response_model=List[Dict[str, Any]])
def list_versions(session_id: str):
    """List all versions of a session"""
    session = _load_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    versions = session.metadata.get("versions", [])
    current = {
        "version": session.version,
        "created_at": session.updated_at,
        "is_current": True
    }
    return [current] + versions

@router.post("/{session_id}/restore/{version}", response_model=SessionData)
def restore_version(session_id: str, version: int):
    """Restore a session to a specific version"""
    session = _load_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    versions = session.metadata.get("versions", [])
    target_version = next((v for v in versions if v["version"] == version), None)
    
    if not target_version and version != session.version:
        raise HTTPException(status_code=404, detail="Version not found")
    
    if target_version:
        session.messages = [ConversationMessage(**msg) for msg in target_version.get("messages", [])]
        session.graph_data = target_version.get("graph_data")
    
    session.updated_at = datetime.utcnow().isoformat()
    _save_session(session)
    return session

def _normalize_node_id(node: Dict[str, Any]) -> str:
    """Get a consistent ID for a node"""
    return node.get("id", str(node))

def _normalize_link_id(link: Dict[str, Any]) -> tuple:
    """Get a consistent ID for a link"""
    source = link.get("source", "")
    target = link.get("target", "")
    if isinstance(source, dict):
        source = source.get("id", "")
    if isinstance(target, dict):
        target = target.get("id", "")
    return (str(source), str(target), link.get("type", "RELATED_TO"))

def _compare_nodes(nodes1: List[Dict], nodes2: List[Dict]) -> Dict[str, Any]:
    """Compare two sets of nodes"""
    nodes1_map = {_normalize_node_id(n): n for n in nodes1}
    nodes2_map = {_normalize_node_id(n): n for n in nodes2}
    
    added = [n for nid, n in nodes2_map.items() if nid not in nodes1_map]
    removed = [n for nid, n in nodes1_map.items() if nid not in nodes2_map]
    modified = []
    unchanged = []
    
    for nid in nodes1_map.keys() & nodes2_map.keys():
        n1, n2 = nodes1_map[nid], nodes2_map[nid]
        if n1 != n2:
            modified.append({
                "id": nid,
                "old": n1,
                "new": n2
            })
        else:
            unchanged.append(n1)
    
    return {
        "added": added,
        "removed": removed,
        "modified": modified,
        "unchanged": unchanged,
        "count_added": len(added),
        "count_removed": len(removed),
        "count_modified": len(modified),
        "count_unchanged": len(unchanged)
    }

def _compare_links(links1: List[Dict], links2: List[Dict]) -> Dict[str, Any]:
    """Compare two sets of links"""
    links1_map = {_normalize_link_id(l): l for l in links1}
    links2_map = {_normalize_link_id(l): l for l in links2}
    
    added = [l for lid, l in links2_map.items() if lid not in links1_map]
    removed = [l for lid, l in links1_map.items() if lid not in links2_map]
    modified = []
    unchanged = []
    
    for lid in links1_map.keys() & links2_map.keys():
        l1, l2 = links1_map[lid], links2_map[lid]
        if l1 != l2:
            modified.append({
                "link": lid,
                "old": l1,
                "new": l2
            })
        else:
            unchanged.append(l1)
    
    return {
        "added": added,
        "removed": removed,
        "modified": modified,
        "unchanged": unchanged,
        "count_added": len(added),
        "count_removed": len(removed),
        "count_modified": len(modified),
        "count_unchanged": len(unchanged)
    }

@router.post("/compare")
def compare_sessions(
    session_id1: str = Body(...),
    session_id2: str = Body(...)
):
    """Compare two sessions and highlight differences"""
    session1 = _load_session(session_id1)
    session2 = _load_session(session_id2)
    
    if not session1 or not session2:
        raise HTTPException(status_code=404, detail="One or both sessions not found")
    
    # Compare messages
    msg_ids1 = {msg.id for msg in session1.messages}
    msg_ids2 = {msg.id for msg in session2.messages}
    
    only_in_1 = [msg for msg in session1.messages if msg.id not in msg_ids2]
    only_in_2 = [msg for msg in session2.messages if msg.id not in msg_ids1]
    
    # Compare graph data using proper comparison logic
    graph_diff = {
        "nodes_added": [],
        "nodes_removed": [],
        "nodes_modified": [],
        "links_added": [],
        "links_removed": [],
        "links_modified": []
    }
    
    # Calculate similarity score based on graph comparison
    similarity_score = 0.0
    
    if session1.graph_data and session2.graph_data:
        nodes1 = session1.graph_data.get("nodes", [])
        nodes2 = session2.graph_data.get("nodes", [])
        links1 = session1.graph_data.get("links", [])
        links2 = session2.graph_data.get("links", [])
        
        node_diff = _compare_nodes(nodes1, nodes2)
        link_diff = _compare_links(links1, links2)
        
        graph_diff["nodes_added"] = node_diff["added"]
        graph_diff["nodes_removed"] = node_diff["removed"]
        graph_diff["nodes_modified"] = node_diff["modified"]
        graph_diff["links_added"] = link_diff["added"]
        graph_diff["links_removed"] = link_diff["removed"]
        graph_diff["links_modified"] = link_diff["modified"]
        
        # Calculate similarity based on graph structure
        # Similarity = (unchanged nodes + unchanged links) / (total nodes + total links)
        total_nodes = max(len(nodes1), len(nodes2), 1)
        total_links = max(len(links1), len(links2), 1)
        node_similarity = node_diff["count_unchanged"] / total_nodes
        link_similarity = link_diff["count_unchanged"] / total_links
        similarity_score = (node_similarity + link_similarity) / 2
    elif not session1.graph_data and not session2.graph_data:
        # Both sessions have no graph data - consider them similar if messages match
        total_messages = max(len(session1.messages), len(session2.messages), 1)
        common_messages = len(msg_ids1 & msg_ids2)
        similarity_score = common_messages / total_messages
    else:
        # One session has graph data, the other doesn't - very different
        similarity_score = 0.0
    
    return {
        "session1": {"id": session_id1, "name": session1.name, "version": session1.version},
        "session2": {"id": session_id2, "name": session2.name, "version": session2.version},
        "messages_only_in_1": [msg.dict() for msg in only_in_1],
        "messages_only_in_2": [msg.dict() for msg in only_in_2],
        "graph_differences": graph_diff,
        "similarity_score": similarity_score
    }

@router.get("/{session_id}/export")
def export_session(session_id: str, format: str = Query("json", pattern="^(json|markdown|txt)$")):
    """Export session in various formats"""
    session = _load_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if format == "json":
        return {
            "format": "json",
            "data": session.dict(),
            "content_type": "application/json"
        }
    elif format == "markdown":
        md = f"# {session.name}\n\n"
        if session.description:
            md += f"{session.description}\n\n"
        md += f"**Created:** {session.created_at}\n**Updated:** {session.updated_at}\n**Version:** {session.version}\n\n"
        md += "## Conversation\n\n"
        for msg in session.messages:
            md += f"**{msg.sender}:** {msg.text}\n\n"
        return {
            "format": "markdown",
            "data": md,
            "content_type": "text/markdown"
        }
    else:  # txt
        txt = f"{session.name}\n{'='*len(session.name)}\n\n"
        if session.description:
            txt += f"{session.description}\n\n"
        txt += f"Created: {session.created_at}\nUpdated: {session.updated_at}\nVersion: {session.version}\n\n"
        txt += "Conversation:\n" + "-"*50 + "\n"
        for msg in session.messages:
            txt += f"{msg.sender}: {msg.text}\n\n"
        return {
            "format": "txt",
            "data": txt,
            "content_type": "text/plain"
        }

@router.delete("/{session_id}")
def delete_session(session_id: str):
    """Delete a session"""
    path = _get_session_path(session_id)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Session not found")
    
    try:
        os.remove(path)
        return {"message": "Session deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting session: {str(e)}")

