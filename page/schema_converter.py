import streamlit as st
from services.llm_service import LLMService
from config.llm_config import LLMConfig
from schema_parser import SchemaParser
import pandas as pd

def schema_converter_page():
    """Main page for schema conversion functionality."""
    
    # Initialize LLM service
    if 'llm_service' not in st.session_state:
        st.session_state.llm_service = LLMService()
    
    # Main layout with AI configuration and schema input
    col1, col2 = st.columns([2, 1])
    
    with col1:
        schema_input_section()
    
    with col2:
        # AI Configuration in the main content area
        configure_llm_section()
        st.markdown("---")
        examples_and_help_section()
    
    # Display conversion results if available
    if st.session_state.get('converted_schema'):
        display_conversion_results()

def schema_converter_page():
    """Main page for schema conversion functionality."""
    
    # Initialize LLM service
    if 'llm_service' not in st.session_state:
        st.session_state.llm_service = LLMService()

    # AI Configuration Expander
    with st.expander("AI Configuration", expanded=True):
        configure_llm_section()
    
    # Main layout with schema input and examples/help
    col1, col2 = st.columns([2, 1])
    
    with col1:
        schema_input_section()
    
    with col2:
        examples_and_help_section()
    
    # Display conversion results if available
    if st.session_state.get('converted_schema'):
        display_conversion_results()

def configure_llm_section():
    """Configure LLM settings."""
    
    # Model selection
    model_names = LLMConfig.get_model_names()
    selected_model_name = st.selectbox(
        "AI Model",
        model_names,
        help="Choose the AI model for schema conversion"
    )
    
    selected_model_id = LLMConfig.get_model_id_by_name(selected_model_name)
    model_info = LLMConfig.get_model_info(selected_model_id)
    
    st.info(f"**{model_info['name']}**\n{model_info['description']}")
    
    # Advanced settings in tabs
    tab1, tab2 = st.tabs(["Sampling", "Output"])
    
    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            temperature = col1.slider(
                "Temperature",
                min_value=0.0,
                max_value=2.0,
                value=model_info['default_temperature'],
                step=0.1,
                help="Controls randomness. Lower = more consistent"
            )
        with col2:
            top_p = col2.slider(
                "Top P",
                min_value=0.1,
                max_value=1.0,
                value=0.95,
                step=0.05,
                help="Controls diversity of output"
            )
    
    with tab2:
        col1, col2 = st.columns(2)
        with col1:
            max_tokens = col1.slider(
                "Max Output Tokens",
                min_value=100,
                max_value=model_info['max_tokens'],
                value=min(4096, model_info['max_tokens']),
                step=100,
                help="Maximum length of generated response"
            )

        with col2:
            top_k = col2.slider(
                "Top K",
            min_value=1,
            max_value=100,
            value=40,
            step=1,
            help="Limits vocabulary for each step"
        )
    
    # Store configuration in session state
    st.session_state.model_config = {
        "model": selected_model_id,
        "temperature": temperature,
        "max_output_tokens": max_tokens,
        "top_p": top_p,
        "top_k": top_k
    }

