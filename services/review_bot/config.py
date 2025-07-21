"""
Configuration settings for the review bot knowledge graph builder.
"""

import os
from pathlib import Path
from typing import Dict, Any


class ReviewBotConfig:
    """Configuration class for review bot settings."""
    
    # Neo4j Configuration
    NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")
    
    # File discovery settings
    SUPPORTED_EXTENSIONS = [".js", ".jsx", ".ts", ".tsx"]
    EXCLUDE_PATTERNS = [
        "test", "spec", "__tests__", "node_modules", 
        ".git", "dist", "build", "coverage"
    ]
    
    # Source directory configuration
    DEFAULT_SRC_DIR = "src"
    
    # Processing settings
    BATCH_SIZE = 50  # For progress updates
    
    # Smart filtering settings
    ENABLE_SMART_FILTERING = os.getenv("ENABLE_SMART_FILTERING", "true").lower() == "true"
    MAX_SECONDARY_IMPACTS = int(os.getenv("MAX_SECONDARY_IMPACTS", "80"))
    MIN_CENTRALITY_THRESHOLD = int(os.getenv("MIN_CENTRALITY_THRESHOLD", "5"))
    MIN_ORCHESTRATOR_THRESHOLD = int(os.getenv("MIN_ORCHESTRATOR_THRESHOLD", "10"))
    
    # Docker Neo4j settings (for local development)
    NEO4J_DOCKER_IMAGE = "neo4j:5.20"
    NEO4J_CONTAINER_NAME = "neo4j-kg"
    NEO4J_HTTP_PORT = 7474
    NEO4J_BOLT_PORT = 7687
    
    @classmethod
    def get_neo4j_config(cls) -> Dict[str, str]:
        """Get Neo4j connection configuration."""
        return {
            "uri": cls.NEO4J_URI,
            "user": cls.NEO4J_USER,
            "password": cls.NEO4J_PASSWORD
        }
    
    @classmethod
    def get_file_discovery_config(cls) -> Dict[str, Any]:
        """Get file discovery configuration."""
        return {
            "extensions": cls.SUPPORTED_EXTENSIONS,
            "exclude_patterns": cls.EXCLUDE_PATTERNS,
            "src_dir": cls.DEFAULT_SRC_DIR
        }
    
    @classmethod
    def get_smart_filtering_config(cls) -> Dict[str, Any]:
        """Get smart filtering configuration."""
        return {
            "enabled": cls.ENABLE_SMART_FILTERING,
            "max_secondary_impacts": cls.MAX_SECONDARY_IMPACTS,
            "min_centrality_threshold": cls.MIN_CENTRALITY_THRESHOLD,
            "min_orchestrator_threshold": cls.MIN_ORCHESTRATOR_THRESHOLD
        }
    
    @classmethod
    def validate_repository(cls, repo_path: Path) -> bool:
        """
        Validate that the given path is a valid git repository.
        
        Args:
            repo_path: Path to check
            
        Returns:
            True if valid repository, False otherwise
        """
        return (
            repo_path.exists() and
            repo_path.is_dir() and
            (repo_path / ".git").exists()
        )
    
    @classmethod
    def get_src_directory(cls, repo_path: Path) -> Path:
        """
        Get the source directory for the repository.
        
        Args:
            repo_path: Repository root path
            
        Returns:
            Path to source directory
        """
        return repo_path / cls.DEFAULT_SRC_DIR
    
    @classmethod 
    def get_repo_info(cls) -> Dict[str, str]:
        """
        Get repository information from constants.
        
        Returns:
            Dictionary with owner and name
        """
        from libs import constants
        return {
            "owner": constants.REPO_OWNER,
            "name": constants.REPO_NAME
        }