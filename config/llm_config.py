from typing import Dict, List, Any

class LLMConfig:
    """Configuration class for LLM settings and options."""
    
    # Available models
    AVAILABLE_MODELS = {
        "gemini-2.0-flash-001": {
            "name": "Gemini 2.0 Flash",
            "description": "Latest and fastest model, great for most tasks",
            "max_tokens": 8192,
            "default_temperature": 0.1
        },
        "gemini-2.5-flash-preview-05-20": {
            "name": "Gemini 2.5 Flash Preview",
            "description": "Preview version of the next generation model",
            "max_tokens": 8192,
            "default_temperature": 0.1
        },
        "gemini-1.5-pro": {
            "name": "Gemini 1.5 Pro",
            "description": "Most capable model, best for complex schema conversion",
            "max_tokens": 8192,
            "default_temperature": 0.1
        },
        "gemini-1.5-flash": {
            "name": "Gemini 1.5 Flash",
            "description": "Faster model, good for simple schema conversions",
            "max_tokens": 8192,
            "default_temperature": 0.1
        }
    }
    
    # Default configuration
    DEFAULT_CONFIG = {
        "model": "gemini-2.0-flash-001",
        "temperature": 0.1,
        "max_output_tokens": 4096,
        "top_p": 0.95,
        "top_k": 40
    }
    
    # Schema conversion prompt template
    SCHEMA_CONVERSION_PROMPT = """
You are an expert SQL database designer and translator. Your task is to convert the provided schema, data description, or raw SQL statements into properly formatted {output_format} SQL code. 
REQUIREMENTS:
1. Detect whether the input is a schema definition, a data description in natural language, or raw SQL statements (DDL, DML, queries, functions, stored procedures, etc.).

2. For schema definitions or descriptions:
   2.1. Generate valid {output_format} DDL statements (CREATE TABLE, ALTER TABLE, etc.).
   2.2. Use appropriate data types for {output_format}, choosing from: INT/INTEGER/BIGINT/SMALLINT, VARCHAR(n), TEXT, DECIMAL(p,s), FLOAT/DOUBLE, DATE, DATETIME/TIMESTAMP, BOOLEAN/BOOL, and any dialect-specific types if needed.
   2.3. Add PRIMARY KEY, FOREIGN KEY, UNIQUE, NOT NULL, CHECK, and DEFAULT constraints where applicable.
   2.4. Assign meaningful table and column names, and include helpful inline comments.

3. For raw SQL statements (SELECT, INSERT, UPDATE, DELETE, JOINs, subqueries, stored procedures, functions, views, triggers):
   3.1. Translate syntax, functions, and built-ins into equivalent {output_format} constructs.
   3.2. Rewrite data type casts, string concatenation, date/time functions, and conditional logic to match the target dialect.
   3.3. Preserve query logic, joins, filters, grouping, ordering, and pagination semantics.
   3.4. Convert any procedural or scripting elements (e.g., T-SQL, PL/pgSQL) into the correct {output_format} procedural syntax if supported.
   3.5. If the input already closely matches {output_format} but contains errors or deprecated features, fix them and modernize to best practices.
   3.6. Ensure no errors or bugs remain in the generated SQL; validate syntax for {output_format}.
   3.7. Output only the translated SQL code—NO explanatory text, examples, or commentary. Each statement must end with a semicolon.

4. SUPPORTED DIALECTS (for {output_format}): MySQL, PostgreSQL, SQLite, MS SQL Server, Oracle, MariaDB, etc. The prompt is agnostic: choosing correct data types and syntax based solely on the {output_format}.

INSTRUCTIONS:
0. Your first line of the output should always be the SQL Dialect you are using, e.g., "MySQL", "PostgreSQL", etc in comments.
1. Identify input type (schema description vs. raw SQL).
2. Convert or correct to valid {output_format} SQL, handling both DDL and DML/procedural code as needed.
3. Use dialect-specific data types and syntax mappings.
4. Include inline comments only when defining tables or complex logic; do not add explanatory paragraphs.
5. Do not output anything except the final SQL statements.

INPUT SCHEMA/DESCRIPTION/SQL:
{input_schema_or_sql}
"""

    # Example schemas for user reference
    EXAMPLE_SCHEMAS = {
        "E-commerce": """
-- E-commerce Database Schema
CREATE TABLE customers (
    customer_id INT PRIMARY KEY AUTO_INCREMENT,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(20),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE products (
    product_id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    price DECIMAL(10,2) NOT NULL,
    stock_quantity INT DEFAULT 0,
    category VARCHAR(50),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE orders (
    order_id INT PRIMARY KEY AUTO_INCREMENT,
    customer_id INT NOT NULL,
    order_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    total_amount DECIMAL(10,2) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending'
);
""",
        "HR Management": """
-- HR Management System Schema
CREATE TABLE employees (
    employee_id INT PRIMARY KEY AUTO_INCREMENT,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    hire_date DATE NOT NULL,
    salary DECIMAL(10,2),
    department VARCHAR(50),
    position VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE departments (
    department_id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    manager_id INT,
    budget DECIMAL(12,2),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
""",
        "Student Management": """
-- Student Management System Schema
CREATE TABLE students (
    student_id INT PRIMARY KEY AUTO_INCREMENT,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    date_of_birth DATE,
    enrollment_date DATE NOT NULL,
    gpa DECIMAL(3,2),
    is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE courses (
    course_id INT PRIMARY KEY AUTO_INCREMENT,
    course_code VARCHAR(10) UNIQUE NOT NULL,
    course_name VARCHAR(200) NOT NULL,
    credits INT NOT NULL,
    instructor VARCHAR(100),
    semester VARCHAR(20)
);
"""
    }
    
    @classmethod
    def get_model_info(cls, model_id: str) -> Dict[str, Any]:
        """Get information about a specific model."""
        return cls.AVAILABLE_MODELS.get(model_id, cls.AVAILABLE_MODELS["gemini-1.5-pro"])
    
    @classmethod
    def get_model_names(cls) -> List[str]:
        """Get list of available model names."""
        return [info["name"] for info in cls.AVAILABLE_MODELS.values()]
    
    @classmethod
    def get_model_id_by_name(cls, name: str) -> str:
        """Get model ID by display name."""
        for model_id, info in cls.AVAILABLE_MODELS.items():
            if info["name"] == name:
                return model_id
        return "gemini-1.5-pro"  # Default fallback
    
    @classmethod
    def validate_config(cls, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and sanitize configuration."""
        validated_config = cls.DEFAULT_CONFIG.copy()
        
        if "model" in config and config["model"] in cls.AVAILABLE_MODELS:
            validated_config["model"] = config["model"]
        
        if "temperature" in config:
            validated_config["temperature"] = max(0.0, min(2.0, float(config["temperature"])))
        
        if "max_output_tokens" in config:
            model_info = cls.get_model_info(validated_config["model"])
            validated_config["max_output_tokens"] = max(1, min(
                model_info["max_tokens"], 
                int(config["max_output_tokens"])
            ))
        
        if "top_p" in config:
            validated_config["top_p"] = max(0.0, min(1.0, float(config["top_p"])))
        
        if "top_k" in config:
            validated_config["top_k"] = max(1, min(100, int(config["top_k"])))
        
        return validated_config