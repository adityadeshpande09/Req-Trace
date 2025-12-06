from fastapi import APIRouter, HTTPException, Body, Query
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import os
import uuid

router = APIRouter(prefix="/api/graph-comparison", tags=["graph-comparison"])

COMPARISONS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "comparisons")
os.makedirs(COMPARISONS_DIR, exist_ok=True)

class GraphVersion(BaseModel):
    version_id: str
    name: str
    graph_data: Dict[str, Any]
    timestamp: str
    metadata: Dict[str, Any] = {}

class ComparisonResult(BaseModel):
    comparison_id: str
    version1: GraphVersion
    version2: GraphVersion
    differences: Dict[str, Any]
    created_at: str

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
                "new": n2,
                "changes": _get_property_changes(n1, n2)
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
                "new": l2,
                "changes": _get_property_changes(l1.get("props", {}), l2.get("props", {}))
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

def _get_property_changes(old: Dict, new: Dict) -> Dict[str, Any]:
    """Get property-level changes between two objects"""
    changes = {}
    all_keys = set(old.keys()) | set(new.keys())
    
    for key in all_keys:
        old_val = old.get(key)
        new_val = new.get(key)
        if old_val != new_val:
            changes[key] = {"old": old_val, "new": new_val}
    
    return changes

@router.post("/compare")
def compare_graphs(
    graph1: Dict[str, Any] = Body(..., description="First graph data"),
    graph2: Dict[str, Any] = Body(..., description="Second graph data"),
    name1: Optional[str] = Body("Graph 1"),
    name2: Optional[str] = Body("Graph 2"),
    save: bool = Body(False, description="Save comparison result")
):
    """Compare two graph versions and highlight differences"""
    try:
        nodes1 = graph1.get("nodes", [])
        nodes2 = graph2.get("nodes", [])
        links1 = graph1.get("links", [])
        links2 = graph2.get("links", [])
        
        node_diff = _compare_nodes(nodes1, nodes2)
        link_diff = _compare_links(links1, links2)
        
        # Calculate similarity score
        total_nodes = max(len(nodes1), len(nodes2), 1)
        total_links = max(len(links1), len(links2), 1)
        node_similarity = node_diff["count_unchanged"] / total_nodes
        link_similarity = link_diff["count_unchanged"] / total_links
        overall_similarity = (node_similarity + link_similarity) / 2
        
        differences = {
            "nodes": node_diff,
            "links": link_diff,
            "similarity_score": overall_similarity,
            "total_changes": node_diff["count_added"] + node_diff["count_removed"] + 
                           node_diff["count_modified"] + link_diff["count_added"] + 
                           link_diff["count_removed"] + link_diff["count_modified"]
        }
        
        result = {
            "version1": {
                "version_id": str(uuid.uuid4()),
                "name": name1,
                "graph_data": graph1,
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": {}
            },
            "version2": {
                "version_id": str(uuid.uuid4()),
                "name": name2,
                "graph_data": graph2,
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": {}
            },
            "differences": differences,
            "created_at": datetime.utcnow().isoformat()
        }
        
        if save:
            comparison_id = str(uuid.uuid4())
            result["comparison_id"] = comparison_id
            path = os.path.join(COMPARISONS_DIR, f"{comparison_id}.json")
            with open(path, 'w') as f:
                json.dump(result, f, indent=2)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error comparing graphs: {str(e)}")

