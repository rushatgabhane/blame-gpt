;; Python tree-sitter queries for code analysis

;; Functions
(function_definition) @function.def
(function_definition name: (identifier) @function.name)
(function_definition parameters: (parameters) @function.parameters)

;; Classes  
(class_definition) @class.def
(class_definition name: (identifier) @class.name)

;; Function calls
(call) @call

;; Imports
(import_statement) @import
(import_from_statement) @import_from

;; Strings (for docstrings)
(string) @string
