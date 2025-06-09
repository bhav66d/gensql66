import streamlit as st
from google import genai
from google.genai import types
import os
from typing import Dict, Any, Optional, Tuple
import re
from config.llm_config import LLMConfig

class LLMService:
    """Service class for handling LLM interactions using google-genai with Vertex AI."""
    
    def __init__(self):
        self.client = None
        self.is_configured = False
        self.configure_vertex_ai()
    
    def configure_vertex_ai(self) -> bool:
        """
        Configure the Google GenAI client for Vertex AI using service account.
        
        Returns:
            True if configuration successful, False otherwise
        """
        try:
            # Set up Vertex AI environment
            os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "true"
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "ai-ml-team-sandbox-f9080a491656.json"
            
            # Create Vertex AI client
            self.client = genai.Client(
                vertexai=True,
                project="ai-ml-team-sandbox",  # Extracted from your JSON filename
                location="us-central1"
            )
            self.is_configured = True
            return True
        except Exception as e:
            st.error(f"Failed to configure Vertex AI client: {str(e)}")
            self.is_configured = False
            return False
    
    def test_connection(self, model_config: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Test the connection to Vertex AI.
        
        Args:
            model_config: Model configuration dictionary
            
        Returns:
            Tuple of (success, message)
        """
        if not self.is_configured:
            return False, "Vertex AI client not configured properly."
        
        try:
            response = self.client.models.generate_content(
                model=model_config["model"],
                contents="Say 'Connection successful' if you can read this.",
                config=types.GenerateContentConfig(
                    temperature=0.1,
                    max_output_tokens=50
                )
            )
            
            if response and response.text:
                return True, "Vertex AI connection successful!"
            else:
                return False, "No response received from the model."
                
        except Exception as e:
            return False, f"Connection failed: {str(e)}"
    
    def convert_schema(self, input_schema: str, output_format: str, model_config: Dict[str, Any]) -> Tuple[bool, str, str, bool, Dict[str, int]]:
        """
        Convert input schema to proper SQL format using LLM.
        
        Args:
            input_schema: Raw schema input from user
            output_format: The target SQL dialect (e.g., "MySQL", "PostgreSQL")
            model_config: Model configuration dictionary
            
        Returns:
            Tuple of (success, 
                      converted_schema_with_dialect, 
                      validation_message, 
                      is_suitable_for_data_gen, 
                      construct_counts)
        """
        if not self.is_configured:
            return False, "", "Vertex AI client not configured properly.", False, {}
        
        try:
            # Validate configuration
            validated_config = LLMConfig.validate_config(model_config)
            
            # Create the prompt
            prompt = LLMConfig.SCHEMA_CONVERSION_PROMPT.format(input_schema_or_sql=input_schema, output_format=output_format)
            
            # Generate content using Vertex AI
            generation_config = types.GenerateContentConfig(
                temperature=validated_config["temperature"],
                max_output_tokens=validated_config["max_output_tokens"],
                top_p=validated_config["top_p"],
                top_k=validated_config["top_k"]
            )
            
            response = self.client.models.generate_content(
                model=validated_config["model"],
                contents=prompt,
                config=generation_config
            )
            
            if response and response.text:
                cleaned_schema_content = self._clean_schema_response(response.text)
                schema_with_dialect = f"{output_format}\n{cleaned_schema_content}"
                
                # Correctly unpack the 3 values from _validate_converted_schema
                is_valid, validation_message, construct_counts = self._validate_converted_schema(schema_with_dialect)
                # The line below is removed as construct_counts is now received from the validation:
                # construct_counts = {}  # Since _validate_converted_schema does not return construct_counts

                # Determine suitability for data generation
                # Suitable if it has tables and no other major DDL/DML that SchemaParser won't handle.
                tables_found = construct_counts.get('tables', 0) > 0
                other_major_constructs = sum(
                    construct_counts.get(k, 0) for k in [
                        'views', 'functions', 'procedures', 'triggers', 'databases',
                        'insert_statements', 'update_statements', 'delete_statements',
                        'select_statements' # Exclude SELECT as data generator focuses on table structure
                        # 'alter_statements' could be debatable; for now, consider them as making it less straightforward
                    ]
                )
                # Allow alter statements if they are the only other thing besides tables,
                # as they might be adding constraints. This is a heuristic.
                # A more precise check would analyze the nature of ALTER statements.
                # For now, let's be strict: only tables, or tables + alters.
                # Or even stricter: only tables. Let's go with stricter for now for simplicity.
                
                is_suitable_for_data_gen = tables_found and other_major_constructs == 0

                if is_valid:
                    return True, schema_with_dialect, validation_message, is_suitable_for_data_gen, construct_counts
                else:
                    return False, schema_with_dialect, f"Schema validation failed: {validation_message}", is_suitable_for_data_gen, construct_counts
            else:
                return False, "", "No response received from the model.", False, {}
                
        except Exception as e:
            return False, "", f"Schema conversion failed: {str(e)}", False, {}
    
    def _clean_schema_response(self, response_text: str) -> str:
        """
        Clean and format the LLM response to extract SQL statements.
        Removes markdown code blocks and trims whitespace.
        
        Args:
            response_text: Raw response from LLM
            
        Returns:
            Cleaned SQL schema
        """
        # Remove markdown code blocks if present
        # Remove ```sql at the beginning
        cleaned_text = re.sub(r'^\s*```sql\s*\n?', '', response_text, flags=re.IGNORECASE)
        # Remove ``` at the end
        cleaned_text = re.sub(r'\n?\s*```\s*$', '', cleaned_text)
        # Remove any other ```
        cleaned_text = cleaned_text.replace('```', '')
        
        # Remove leading/trailing whitespace from the whole text and from each line
        lines = [line.strip() for line in cleaned_text.split('\n')]
        # Filter out empty lines that might result from stripping, but preserve structure
        # For example, don't collapse multiple intentional blank lines between statements if any.
        # However, for simplicity here, we'll just join them back.
        # If the LLM is instructed to only output SQL, extensive cleaning of non-SQL lines shouldn't be needed.
        
        # Rejoin lines and strip overall whitespace
        cleaned_schema = '\n'.join(lines).strip()
        
        return cleaned_schema
    
    def _validate_converted_schema(self, schema_text_with_dialect: str) -> Tuple[bool, str, Dict[str, int]]:
        """
        Validate the converted schema for basic SQL syntax, aware of the dialect,
        and provide a summary of detected constructs.
        The first line of schema_text_with_dialect is expected to be the SQL dialect.
        
        Args:
            schema_text_with_dialect: Converted SQL schema with dialect as the first line.
            
        Returns:
            Tuple of (is_valid, validation_message, construct_counts)
        """
        lines = schema_text_with_dialect.strip().split('\n')
        construct_counts = {} # Initialize here

        if not lines:
            return False, "Empty schema input (no dialect or content provided)", construct_counts

        dialect = lines[0].strip()
        if not dialect: # Ensure dialect line is not empty
            return False, "Dialect not specified or empty on the first line.", construct_counts

        schema_content = '\n'.join(lines[1:]).strip()

        if not schema_content:
            return False, f"Empty schema content (Dialect: {dialect})", construct_counts
        
        schema_upper = schema_content.upper()
        
        # Handle schemas that are only comments
        schema_no_comments_for_activity_check = "\n".join(
            [line for line in schema_content.split('\n') if not line.strip().startswith('--')]
        )
        if not schema_no_comments_for_activity_check.strip() and schema_content.strip().startswith('--'):
            return True, f"Schema (Dialect: {dialect}) contains only comments and is considered valid.", construct_counts

        # --- Basic Syntax Checks ---
        # 1. Mismatched parentheses
        if schema_content.count('(') != schema_content.count(')'):
            return False, f"Validation Error (Dialect: {dialect}): Mismatched parentheses.", construct_counts
        
        # --- Count SQL Constructs ---
        # construct_counts was initialized earlier
        keywords_to_count = {
            'tables': 'CREATE TABLE',
            'views': 'CREATE VIEW',
            'functions': 'CREATE FUNCTION',
            'procedures': 'CREATE PROCEDURE',
            'triggers': 'CREATE TRIGGER',
            'indexes': 'CREATE INDEX',
            'databases': 'CREATE DATABASE', 
            'alter_statements': 'ALTER ', 
            'insert_statements': 'INSERT INTO',
            'update_statements': 'UPDATE ', 
            'delete_statements': 'DELETE FROM',
            'select_statements': 'SELECT ' 
        }

        found_any_construct = False
        for construct_name, keyword in keywords_to_count.items():
            count = schema_upper.count(keyword)
            if count > 0:
                construct_counts[construct_name] = count # Use direct assignment
                found_any_construct = True
        
        if not found_any_construct and not schema_content.strip().startswith('--'): # if not just comments
             return False, f"Validation Error (Dialect: {dialect}): No common SQL DDL/DML keywords (CREATE, INSERT, SELECT, etc.) detected.", construct_counts

        # --- Further Checks (can be expanded) ---

        # --- Constructing the Validation Message ---
        summary_parts = []
        if construct_counts: # Check if dictionary is not empty
            for name, count in construct_counts.items():
                friendly_name = name.replace('_', ' ')
                summary_parts.append(f"{count} {friendly_name}")
        
        if not summary_parts: 
            # This case should ideally be caught by 'found_any_construct' check earlier
            # if it's not just comments.
            if schema_content.strip().startswith('--'): # If it was only comments
                 return True, f"Schema (Dialect: {dialect}) contains only comments and is considered valid.", construct_counts
            return True, f"Schema (Dialect: {dialect}) passed basic checks, but no specific SQL constructs were automatically counted. Please review manually.", construct_counts


        validation_message = f"Schema (Dialect: {dialect}) passed basic validation checks. Detected: {', '.join(summary_parts)}."
        return True, validation_message, construct_counts
        
    
    def get_improvement_suggestions(self, schema: str, model_config: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Get improvement suggestions for a schema.
        
        Args:
            schema: SQL schema to analyze
            model_config: Model configuration dictionary
            
        Returns:
            Tuple of (success, suggestions)
        """
        if not self.is_configured:
            return False, "Vertex AI client not configured."
        
        try:
            improvement_prompt = f"""
Analyze the following SQL schema and provide improvement suggestions:

{schema}

Please provide:
1. Missing indexes that should be added
2. Missing constraints or relationships
3. Data type optimizations
4. Naming convention improvements
5. Performance optimization suggestions

Keep suggestions concise and practical.
"""
            
            response = self.client.models.generate_content(
                model=model_config["model"],
                contents=improvement_prompt,
                config=types.GenerateContentConfig(
                    temperature=0.3,
                    max_output_tokens=1000
                )
            )
            
            if response and response.text:
                return True, response.text
            else:
                return False, "No suggestions received."
                
        except Exception as e:
            return False, f"Failed to generate suggestions: {str(e)}"