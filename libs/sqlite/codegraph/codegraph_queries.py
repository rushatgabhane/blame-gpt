CREATE_TABLES = """
CREATE TABLE IF NOT EXISTS code_nodes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path TEXT NOT NULL,           -- relative path to the source file
    node_type TEXT NOT NULL,           -- 'function', 'class', 'method', 'variable', 'import'
    name TEXT NOT NULL,                -- name of the node (function name, class name, etc.)
    full_name TEXT,                    -- fully qualified name (e.g., ClassName.methodName)
    signature TEXT,                    -- function signature or class definition
    start_line INTEGER,                -- starting line number in the file
    end_line INTEGER,                  -- ending line number in the file
    content_hash TEXT,                 -- SHA256 hash of the node content
    metadata TEXT,                     -- JSON metadata (parameters, return type, etc.)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(file_path, node_type, name, start_line)
);

CREATE TABLE IF NOT EXISTS code_relationships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_node_id INTEGER NOT NULL,
    target_node_id INTEGER NOT NULL,
    relationship_type TEXT NOT NULL,   -- 'calls', 'imports', 'inherits', 'contains', 'references'
    metadata TEXT,                     -- JSON metadata about the relationship
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (source_node_id) REFERENCES code_nodes(id) ON DELETE CASCADE,
    FOREIGN KEY (target_node_id) REFERENCES code_nodes(id) ON DELETE CASCADE,
    UNIQUE(source_node_id, target_node_id, relationship_type)
);

CREATE TABLE IF NOT EXISTS code_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path TEXT NOT NULL UNIQUE,   -- relative path to the source file
    content_hash TEXT NOT NULL,       -- SHA256 hash of the file content
    language TEXT,                    -- detected programming language
    size_bytes INTEGER,               -- file size in bytes
    line_count INTEGER,               -- number of lines
    last_parsed TIMESTAMP,            -- when this file was last parsed
    parse_status TEXT DEFAULT 'pending', -- 'pending', 'success', 'error'
    parse_error TEXT,                 -- error message if parsing failed
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_code_nodes_file_path ON code_nodes(file_path);
CREATE INDEX IF NOT EXISTS idx_code_nodes_type ON code_nodes(node_type);
CREATE INDEX IF NOT EXISTS idx_code_nodes_name ON code_nodes(name);
CREATE INDEX IF NOT EXISTS idx_code_relationships_source ON code_relationships(source_node_id);
CREATE INDEX IF NOT EXISTS idx_code_relationships_target ON code_relationships(target_node_id);
CREATE INDEX IF NOT EXISTS idx_code_relationships_type ON code_relationships(relationship_type);
CREATE INDEX IF NOT EXISTS idx_code_files_path ON code_files(file_path);
CREATE INDEX IF NOT EXISTS idx_code_files_status ON code_files(parse_status);
"""

# File operations
INSERT_CODE_FILE = """
INSERT OR REPLACE INTO code_files (file_path, content_hash, language, size_bytes, line_count, last_parsed, parse_status, parse_error)
VALUES (?, ?, ?, ?, ?, ?, ?, ?);
"""

GET_CODE_FILE = """
SELECT * FROM code_files WHERE file_path = ?;
"""

GET_FILES_BY_STATUS = """
SELECT * FROM code_files WHERE parse_status = ?;
"""

UPDATE_FILE_PARSE_STATUS = """
UPDATE code_files 
SET parse_status = ?, parse_error = ?, last_parsed = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
WHERE file_path = ?;
"""

# Node operations
INSERT_CODE_NODE = """
INSERT OR REPLACE INTO code_nodes (file_path, node_type, name, full_name, signature, start_line, end_line, content_hash, metadata)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
"""

GET_NODES_BY_FILE = """
SELECT * FROM code_nodes WHERE file_path = ?;
"""

GET_NODES_BY_TYPE = """
SELECT * FROM code_nodes WHERE node_type = ?;
"""

GET_NODE_BY_ID = """
SELECT * FROM code_nodes WHERE id = ?;
"""

