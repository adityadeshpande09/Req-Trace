from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import os
import uuid

router = APIRouter(prefix="/api/views", tags=["views"])

VIEWS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "views")
os.makedirs(VIEWS_DIR, exist_ok=True)

class GraphView(BaseModel):
    view_id: str
    name: str
    description: Optional[str] = None
    view_type: str = Field(..., description="Type: custom, stakeholder, dependency, feature_cluster, timeline")
    filters: Dict[str, Any] = Field(default_factory=dict)
    layout_config: Dict[str, Any] = Field(default_factory=dict)
    node_positions: Optional[Dict[str, Dict[str, float]]] = None
    active_filters: Dict[str, bool] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: str
    updated_at: str

class ViewCreate(BaseModel):
    name: str
    description: Optional[str] = None
    view_type: str
    filters: Dict[str, Any] = Field(default_factory=dict)
    layout_config: Dict[str, Any] = Field(default_factory=dict)
    node_positions: Optional[Dict[str, Dict[str, float]]] = None
    active_filters: Dict[str, bool] = Field(default_factory=dict)

class ViewUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    filters: Optional[Dict[str, Any]] = None
    layout_config: Optional[Dict[str, Any]] = None
    node_positions: Optional[Dict[str, Dict[str, float]]] = None
    active_filters: Optional[Dict[str, bool]] = None

def _get_view_path(view_id: str) -> str:
    return os.path.join(VIEWS_DIR, f"{view_id}.json")

def _load_view(view_id: str) -> Optional[GraphView]:
    path = _get_view_path(view_id)
    if not os.path.exists(path):
        return None
    try:
        with open(path, 'r') as f:
            data = json.load(f)
            return GraphView(**data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading view: {str(e)}")

def _save_view(view: GraphView):
    path = _get_view_path(view.view_id)
    try:
        with open(path, 'w') as f:
            json.dump(view.dict(), f, indent=2)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving view: {str(e)}")

def _list_views() -> List[GraphView]:
    views = []
    if not os.path.exists(VIEWS_DIR):
        return views
    for filename in os.listdir(VIEWS_DIR):
        if filename.endswith('.json'):
            view_id = filename[:-5]
            view = _load_view(view_id)
            if view:
                views.append(view)
    return sorted(views, key=lambda v: v.updated_at, reverse=True)

@router.post("/", response_model=GraphView)
def create_view(view_data: ViewCreate):
    """Create a new custom graph view"""
    view_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    
    view = GraphView(
        view_id=view_id,
        name=view_data.name,
        description=view_data.description,
        view_type=view_data.view_type,
        filters=view_data.filters,
        layout_config=view_data.layout_config,
        node_positions=view_data.node_positions,
        active_filters=view_data.active_filters,
        created_at=now,
        updated_at=now
    )
    
    _save_view(view)
    return view

@router.get("/", response_model=List[GraphView])
def list_views(view_type: Optional[str] = None):
    """List all saved views, optionally filtered by type"""
    views = _list_views()
    if view_type:
        views = [v for v in views if v.view_type == view_type]
    return views

@router.get("/{view_id}", response_model=GraphView)
def get_view(view_id: str):
    """Get a specific view by ID"""
    view = _load_view(view_id)
    if not view:
        raise HTTPException(status_code=404, detail="View not found")
    return view

@router.put("/{view_id}", response_model=GraphView)
def update_view(view_id: str, update: ViewUpdate):
    """Update an existing view"""
    view = _load_view(view_id)
    if not view:
        raise HTTPException(status_code=404, detail="View not found")
    
    if update.name is not None:
        view.name = update.name
    if update.description is not None:
        view.description = update.description
    if update.filters is not None:
        view.filters = update.filters
    if update.layout_config is not None:
        view.layout_config = update.layout_config
    if update.node_positions is not None:
        view.node_positions = update.node_positions
    if update.active_filters is not None:
        view.active_filters = update.active_filters
    
    view.updated_at = datetime.utcnow().isoformat()
    _save_view(view)
    return view

@router.delete("/{view_id}")
def delete_view(view_id: str):
    """Delete a view"""
    path = _get_view_path(view_id)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="View not found")
    
    try:
        os.remove(path)
        return {"message": "View deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting view: {str(e)}")

@router.post("/presets/stakeholder")
def create_stakeholder_view(
    stakeholder_id: Optional[str] = None,
    name: Optional[str] = None
):
    """Create a stakeholder-specific view preset"""
    view_data = ViewCreate(
        name=name or f"Stakeholder View: {stakeholder_id or 'All'}",
        description=f"View focused on stakeholder: {stakeholder_id or 'All stakeholders'}",
        view_type="stakeholder",
        filters={"stakeholder_id": stakeholder_id} if stakeholder_id else {},
        active_filters={"Stakeholder": True, "Requirement": True}
    )
    return create_view(view_data)

@router.post("/presets/dependency")
def create_dependency_view(name: Optional[str] = None):
    """Create a dependency-focused view preset"""
    view_data = ViewCreate(
        name=name or "Dependency View",
        description="View showing dependency relationships",
        view_type="dependency",
        filters={"show_dependencies": True},
        active_filters={"Requirement": True, "Feature": True, "Constraint": True}
    )
    return create_view(view_data)

@router.post("/presets/feature-cluster")
def create_feature_cluster_view(name: Optional[str] = None):
    """Create a feature cluster view preset"""
    view_data = ViewCreate(
        name=name or "Feature Cluster View",
        description="View showing feature clusters and relationships",
        view_type="feature_cluster",
        filters={"cluster_by": "feature"},
        active_filters={"Feature": True, "Requirement": True}
    )
    return create_view(view_data)

@router.post("/presets/timeline")
def create_timeline_view(name: Optional[str] = None):
    """Create a timeline view preset"""
    view_data = ViewCreate(
        name=name or "Timeline View",
        description="View showing temporal evolution of requirements",
        view_type="timeline",
        filters={"sort_by": "timestamp", "group_by_time": True},
        layout_config={"layout": "timeline", "orientation": "horizontal"}
    )
    return create_view(view_data)

