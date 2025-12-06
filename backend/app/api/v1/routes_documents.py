from fastapi import APIRouter, HTTPException, Body, Response
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
import json
import os
from datetime import datetime

router = APIRouter(prefix="/api/documents", tags=["documents"])

class DocumentRequest(BaseModel):
    graph_data: Dict[str, Any]
    conversation_context: Optional[List[Dict[str, Any]]] = None
    document_type: str = Field(..., description="Type: architecture, component_spec, interface_design, design_rationale")
    format: str = Field("markdown", description="Output format: markdown or pdf")
    options: Dict[str, Any] = {}

def _generate_architecture_diagram(graph_data: Dict[str, Any]) -> str:
    """Generate architecture diagram description from graph structure"""
    nodes = graph_data.get("nodes", [])
    links = graph_data.get("links", [])
    
    md = "# Architecture Diagram\n\n"
    md += "This document describes the system architecture derived from the requirement graph.\n\n"
    
    # Group nodes by type
    nodes_by_type = {}
    for node in nodes:
        node_type = node.get("label", node.get("type", "Unknown"))
        if node_type not in nodes_by_type:
            nodes_by_type[node_type] = []
        nodes_by_type[node_type].append(node)
    
    md += "## Components\n\n"
    for node_type, type_nodes in nodes_by_type.items():
        md += f"### {node_type}s\n\n"
        for node in type_nodes:
            name = node.get("name", node.get("id", "Unknown"))
            md += f"- **{name}**\n"
            props = node.get("props", {})
            for key, value in props.items():
                if key not in ["id", "name"]:
                    md += f"  - {key}: {value}\n"
        md += "\n"
    
    md += "## Relationships\n\n"
    md += "```\n"
    for link in links[:50]:  # Limit to first 50 for readability
        source_id = link.get("source", "")
        target_id = link.get("target", "")
        link_type = link.get("type", "RELATED_TO")
        
        # Try to get node names
        source_name = source_id
        target_name = target_id
        for node in nodes:
            if node.get("id") == source_id:
                source_name = node.get("name", source_id)
            if node.get("id") == target_id:
                target_name = node.get("name", target_id)
        
        md += f"{source_name} --[{link_type}]--> {target_name}\n"
    md += "```\n\n"
    
    return md

def _generate_component_spec(graph_data: Dict[str, Any], component_type: Optional[str] = None) -> str:
    """Generate component specifications from requirement nodes"""
    nodes = graph_data.get("nodes", [])
    links = graph_data.get("links", [])
    
    md = "# Component Specifications\n\n"
    md += "This document specifies components derived from requirements.\n\n"
    
    # Filter by component type if specified
    if component_type:
        nodes = [n for n in nodes if n.get("label") == component_type]
    
    for node in nodes:
        name = node.get("name", node.get("id", "Unknown"))
        node_type = node.get("label", "Component")
        props = node.get("props", {})
        
        md += f"## {name}\n\n"
        md += f"**Type:** {node_type}\n\n"
        
        # Get related requirements
        related_requirements = []
        for link in links:
            source_id = link.get("source", "")
            target_id = link.get("target", "")
            if source_id == node.get("id") or target_id == node.get("id"):
                other_id = target_id if source_id == node.get("id") else source_id
                for other_node in graph_data.get("nodes", []):
                    if other_node.get("id") == other_id and other_node.get("label") == "Requirement":
                        related_requirements.append(other_node)
        
        if related_requirements:
            md += "### Related Requirements\n\n"
            for req in related_requirements:
                req_name = req.get("name", req.get("id"))
                md += f"- {req_name}\n"
            md += "\n"
        
        # Properties
        if props:
            md += "### Properties\n\n"
            for key, value in props.items():
                if key not in ["id", "name"]:
                    md += f"- **{key}:** {value}\n"
            md += "\n"
        
        md += "---\n\n"
    
    return md

def _generate_interface_design(graph_data: Dict[str, Any]) -> str:
    """Generate interface designs from relationships"""
    nodes = graph_data.get("nodes", [])
    links = graph_data.get("links", [])
    
    md = "# Interface Design Document\n\n"
    md += "This document describes interfaces derived from relationships in the requirement graph.\n\n"
    
    # Find interface-like relationships
    interface_types = ["DEPENDS_ON", "INTERACTS_WITH", "INTEGRATES", "USES"]
    
    interfaces = []
    for link in links:
        link_type = link.get("type", "")
        if any(it in link_type for it in interface_types):
            source_id = link.get("source", "")
            target_id = link.get("target", "")
            
            source_node = next((n for n in nodes if n.get("id") == source_id), None)
            target_node = next((n for n in nodes if n.get("id") == target_id), None)
            
            if source_node and target_node:
                interfaces.append({
                    "source": source_node,
                    "target": target_node,
                    "link": link
                })
    
    md += "## Interfaces\n\n"
    for interface in interfaces:
        source_name = interface["source"].get("name", interface["source"].get("id"))
        target_name = interface["target"].get("name", interface["target"].get("id"))
        link_type = interface["link"].get("type", "RELATED_TO")
        
        md += f"### {source_name} → {target_name}\n\n"
        md += f"**Interface Type:** {link_type}\n\n"
        
        # Describe the interface
        md += f"The {source_name} component interfaces with {target_name} through a {link_type} relationship.\n\n"
        
        props = interface["link"].get("props", {})
        if props:
            md += "**Interface Properties:**\n\n"
            for key, value in props.items():
                md += f"- {key}: {value}\n"
            md += "\n"
        
        md += "---\n\n"
    
    return md