@router.post("/merge")
def merge_graphs(
    graph1: Dict[str, Any] = Body(..., description="First graph data"),
    graph2: Dict[str, Any] = Body(..., description="Second graph data"),
    merge_strategy: str = Body("union", pattern="^(union|intersection|prefer_first|prefer_second)$")
):
    """Merge two graphs using specified strategy"""
    try:
        nodes1 = {_normalize_node_id(n): n for n in graph1.get("nodes", [])}
        nodes2 = {_normalize_node_id(n): n for n in graph2.get("nodes", [])}
        links1 = {_normalize_link_id(l): l for l in graph1.get("links", [])}
        links2 = {_normalize_link_id(l): l for l in graph2.get("links", [])}
        
        merged_nodes = []
        merged_links = []
        
        if merge_strategy == "union":
            # Union: combine all nodes and links
            merged_nodes_map = {**nodes1, **nodes2}
            merged_links_map = {**links1, **links2}
            merged_nodes = list(merged_nodes_map.values())
            merged_links = list(merged_links_map.values())
        elif merge_strategy == "intersection":
            # Intersection: only nodes/links present in both
            merged_nodes_map = {nid: nodes1[nid] for nid in nodes1.keys() & nodes2.keys()}
            merged_links_map = {lid: links1[lid] for lid in links1.keys() & links2.keys()}
            merged_nodes = list(merged_nodes_map.values())
            merged_links = list(merged_links_map.values())
        elif merge_strategy == "prefer_first":
            # Prefer first: use graph1, add from graph2 only if not in graph1
            merged_nodes_map = {**nodes1}
            for nid, n in nodes2.items():
                if nid not in merged_nodes_map:
                    merged_nodes_map[nid] = n
            merged_links_map = {**links1}
            for lid, l in links2.items():
                if lid not in merged_links_map:
                    merged_links_map[lid] = l
            merged_nodes = list(merged_nodes_map.values())
            merged_links = list(merged_links_map.values())
        else:  # prefer_second
            # Prefer second: use graph2, add from graph1 only if not in graph2
            merged_nodes_map = {**nodes2}
            for nid, n in nodes1.items():
                if nid not in merged_nodes_map:
                    merged_nodes_map[nid] = n
            merged_links_map = {**links2}
            for lid, l in links1.items():
                if lid not in merged_links_map:
                    merged_links_map[lid] = l
            merged_nodes = list(merged_nodes_map.values())
            merged_links = list(merged_links_map.values())
        
        return {
            "merged_graph": {
                "nodes": merged_nodes,
                "links": merged_links
            },
            "statistics": {
                "nodes_from_1": len([n for n in merged_nodes if _normalize_node_id(n) in nodes1]),
                "nodes_from_2": len([n for n in merged_nodes if _normalize_node_id(n) in nodes2]),
                "links_from_1": len([l for l in merged_links if _normalize_link_id(l) in links1]),
                "links_from_2": len([l for l in merged_links if _normalize_link_id(l) in links2]),
                "total_nodes": len(merged_nodes),
                "total_links": len(merged_links)
            },
            "merge_strategy": merge_strategy
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error merging graphs: {str(e)}")

@router.post("/evolution/track")
def track_evolution(
    graph_versions: List[Dict[str, Any]] = Body(..., description="List of graph versions in chronological order")
):
    """Track evolution of a graph over time"""
    try:
        if len(graph_versions) < 2:
            raise HTTPException(status_code=400, detail="At least 2 versions required")
        
        evolution_steps = []
        for i in range(1, len(graph_versions)):
            prev = graph_versions[i-1]
            curr = graph_versions[i]
            
            nodes_prev = prev.get("nodes", [])
            nodes_curr = curr.get("nodes", [])
            links_prev = prev.get("links", [])
            links_curr = curr.get("links", [])
            
            node_diff = _compare_nodes(nodes_prev, nodes_curr)
            link_diff = _compare_links(links_prev, links_curr)
            
            evolution_steps.append({
                "from_version": i-1,
                "to_version": i,
                "timestamp": curr.get("timestamp", ""),
                "nodes_added": node_diff["count_added"],
                "nodes_removed": node_diff["count_removed"],
                "nodes_modified": node_diff["count_modified"],
                "links_added": link_diff["count_added"],
                "links_removed": link_diff["count_removed"],
                "links_modified": link_diff["count_modified"],
                "changes": {
                    "nodes": node_diff,
                    "links": link_diff
                }
            })
        
        return {
            "total_versions": len(graph_versions),
            "evolution_steps": evolution_steps,
            "summary": {
                "total_node_additions": sum(s["nodes_added"] for s in evolution_steps),
                "total_node_removals": sum(s["nodes_removed"] for s in evolution_steps),
                "total_link_additions": sum(s["links_added"] for s in evolution_steps),
                "total_link_removals": sum(s["links_removed"] for s in evolution_steps)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error tracking evolution: {str(e)}")

@router.get("/comparisons/{comparison_id}")
def get_comparison(comparison_id: str):
    """Get a saved comparison by ID"""
    path = os.path.join(COMPARISONS_DIR, f"{comparison_id}.json")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Comparison not found")
    
    with open(path, 'r') as f:
        return json.load(f)