def schema_input_section():
    """Handle schema input and conversion."""
    
    st.markdown("""
    <div class="option-card">
        <h3>Input Your Schema</h3>
        <p>Upload a file or paste your schema/description below. The AI will convert it to proper SQL format.</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([0.8, 1])
    with col1:
        # Input method selection
        input_method = st.radio(
            "Choose input method:",
            ["Upload File", "Text Input"],
            horizontal=True
        )
    
    with col2:
        output_format = st.radio(
            "Convert to SQL Dialect:",
            ["MySQL", "PostgreSQL", "SQLite", "MS SQL Server"],
            horizontal=True
        )

    schema_input = ""

    if input_method == "Upload File":
        uploaded_file = st.file_uploader(
            "Upload schema file",
            type=['sql', 'txt'],
            help="Upload any file containing schema information"
        )
        
        if uploaded_file:
            try:
                schema_input = uploaded_file.read().decode('utf-8')
                st.text_area(
                    "File content preview:",
                    value=schema_input[:1000] + ("..." if len(schema_input) > 1000 else ""),
                    height=200,
                    disabled=True
                )
            except Exception as e:
                st.error(f"Error reading file: {str(e)}")
                return
    
    else:  # Text input
        schema_input = st.text_area(
            "Paste your schema or describe your data structure:",
            height=200,
            placeholder="""You can paste:
- Existing SQL schema (even if malformed)
- JSON schema
- Table descriptions in plain text
- CSV headers with data types
- Any other format describing your data structure

Example:
"I need a database for an online store with customers, products, and orders. 
Customers have names, emails, and addresses. Products have names, prices, and categories. 
Orders connect customers to products with quantities and dates."
"""
        )
    
    # Conversion button
    if schema_input and output_format and st.button("Convert Schema", type="primary"):
        if not hasattr(st.session_state, 'model_config'):
            st.error("Please configure the AI settings first.")
            return
        
        convert_schema(schema_input, output_format)

def convert_schema(input_schema: str, output_format: str):
    """Convert the input schema using LLM."""
    
    with st.spinner("Converting schema using AI..."):
        success, converted_schema, error_message, is_suitable_for_data_gen, construct_counts = st.session_state.llm_service.convert_schema(
            input_schema,
            output_format,
            st.session_state.model_config
        )
        
        st.session_state.converted_schema = converted_schema # Store even on failure if partial is returned
        st.session_state.is_suitable_for_data_gen = is_suitable_for_data_gen
        st.session_state.schema_construct_counts = construct_counts
        st.session_state.conversion_validation_message = error_message # Store the validation message

        if success:
            st.success("Schema converted successfully!")
            # The error_message here is actually the validation_message from LLMService
            if "validation failed" not in error_message.lower() and "error" not in error_message.lower():
                 st.info(f"Validation: {error_message}") # Show positive validation result
            else:
                 st.warning(f"Validation: {error_message}") # Show warning/error from validation
                
        else:
            st.error(f"Conversion failed: {error_message}") # This is the primary error from conversion
            if converted_schema:
                st.warning("Partial result available above - please review carefully.")

def examples_and_help_section():
    """Show examples and help information."""
    
    st.markdown("### Examples & Help")
    
    # Example schemas
    with st.expander("Example Schemas"):
        example_type = st.selectbox(
            "Choose example:",
            list(LLMConfig.EXAMPLE_SCHEMAS.keys()),
            key="example_selector"
        )
        
        st.code(LLMConfig.EXAMPLE_SCHEMAS[example_type], language='sql', wrap_lines=True)
        
        if st.button(f"Use {example_type} Example", key="use_example"):
            st.session_state.converted_schema = LLMConfig.EXAMPLE_SCHEMAS[example_type]
            st.success("Example loaded! Check the results below.")
    
    # Input format help
    with st.expander("Input Formats"):
        st.markdown("""
        **AI can convert:**
        
        • **Malformed SQL** - Fix syntax, add constraints
        
        • **Plain Text** - "I need a user table with name, email"
        
        • **JSON Schema** - Convert to SQL tables
        
        • **CSV Headers** - Column names to table structure
        
        • **Business Requirements** - Descriptions to SQL
        """)
    
    # Troubleshooting
    with st.expander("Troubleshooting"):
        st.markdown("""
        **Common Issues:**
        
        • **No response** - Check Vertex AI connection
        
        • **Invalid schema** - Review output, edit manually
        
        • **Rate limit** - Wait and try again
        
        **Tips:**
        - Be specific about data types
        - Mention relationships
        - Include constraints
        """)

def display_conversion_results():
    """Display the converted schema results."""
    
    st.markdown("---")
    st.subheader("Conversion Results")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown("""
        <div class="conversion-result">
            <h4>Converted SQL Schema</h4>
            <p>Review the generated schema and make any necessary adjustments.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Display the converted schema
        edited_schema = st.text_area(
            "Generated SQL Schema:",
            value=st.session_state.get('converted_schema', ''), 
            height=400,
            key="text_area_converted_schema", 
            help="You can edit the schema before using it for data generation"
        )
        
        if edited_schema != st.session_state.get('converted_schema', ''):
            st.session_state.converted_schema = edited_schema
            # Re-validate or at least clear suitability if user edits manually
            # For simplicity, we'll let the existing validation button handle re-validation.
            # Manual edits might change suitability.
            st.session_state.is_suitable_for_data_gen = False # Assume not suitable after manual edit until re-validated
            st.info("Schema edited. Please re-validate if you intend to use it for data generation with specific checks.")

    
    with col2:
        st.markdown("### Actions")
        
        if st.button("Validate Schema", key="validate_schema_button"): 
            if 'converted_schema' in st.session_state and st.session_state.converted_schema:
                # Use the stored validation message from the last conversion, or re-validate
                # For simplicity, let's call the validation function which will display messages
                validate_converted_schema(st.session_state.converted_schema)
            else:
                st.warning("There is no schema to validate.")
        
        if st.button("Get Suggestions", key="suggestions"):
            if 'converted_schema' in st.session_state and st.session_state.converted_schema:
                get_schema_suggestions(st.session_state.converted_schema)
            else:
                st.warning("There is no schema to get suggestions for.")

        # Dynamically generate the file name
        file_name = "converted_schema.sql"  # Default name
        if 'output_format' in st.session_state and 'uploaded_file' in st.session_state and st.session_state.uploaded_file:
            output_format = st.session_state.output_format.replace(" ", "_")
            original_file_name = st.session_state.uploaded_file.name.split(".")[0]
            file_name = f"{output_format}_{original_file_name}.sql"
        elif 'output_format' in st.session_state:
            output_format = st.session_state.output_format.replace(" ", "_")
            file_name = f"{output_format}_converted_schema.sql"

        st.download_button(
            label="Download Schema",
            data=st.session_state.get('converted_schema', ''),
            file_name=file_name,
            mime="text/plain"
        )
        
        is_suitable = st.session_state.get('is_suitable_for_data_gen', False)
        use_for_gen_button = st.button(
            "Use for Data Generation", 
            type="primary", 
            key="use_for_generation",
            disabled=not is_suitable
        )

        if use_for_gen_button:
            st.session_state.use_converted_schema = True
            st.success("Schema marked for data generation!")
            st.info("Switch to the 'Data Generator' tab to continue.")
        
        if not is_suitable and st.session_state.get('converted_schema'):
            # Explain why it might be disabled if a schema exists
            counts = st.session_state.get('schema_construct_counts', {})
            if counts.get('tables', 0) == 0:
                st.warning("Data generation requires `CREATE TABLE` statements. None found.")
            else:
                other_constructs_details = []
                for k, v in counts.items():
                    if k != 'tables' and v > 0:
                        other_constructs_details.append(f"{v} {k.replace('_', ' ')}")
                if other_constructs_details:
                    st.warning(f"Data generation is best with only `CREATE TABLE` statements. Found: {', '.join(other_constructs_details)}. Please simplify the schema or ensure it's primarily table definitions.")
                elif not counts: # No counts but schema exists
                     st.warning("Schema suitability for data generation could not be determined. Please ensure it contains valid CREATE TABLE statements.")

def validate_converted_schema(schema: str):
    """
    Validate the converted schema using the LLM service's more general validation logic.
    This expects the schema string to have the SQL dialect as its first line.
    """
    if not schema.strip():
        st.warning("Schema is empty. Nothing to validate.")
        return

    if 'llm_service' not in st.session_state or not st.session_state.llm_service:
        st.error("LLM Service not initialized. Cannot validate schema.")
        return
    
    is_valid, validation_message, construct_counts = st.session_state.llm_service._validate_converted_schema(schema)
    
    # Update session state with the results of this explicit validation
    st.session_state.schema_construct_counts = construct_counts
    tables_found = construct_counts.get('tables', 0) > 0
    other_major_constructs = sum(
        construct_counts.get(k, 0) for k in [
            'views', 'functions', 'procedures', 'triggers', 'databases',
            'insert_statements', 'update_statements', 'delete_statements',
            'select_statements'
        ]
    )
    st.session_state.is_suitable_for_data_gen = tables_found and other_major_constructs == 0

    if is_valid:
        st.success(f"✅ Schema Validation: {validation_message}")
    else:
        st.error(f"❌ Schema Validation: {validation_message}")

def get_schema_suggestions(schema: str):
    """Get improvement suggestions for the schema."""
    
    if not hasattr(st.session_state, 'model_config'):
        st.error("Please configure LLM settings first.")
        return
    
    with st.spinner("🤖 Analyzing schema for improvements..."):
        success, suggestions = st.session_state.llm_service.get_improvement_suggestions(
            schema, 
            st.session_state.model_config
        )
        
        if success:
            st.markdown("### 💡 Improvement Suggestions:")
            st.markdown(suggestions)
        else:
            st.error(f"❌ Failed to get suggestions: {suggestions}")