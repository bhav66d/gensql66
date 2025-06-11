import re
from typing import Dict, List, Any

class SchemaParser:
    """Parse SQL schema files and extract table definitions."""
    
    KNOWN_DIALECTS = ["MySQL", "PostgreSQL", "SQLite", "MS SQL Server", "Oracle", "MariaDB"] # Expanded list

    def __init__(self):
        # Regex to find CREATE TABLE statements. Handles optional schema names and backticks.
        # Example: CREATE TABLE `tableName` (...) or CREATE TABLE schemaName.tableName (...)
        self.table_pattern = re.compile(
            r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(?:`?(\w+)`?\.?)?`?(\w+)`?\s*\((.*?)\)\s*;",
            re.IGNORECASE | re.DOTALL
        )
        # Basic column parsing - this would need to be more robust for production
        # This simplified version extracts name and type.
        self.column_pattern = re.compile(
            r"^\s*`?(\w+)`?\s+([\w\s]+(?:\([\d,\s]*\))?)([^,]*?)(?:,|\n|$)", 
            re.IGNORECASE | re.MULTILINE
        )
    
    def parse_schema(self, schema_content: str) -> Dict[str, Any]:
        """
        Parse SQL schema content and return table definitions and detected dialect.
        
        Args:
            schema_content: String containing SQL CREATE TABLE statements,
                            optionally prefixed with a dialect name on the first line 
                            (e.g., "MySQL", "-- PostgreSQL", "/* SQLite */").
            
        Returns:
            Dictionary with 'tables' (table names as keys and column definitions as values)
            and 'dialect' (detected dialect string or None).
        """
        tables = {}
        detected_dialect = None
        lines = schema_content.splitlines()
        content_to_parse = schema_content

        if lines:
            first_line_stripped = lines[0].strip()
            # Clean the first line from common comment markers for dialect detection
            # Handles "-- MySQL", "# MySQL", "/* MySQL */"
            #first_line_cleaned_for_dialect = re.sub(r"^[--#/\*\s]+|\s*[\*/]*$", "", first_line_stripped, flags=re.IGNORECASE)
            first_line_cleaned_for_dialect = re.sub(r"^[-/#\*\s]+|\s*[\*/]*$", "", first_line_stripped, flags=re.IGNORECASE)

            for dialect_candidate in self.KNOWN_DIALECTS:
                if first_line_cleaned_for_dialect.lower() == dialect_candidate.lower():
                    detected_dialect = dialect_candidate # Store the original casing
                    # If dialect is found, parse content from the second line onwards
                    content_to_parse = "\n".join(lines[1:])
                    break
        
        # Remove comments from the actual schema content that will be parsed for tables
        schema_content_no_comments = self._remove_comments(content_to_parse)
        
        matches = self.table_pattern.findall(schema_content_no_comments)

        for match_groups in matches:
            # The regex captures: (optional_schema_name, table_name, columns_text)
            db_schema_name, table_name_str, columns_text_str = match_groups
            
            actual_table_name = table_name_str.strip().lower().replace('`', '')
            if db_schema_name: # Prepend schema name if present
                actual_table_name = f"{db_schema_name.strip().lower().replace('`', '')}.{actual_table_name}"
            
            columns = self._parse_columns(columns_text_str)
            if columns: # Only add table if columns were successfully parsed
                tables[actual_table_name] = columns
        
        return {'tables': tables, 'dialect': detected_dialect}
    
    def _remove_comments(self, content: str) -> str:
            """Remove SQL comments from content."""
            # Remove single-line comments (--)
            content = re.sub(r"--.*?\n", "\n", content)
            # Remove single-line comments (#) - common in MySQL
            content = re.sub(r"#.*?\n", "\n", content)
            # Remove multi-line comments (/* ... */)
            content = re.sub(r"/\*.*?\*/", "", content, flags=re.DOTALL)
            return content.strip()
    
    def _parse_columns(self, columns_text: str) -> List[Dict[str, Any]]:
        """
        Parse column definitions from the text within table parentheses.
        This is a simplified example. A robust parser would handle constraints, 
        data type parameters (VARCHAR(255), DECIMAL(10,2)), etc., in more detail.
        """
        columns = []
        
        # Remove comments from column definitions first
        columns_text_no_comments = self._remove_comments(columns_text)

        # Split column definitions. A more robust way would be to parse token by token
        # or use a more advanced regex that handles commas within type definitions (e.g., DECIMAL(10, 2)).
        # This simple split by comma might break on complex definitions.
        potential_column_defs = []
        buffer = ""
        paren_level = 0
        for char in columns_text_no_comments:
            if char == '(':
                paren_level += 1
            elif char == ')':
                paren_level -= 1
            
            if char == ',' and paren_level == 0:
                potential_column_defs.append(buffer.strip())
                buffer = ""
            else:
                buffer += char
        if buffer.strip():
            potential_column_defs.append(buffer.strip())

        for col_def_full in potential_column_defs:
            col_def_full = col_def_full.strip()
            # Skip lines that are likely constraints defined separately (PRIMARY KEY, FOREIGN KEY, etc.)
            if not col_def_full or col_def_full.upper().startswith((
                "PRIMARY KEY", "FOREIGN KEY", "UNIQUE", "CONSTRAINT", "CHECK", "INDEX", "KEY", "TABLESPACE"
            )):
                continue

            match = self.column_pattern.match(col_def_full)
            if match:
                name = match.group(1).strip('`')
                raw_type_full = match.group(2).strip() # e.g., VARCHAR(255), INT, DECIMAL(10,2)
                
                # Basic type normalization (example)
                # This should map to types understood by DataGenerator
                data_type_lower = raw_type_full.lower()
                col_type_norm = "string" # Default
                if "int" in data_type_lower:
                    col_type_norm = "integer"
                elif "char" in data_type_lower or "text" in data_type_lower:
                    col_type_norm = "string"
                elif "float" in data_type_lower or "double" in data_type_lower or "real" in data_type_lower:
                    col_type_norm = "float"
                elif "decimal" in data_type_lower or "numeric" in data_type_lower:
                    col_type_norm = "float" # Or a specific "decimal" type if DataGenerator handles it
                elif "date" == data_type_lower or (data_type_lower.startswith("date") and '(' not in data_type_lower) : # avoid date() function
                    col_type_norm = "date"
                elif "datetime" in data_type_lower or "timestamp" in data_type_lower:
                    col_type_norm = "datetime"
                elif "bool" in data_type_lower:
                    col_type_norm = "boolean"

                columns.append({
                    'name': name,
                    'type': col_type_norm,
                    'raw_type': raw_type_full,
                    'params': {}, # Placeholder for future detailed parsing of type parameters
                    'constraints': [] # Placeholder for future detailed parsing of constraints
                })
        return columns
    
    def _split_column_definitions(self, columns_text: str) -> List[str]:
        """Split column definitions while respecting parentheses."""
        definitions = []
        current_def = ""
        paren_level = 0
        
        for char in columns_text:
            if char == '(':
                paren_level += 1
            elif char == ')':
                paren_level -= 1
            elif char == ',' and paren_level == 0:
                if current_def.strip():
                    definitions.append(current_def.strip())
                current_def = ""
                continue
            
            current_def += char
        
        if current_def.strip():
            definitions.append(current_def.strip())
        
        return definitions
    
    def _parse_single_column(self, col_def: str) -> Dict[str, Any]:
        """Parse a single column definition."""
        # Basic pattern: column_name data_type constraints
        parts = col_def.split()
        if len(parts) < 2:
            return None
        
        column_name = parts[0].strip('`"[]')
        data_type_part = parts[1]
        
        # Extract data type and size
        data_type, size = self._extract_data_type_and_size(data_type_part)
        
        # Map to standard type
        standard_type = self._map_data_type(data_type)
        
        # Extract constraints
        constraints = self._extract_constraints(' '.join(parts[1:]))
        
        # Generate additional parameters based on type and constraints
        params = self._generate_type_parameters(standard_type, size, constraints)
        
        return {
            'name': column_name,
            'type': standard_type,
            'original_type': data_type,
            'size': size,
            'constraints': constraints,
            'params': params
        }
    
    def _extract_data_type_and_size(self, data_type_part: str) -> tuple:
        """Extract data type and size from type definition."""
        # Handle types like VARCHAR(255), DECIMAL(10,2), etc.
        match = re.match(r'([a-zA-Z]+)(?:\(([^)]+)\))?', data_type_part)
        if match:
            data_type = match.group(1).lower()
            size_part = match.group(2)
            
            if size_part:
                # Handle cases like (10,2) for decimal or (255) for varchar
                if ',' in size_part:
                    parts = size_part.split(',')
                    return data_type, {'precision': int(parts[0]), 'scale': int(parts[1])}
                else:
                    return data_type, {'length': int(size_part)}
            else:
                return data_type, None
        
        return data_type_part.lower(), None
    
    def _map_data_type(self, data_type: str) -> str:
        """Map database-specific data types to standard types."""
        return self.data_type_mapping.get(data_type.lower(), 'string')
    
    def _extract_constraints(self, type_and_constraints: str) -> List[str]:
        """Extract constraints from column definition."""
        constraints = []
        upper_text = type_and_constraints.upper()
        
        constraint_patterns = [
            ('NOT NULL', 'not_null'),
            ('PRIMARY KEY', 'primary_key'),
            ('UNIQUE', 'unique'),
            ('AUTO_INCREMENT', 'auto_increment'),
            ('IDENTITY', 'auto_increment'),
            ('DEFAULT', 'default')
        ]
        
        for pattern, constraint in constraint_patterns:
            if pattern in upper_text:
                constraints.append(constraint)
                
                # Extract default value if present
                if constraint == 'default':
                    default_match = re.search(r'DEFAULT\s+([^,\s]+)', upper_text)
                    if default_match:
                        constraints.append(f"default_value:{default_match.group(1)}")
        
        return constraints
    
    def _generate_type_parameters(self, data_type: str, size: Any, constraints: List[str]) -> Dict[str, Any]:
        """Generate parameters for data generation based on type and constraints."""
        params = {}
        
        if data_type == 'integer':
            if 'auto_increment' in constraints or 'primary_key' in constraints:
                params['min_value'] = 1
                params['max_value'] = 1000000
                params['auto_increment'] = True
            else:
                params['min_value'] = 1
                params['max_value'] = 100000
        
        elif data_type == 'float':
            if size and isinstance(size, dict):
                if 'precision' in size and 'scale' in size:
                    params['precision'] = size['precision']
                    params['scale'] = size['scale']
            params['min_value'] = 0.0
            params['max_value'] = 10000.0
        
        elif data_type == 'string':
            if size and isinstance(size, dict) and 'length' in size:
                params['max_length'] = size['length']
            else:
                params['max_length'] = 255
            params['min_length'] = 1
        
        elif data_type in ['date', 'datetime']:
            params['start_date'] = '2020-01-01'
            params['end_date'] = '2024-12-31'
        
        elif data_type == 'boolean':
            params['true_probability'] = 0.5
        
        # Handle nullable
        params['nullable'] = 'not_null' not in constraints
        
        # Handle unique
        params['unique'] = 'unique' in constraints or 'primary_key' in constraints
        
        return params