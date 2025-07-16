"""
Review bot controller for knowledge graph operations.
Provides API endpoints for building and querying knowledge graphs.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

from services.review_bot import KnowledgeGraphBuilder, ReviewBotConfig

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/review-bot", tags=["review-bot"])


class KnowledgeGraphBuildRequest(BaseModel):
    """Request model for knowledge graph build."""
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "password"
    use_temp_dir: bool = True


class KnowledgeGraphBuildResponse(BaseModel):
    """Response model for knowledge graph build."""
    status: str
    repository: str
    message: str
    build_id: str
    started_at: str


class KnowledgeGraphStatusResponse(BaseModel):
    """Response model for knowledge graph status."""
    build_id: str
    status: str
    repository: str
    progress: Dict[str, Any]
    result: Dict[str, Any] | None = None


# In-memory storage for build status (replace with database in production)
build_status = {}


@router.post("/build", response_model=KnowledgeGraphBuildResponse)
async def build_knowledge_graph(
    request: KnowledgeGraphBuildRequest,
    background_tasks: BackgroundTasks
):
    """
    Start building a knowledge graph for the configured repository.
    
    This endpoint starts the knowledge graph building process in the background
    and returns immediately with a build ID for tracking progress.
    """
    build_id = f"kg_build_{int(datetime.now().timestamp())}"
    
    # Initialize status tracking
    build_status[build_id] = {
        "status": "started",
        "repository": f"{ReviewBotConfig.get_repo_info()['owner']}/{ReviewBotConfig.get_repo_info()['name']}",
        "started_at": datetime.now().isoformat(),
        "progress": {
            "step": "initializing",
            "message": "Starting knowledge graph build process"
        },
        "result": None
    }
    
    # Start background task
    background_tasks.add_task(
        _build_knowledge_graph_background,
        build_id,
        request
    )
    
    return KnowledgeGraphBuildResponse(
        status="started",
        repository=build_status[build_id]["repository"],
        message="Knowledge graph build started successfully",
        build_id=build_id,
        started_at=build_status[build_id]["started_at"]
    )


@router.get("/build/{build_id}/status", response_model=KnowledgeGraphStatusResponse)
async def get_build_status(build_id: str):
    """
    Get the status of a knowledge graph build process.
    
    Args:
        build_id: The build ID returned from the build endpoint
        
    Returns:
        Current status and progress of the build
    """
    if build_id not in build_status:
        raise HTTPException(status_code=404, detail="Build ID not found")
    
    status_info = build_status[build_id]
    
    return KnowledgeGraphStatusResponse(
        build_id=build_id,
        status=status_info["status"],
        repository=status_info["repository"],
        progress=status_info["progress"],
        result=status_info.get("result")
    )


@router.get("/builds")
async def list_builds():
    """
    List all knowledge graph builds.
    
    Returns:
        List of all build statuses
    """
    return {
        "builds": [
            {
                "build_id": build_id,
                "status": info["status"],
                "repository": info["repository"],
                "started_at": info["started_at"]
            }
            for build_id, info in build_status.items()
        ]
    }


@router.delete("/build/{build_id}")
async def delete_build(build_id: str):
    """
    Delete a build record.
    
    Args:
        build_id: The build ID to delete
        
    Returns:
        Success message
    """
    if build_id not in build_status:
        raise HTTPException(status_code=404, detail="Build ID not found")
    
    del build_status[build_id]
    
    return {"message": f"Build {build_id} deleted successfully"}


async def _build_knowledge_graph_background(
    build_id: str,
    request: KnowledgeGraphBuildRequest
):
    """
    Background task to build the knowledge graph.
    
    Args:
        build_id: Unique identifier for this build
        request: Build request parameters
    """
    try:
        # Update status
        build_status[build_id]["progress"] = {
            "step": "cloning",
            "message": "Cloning repository from GitHub"
        }
        
        # Initialize builder
        builder = KnowledgeGraphBuilder(
            neo4j_uri=request.neo4j_uri,
            neo4j_user=request.neo4j_user,
            neo4j_password=request.neo4j_password,
            use_temp_dir=request.use_temp_dir
        )
        
        # Build knowledge graph
        logger.info(f"Starting knowledge graph build {build_id}")
        
        # We could add progress callbacks here to update status in real-time
        result = builder.build_knowledge_graph()
        
        # Update final status
        if result["status"] == "success":
            build_status[build_id]["status"] = "completed"
            build_status[build_id]["progress"] = {
                "step": "completed",
                "message": "Knowledge graph built successfully"
            }
        else:
            build_status[build_id]["status"] = "failed"
            build_status[build_id]["progress"] = {
                "step": "failed", 
                "message": f"Build failed: {result.get('error', 'Unknown error')}"
            }
            
        build_status[build_id]["result"] = result
        build_status[build_id]["completed_at"] = datetime.now().isoformat()
        
        logger.info(f"Knowledge graph build {build_id} completed with status: {result['status']}")
        
    except Exception as e:
        logger.exception(f"Knowledge graph build {build_id} failed with exception: {e}")
        
        build_status[build_id]["status"] = "failed"
        build_status[build_id]["progress"] = {
            "step": "failed",
            "message": f"Build failed with exception: {str(e)}"
        }
        build_status[build_id]["completed_at"] = datetime.now().isoformat()


# Health check endpoint
@router.get("/health")
async def health_check():
    """Health check endpoint for the review bot service."""
    return {
        "status": "healthy",
        "service": "review-bot",
        "timestamp": datetime.now().isoformat()
    }