SEARCH_NODES = """
SELECT * FROM code_nodes 
WHERE name LIKE ? OR full_name LIKE ?
ORDER BY name;
"""

DELETE_NODES_BY_FILE = """
DELETE FROM code_nodes WHERE file_path = ?;
"""

# Relationship operations
INSERT_CODE_RELATIONSHIP = """
INSERT OR REPLACE INTO code_relationships (source_node_id, target_node_id, relationship_type, metadata)
VALUES (?, ?, ?, ?);
"""

GET_RELATIONSHIPS_FROM_NODE = """
SELECT r.*, n.name as target_name, n.node_type as target_type, n.file_path as target_file
FROM code_relationships r
JOIN code_nodes n ON r.target_node_id = n.id
WHERE r.source_node_id = ?;
"""

GET_RELATIONSHIPS_TO_NODE = """
SELECT r.*, n.name as source_name, n.node_type as source_type, n.file_path as source_file
FROM code_relationships r
JOIN code_nodes n ON r.source_node_id = n.id
WHERE r.target_node_id = ?;
"""

GET_RELATIONSHIPS_BY_TYPE = """
SELECT r.*, 
       sn.name as source_name, sn.node_type as source_type, sn.file_path as source_file,
       tn.name as target_name, tn.node_type as target_type, tn.file_path as target_file
FROM code_relationships r
JOIN code_nodes sn ON r.source_node_id = sn.id
JOIN code_nodes tn ON r.target_node_id = tn.id
WHERE r.relationship_type = ?;
"""

DELETE_RELATIONSHIPS_BY_FILE = """
DELETE FROM code_relationships 
WHERE source_node_id IN (SELECT id FROM code_nodes WHERE file_path = ?)
   OR target_node_id IN (SELECT id FROM code_nodes WHERE file_path = ?);
"""

# Query operations for graph analysis
GET_FUNCTION_CALL_GRAPH = """
SELECT r.*, 
       sn.name as caller_name, sn.file_path as caller_file,
       tn.name as callee_name, tn.file_path as callee_file
FROM code_relationships r
JOIN code_nodes sn ON r.source_node_id = sn.id
JOIN code_nodes tn ON r.target_node_id = tn.id
WHERE r.relationship_type = 'calls'
  AND sn.node_type IN ('function', 'method')
  AND tn.node_type IN ('function', 'method');
"""

GET_IMPORT_DEPENDENCIES = """
SELECT r.*, 
       sn.file_path as importing_file,
       tn.name as imported_name, tn.file_path as imported_file
FROM code_relationships r
JOIN code_nodes sn ON r.source_node_id = sn.id
JOIN code_nodes tn ON r.target_node_id = tn.id
WHERE r.relationship_type = 'imports';
"""

GET_CLASS_HIERARCHY = """
SELECT r.*, 
       sn.name as child_class, sn.file_path as child_file,
       tn.name as parent_class, tn.file_path as parent_file
FROM code_relationships r
JOIN code_nodes sn ON r.source_node_id = sn.id
JOIN code_nodes tn ON r.target_node_id = tn.id
WHERE r.relationship_type = 'inherits'
  AND sn.node_type = 'class'
  AND tn.node_type = 'class';
"""

# Statistics and summary queries
COUNT_NODES_BY_TYPE = """
SELECT node_type, COUNT(*) as count
FROM code_nodes
GROUP BY node_type
ORDER BY count DESC;
"""

COUNT_RELATIONSHIPS_BY_TYPE = """
SELECT relationship_type, COUNT(*) as count
FROM code_relationships
GROUP BY relationship_type
ORDER BY count DESC;
"""

GET_FILES_SUMMARY = """
SELECT 
    COUNT(*) as total_files,
    COUNT(CASE WHEN parse_status = 'success' THEN 1 END) as parsed_files,
    COUNT(CASE WHEN parse_status = 'error' THEN 1 END) as error_files,
    COUNT(CASE WHEN parse_status = 'pending' THEN 1 END) as pending_files
FROM code_files;
"""