def _generate_design_rationale(graph_data: Dict[str, Any], conversation_context: Optional[List[Dict[str, Any]]] = None) -> str:
    """Generate design rationale from conversation context and graph"""
    nodes = graph_data.get("nodes", [])
    links = graph_data.get("links", [])
    
    md = "# Design Rationale\n\n"
    md += "This document provides design rationale based on requirements and discussions.\n\n"
    
    if conversation_context:
        md += "## Context from Conversations\n\n"
        for msg in conversation_context:
            sender = msg.get("sender", "Unknown")
            text = msg.get("text", "")
            md += f"**{sender}:** {text}\n\n"
    
    md += "## Design Decisions\n\n"
    
    # Group requirements by feature or stakeholder
    requirements = [n for n in nodes if n.get("label") == "Requirement"]
    features = [n for n in nodes if n.get("label") == "Feature"]
    stakeholders = [n for n in nodes if n.get("label") == "Stakeholder"]
    
    if features:
        md += "### Features and Their Requirements\n\n"
        for feature in features[:10]:  # Limit for readability
            feature_name = feature.get("name", feature.get("id"))
            md += f"#### {feature_name}\n\n"
            
            # Find related requirements
            feature_id = feature.get("id")
            related_reqs = []
            for link in links:
                source_id = link.get("source", "")
                target_id = link.get("target", "")
                if source_id == feature_id:
                    req = next((r for r in requirements if r.get("id") == target_id), None)
                    if req:
                        related_reqs.append(req)
                elif target_id == feature_id:
                    req = next((r for r in requirements if r.get("id") == source_id), None)
                    if req:
                        related_reqs.append(req)
            
            if related_reqs:
                md += "**Supporting Requirements:**\n\n"
                for req in related_reqs:
                    req_name = req.get("name", req.get("id"))
                    md += f"- {req_name}\n"
                md += "\n"
    
    if stakeholders:
        md += "### Stakeholder Priorities\n\n"
        for stakeholder in stakeholders[:10]:
            stakeholder_name = stakeholder.get("name", stakeholder.get("id"))
            md += f"- **{stakeholder_name}**\n"
            props = stakeholder.get("props", {})
            if "role" in props:
                md += f"  - Role: {props['role']}\n"
            md += "\n"
    
    md += "## Rationale Summary\n\n"
    md += f"The system design is based on {len(requirements)} requirements, "
    md += f"{len(features)} features, and {len(stakeholders)} stakeholders. "
    md += f"The relationships between these elements ({len(links)} total) "
    md += "determine the overall architecture and design decisions.\n"
    
    return md

@router.post("/generate")
def generate_document(request: DocumentRequest):
    """Generate a design document from graph structure"""
    try:
        content = ""
        
        if request.document_type == "architecture":
            content = _generate_architecture_diagram(request.graph_data)
        elif request.document_type == "component_spec":
            component_type = request.options.get("component_type")
            content = _generate_component_spec(request.graph_data, component_type)
        elif request.document_type == "interface_design":
            content = _generate_interface_design(request.graph_data)
        elif request.document_type == "design_rationale":
            content = _generate_design_rationale(request.graph_data, request.conversation_context)
        else:
            raise HTTPException(status_code=400, detail=f"Unknown document type: {request.document_type}")
        
        if request.format == "pdf":
            # For PDF, we'd need a library like reportlab or weasyprint
            # For now, return markdown and note that PDF conversion would be needed
            return {
                "format": "markdown",
                "content": content,
                "note": "PDF conversion not yet implemented. Returning markdown format."
            }
        else:
            return {
                "format": "markdown",
                "content": content,
                "document_type": request.document_type,
                "generated_at": datetime.utcnow().isoformat()
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating document: {str(e)}")

@router.post("/export")
def export_document(
    content: str = Body(..., description="Document content"),
    format: str = Body("markdown", pattern="^(markdown|pdf)$"),
    filename: Optional[str] = None
):
    """Export a document in the specified format"""
    if format == "markdown":
        return Response(
            content=content,
            media_type="text/markdown",
            headers={
                "Content-Disposition": f'attachment; filename="{filename or "document.md"}"'
            }
        )
    else:
        # PDF export would require additional libraries
        raise HTTPException(status_code=501, detail="PDF export not yet implemented")

