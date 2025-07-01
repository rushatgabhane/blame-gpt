from fastapi import APIRouter, Depends, Request, HTTPException, Query
from typing import cast, Optional, List
from services.codegraph_service.graph_builder import CodeGraphBuilder
from middlewares import auth_middleware
import logging

logger = logging.getLogger(__name__)

codegraph_router = APIRouter()


@codegraph_router.post(
    "/api/codegraph/index",
    dependencies=[Depends(auth_middleware.verify_internal_auth_token)],
)
async def index_directory(request: Request, directory_path: str, recursive: bool = True):
    """Index a directory to build the code graph."""
    try:
        builder = CodeGraphBuilder()
        stats = builder.index_directory(directory_path, recursive)
        builder.close()
        
        return {
            "success": True,
            "message": f"Successfully indexed {stats['processed_files']} files",
            "stats": stats
        }
    except Exception as e:
        logger.error(f"Error indexing directory: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@codegraph_router.post(
    "/api/codegraph/index-file",
    dependencies=[Depends(auth_middleware.verify_internal_auth_token)],
)
async def index_file(request: Request, file_path: str):
    """Index a single file."""
    try:
        builder = CodeGraphBuilder()
        result = builder.index_file(file_path)
        builder.close()
        
        return {
            "success": result['success'],
            "result": result
        }
    except Exception as e:
        logger.error(f"Error indexing file: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@codegraph_router.get(
    "/api/codegraph/stats",
    dependencies=[Depends(auth_middleware.verify_internal_auth_token)],
)
async def get_graph_stats(request: Request):
    """Get statistics about the code graph."""
    try:
        builder = CodeGraphBuilder()
        stats = builder.get_graph_stats()
        builder.close()
        
        return {"stats": stats}
    except Exception as e:
        logger.error(f"Error getting graph stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@codegraph_router.get(
    "/api/codegraph/search",
    dependencies=[Depends(auth_middleware.verify_internal_auth_token)],
)
async def search_nodes(
    request: Request,
    query: str = Query(..., description="Search query"),
    node_type: Optional[str] = Query(None, description="Filter by node type (function, class, etc.)")
):
    """Search for nodes in the code graph."""
    try:
        builder = CodeGraphBuilder()
        results = builder.search_nodes(query, node_type)
        builder.close()
        
        return {
            "query": query,
            "node_type": node_type,
            "results": results,
            "count": len(results)
        }
    except Exception as e:
        logger.error(f"Error searching nodes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@codegraph_router.get(
    "/api/codegraph/node/{node_id}",
    dependencies=[Depends(auth_middleware.verify_internal_auth_token)],
)
async def get_node_details(request: Request, node_id: int):
    """Get details about a specific node including its relationships."""
    try:
        builder = CodeGraphBuilder()
        
        # Get node details
        node = builder.db.get_node_by_id(node_id)
        if not node:
            raise HTTPException(status_code=404, detail="Node not found")
        
        # Get relationships
        relationships = builder.get_node_relationships(node_id)
        
        builder.close()
        
        return {
            "node": {
                "id": node.id,
                "name": node.name,
                "full_name": node.full_name,
                "type": node.node_type,
                "file_path": node.file_path,
                "signature": node.signature,
                "start_line": node.start_line,
                "end_line": node.end_line,
                "metadata": node.metadata
            },
            "relationships": relationships
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting node details: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@codegraph_router.get(
    "/api/codegraph/call-graph",
    dependencies=[Depends(auth_middleware.verify_internal_auth_token)],
)
async def get_call_graph(request: Request):
    """Get the function call graph."""
    try:
        builder = CodeGraphBuilder()
        call_graph = builder.get_function_call_graph()
        builder.close()
        
        return {
            "call_graph": call_graph,
            "count": len(call_graph)
        }
    except Exception as e:
        logger.error(f"Error getting call graph: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@codegraph_router.get(
    "/api/codegraph/imports",
    dependencies=[Depends(auth_middleware.verify_internal_auth_token)],
)
async def get_import_dependencies(request: Request):
    """Get import dependencies."""
    try:
        builder = CodeGraphBuilder()
        imports = builder.get_import_dependencies()
        builder.close()
        
        return {
            "imports": imports,
            "count": len(imports)
        }
    except Exception as e:
        logger.error(f"Error getting import dependencies: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@codegraph_router.get(
    "/api/codegraph/classes",
    dependencies=[Depends(auth_middleware.verify_internal_auth_token)],
)
async def get_class_hierarchy(request: Request):
    """Get class inheritance hierarchy."""
    try:
        builder = CodeGraphBuilder()
        hierarchy = builder.get_class_hierarchy()
        builder.close()
        
        return {
            "class_hierarchy": hierarchy,
            "count": len(hierarchy)
        }
    except Exception as e:
        logger.error(f"Error getting class hierarchy: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@codegraph_router.get(
    "/api/codegraph/nodes/{node_type}",
    dependencies=[Depends(auth_middleware.verify_internal_auth_token)],
)
async def get_nodes_by_type(request: Request, node_type: str):
    """Get all nodes of a specific type."""
    try:
        builder = CodeGraphBuilder()
        nodes = builder.db.get_nodes_by_type(node_type)
        builder.close()
        
        return {
            "node_type": node_type,
            "nodes": [
                {
                    "id": node.id,
                    "name": node.name,
                    "full_name": node.full_name,
                    "file_path": node.file_path,
                    "signature": node.signature,
                    "start_line": node.start_line,
                    "end_line": node.end_line,
                    "metadata": node.metadata
                }
                for node in nodes
            ],
            "count": len(nodes)
        }
    except Exception as e:
        logger.error(f"Error getting nodes by type: {e}")
        raise HTTPException(status_code=500, detail=str(e))