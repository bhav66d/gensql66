import streamlit as st
import base64
import io
from typing import Any

def download_button(label: str, data: Any, file_name: str, mime: str, help: str = None) -> bool:
    """
    Create a download button for data.
    
    Args:
        label: Button label
        data: Data to download
        file_name: Name of the downloaded file
        mime: MIME type
        help: Help text
        
    Returns:
        True if button was clicked
    """
    return st.download_button(
        label=label,
        data=data,
        file_name=file_name,
        mime=mime,
        help=help
    )

def create_sample_schema() -> str:
    """
    Create a sample SQL schema for demonstration.
    
    Returns:
        String containing sample SQL schema
    """
    schema = """-- Sample Database Schema for E-commerce Platform
-- This is a template showing how to structure your SQL schema

-- Users table
CREATE TABLE users (
    user_id INT PRIMARY KEY AUTO_INCREMENT,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(20),
    date_of_birth DATE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Products table
CREATE TABLE products (
    product_id INT PRIMARY KEY AUTO_INCREMENT,
    product_name VARCHAR(200) NOT NULL,
    description TEXT,
    price DECIMAL(10,2) NOT NULL,
    stock_quantity INT DEFAULT 0,
    category VARCHAR(50),
    weight FLOAT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_available BOOLEAN DEFAULT TRUE
);

-- Orders table
CREATE TABLE orders (
    order_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    order_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    total_amount DECIMAL(10,2) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    shipping_address TEXT,
    discount_percent FLOAT DEFAULT 0.0,
    is_paid BOOLEAN DEFAULT FALSE
);

-- Comments for your reference:
-- - Use standard SQL data types (INT, VARCHAR, TEXT, DECIMAL, DATETIME, BOOLEAN)
-- - PRIMARY KEY and AUTO_INCREMENT for ID fields
-- - NOT NULL for required fields
-- - DEFAULT values where appropriate
-- - UNIQUE constraints for unique fields
-- - Specify VARCHAR lengths for string fields
-- - Use DECIMAL(precision, scale) for monetary values
"""
    return schema

def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human readable format.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted size string
    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"

def validate_schema_content(content: str) -> tuple[bool, str]:
    """
    Validate if the content looks like a valid SQL schema.
    
    Args:
        content: Schema content to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    content_upper = content.upper()
    
    if 'CREATE TABLE' not in content_upper:
        return False, "No CREATE TABLE statements found in the schema."
    
    # Check for basic SQL syntax
    if content_upper.count('(') != content_upper.count(')'):
        return False, "Mismatched parentheses in the schema."
    
    return True, ""

def get_data_type_color(data_type: str) -> str:
    """
    Get color for data type visualization.
    
    Args:
        data_type: Data type name
        
    Returns:
        Hex color code
    """
    color_map = {
        'integer': '#FF6B6B',      # Red
        'float': '#4ECDC4',        # Teal
        'string': '#45B7D1',       # Blue
        'date': '#96CEB4',         # Green
        'datetime': '#FECA57',     # Yellow
        'boolean': '#FF9FF3',      # Pink
        'numeric': '#4ECDC4',      # Teal
        'categorical': '#45B7D1',  # Blue
    }
    
    return color_map.get(data_type.lower(), '#95A5A6')  # Default gray

def create_progress_bar(current: int, total: int, prefix: str = "") -> str:
    """
    Create a text-based progress bar.
    
    Args:
        current: Current progress
        total: Total items
        prefix: Prefix text
        
    Returns:
        Progress bar string
    """
    percentage = int((current / total) * 100) if total > 0 else 0
    bar_length = 30
    filled_length = int(bar_length * current // total) if total > 0 else 0
    
    bar = '█' * filled_length + '-' * (bar_length - filled_length)
    return f"{prefix} |{bar}| {percentage}% ({current}/{total})"

def safe_column_name(name: str) -> str:
    """
    Make a column name safe for use in DataFrames.
    
    Args:
        name: Original column name
        
    Returns:
        Safe column name
    """
    # Remove special characters and replace with underscore
    import re
    safe_name = re.sub(r'[^\w\s]', '_', name)
    safe_name = re.sub(r'\s+', '_', safe_name)
    safe_name = safe_name.strip('_')
    
    # Ensure it doesn't start with a number
    if safe_name and safe_name[0].isdigit():
        safe_name = f"col_{safe_name}"
    
    return safe_name or "unnamed_column"

def estimate_generation_time(num_samples: int, num_columns: int) -> str:
    """
    Estimate time needed for data generation.
    
    Args:
        num_samples: Number of samples to generate
        num_columns: Number of columns
        
    Returns:
        Estimated time string
    """
    # Rough estimation: 1000 samples per second per column
    total_operations = num_samples * num_columns
    estimated_seconds = total_operations / 10000  # Conservative estimate
    
    if estimated_seconds < 1:
        return "< 1 second"
    elif estimated_seconds < 60:
        return f"~{int(estimated_seconds)} seconds"
    else:
        minutes = int(estimated_seconds / 60)
        return f"~{minutes} minute{'s' if minutes > 1 else ''}"

def display_success_message(message: str, details: str = None):
    """
    Display a formatted success message.
    
    Args:
        message: Main success message
        details: Optional details
    """
    st.success(f"✅ {message}")
    if details:
        st.info(f"ℹ️ {details}")

def display_error_message(message: str, details: str = None):
    """
    Display a formatted error message.
    
    Args:
        message: Main error message
        details: Optional error details
    """
    st.error(f"❌ {message}")
    if details:
        with st.expander("Error Details"):
            st.code(details)

def display_warning_message(message: str, details: str = None):
    """
    Display a formatted warning message.
    
    Args:
        message: Main warning message
        details: Optional warning details
    """
    st.warning(f"⚠️ {message}")
    if details:
        st.info(f"ℹ️ {details}")

class ProgressTracker:
    """Helper class to track progress across multiple operations."""
    
    def __init__(self, total_steps: int, description: str = "Processing"):
        self.total_steps = total_steps
        self.current_step = 0
        self.description = description
        self.progress_bar = st.progress(0)
        self.status_text = st.empty()
        
    def update(self, step_description: str = None):
        """Update progress by one step."""
        self.current_step += 1
        progress = self.current_step / self.total_steps
        self.progress_bar.progress(progress)
        
        if step_description:
            self.status_text.text(f"{self.description}: {step_description}")
        else:
            self.status_text.text(f"{self.description}: Step {self.current_step}/{self.total_steps}")
    
    def complete(self, final_message: str = "Complete!"):
        """Mark progress as complete."""
        self.progress_bar.progress(1.0)
        self.status_text.text(f"✅ {final_message}")
    
    def error(self, error_message: str):
        """Mark progress as error."""
        self.status_text.text(f"❌ {error_message}")