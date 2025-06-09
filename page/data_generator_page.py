import streamlit as st
import pandas as pd
import io
import zipfile
import random
from schema_parser import SchemaParser
from data_generator import DataGenerator
from data_analyzer import DataAnalyzer
from utils import create_sample_schema
from config.llm_config import LLMConfig

def data_generator_page():
    """Main page for data generation functionality."""
    
    # Check if we have a converted schema from the converter page
    if st.session_state.get('use_converted_schema') and st.session_state.get('converted_schema'):
        show_converted_schema_option()
    
    # Generation method selection and settings
    configure_generation_settings()
    
    # Main content based on selected method
    generation_method = st.session_state.get('generation_method', 'Schema')
    
    if generation_method == 'Converted Schema':
        converted_schema_flow()
    elif generation_method == 'Schema':
        schema_generation_flow()
    else:  # Existing Data
        existing_data_flow()

def configure_generation_settings():
    """Configure data generation options in the main content area."""
    
    with st.expander("Generation Configuration", expanded=True):
        col1, col2 = st.columns([2, 2])
        
        with col1:
            # Generation method selection
            # st.markdown("**Generation Method**")
            
            # Available methods
            methods = ["Upload Schema", "Generate from Existing Data"]
            
            # Add converted schema option if available and explicitly marked for use
            if st.session_state.get('use_converted_schema', False) and st.session_state.get('converted_schema'):
                methods.insert(0, "Use Converted Schema")
            
            # Determine the default index for the radio button
            # If 'Use Converted Schema' is available and was the last selected, make it default.
            # Otherwise, default to 'Upload Schema' or the first available method.
            default_method_index = 0
            current_generation_method = st.session_state.get('generation_method')

            if "Use Converted Schema" in methods and current_generation_method == 'Converted Schema':
                default_method_index = methods.index("Use Converted Schema")
            elif "Upload Schema" in methods and current_generation_method == 'Schema':
                default_method_index = methods.index("Upload Schema")
            elif "Generate from Existing Data" in methods and current_generation_method == 'Existing Data':
                default_method_index = methods.index("Generate from Existing Data")
            elif "Use Converted Schema" in methods: # Fallback if it's available but wasn't current
                 default_method_index = methods.index("Use Converted Schema")


            selected_method_display_name = st.radio(
                "Choose data generation method:",
                methods,
                index=default_method_index,
                help="Select how you want to generate synthetic data",
                key="generation_method_radio",
                horizontal=True
            )
            
            # Store the method selection based on internal names
            if selected_method_display_name == "Use Converted Schema":
                st.session_state.generation_method = 'Converted Schema'
            elif selected_method_display_name == "Upload Schema":
                st.session_state.generation_method = 'Schema'
            else: # "Generate from Existing Data"
                st.session_state.generation_method = 'Existing Data'
        
        with col2:
            
            # Number of samples
            num_samples = st.slider(
                "Number of samples to generate",
                min_value=10,
                max_value=10000,
                value=st.session_state.get('num_samples', 1000), # Persist value
                step=50,
                help="Number of rows to generate for each table"
            )
            st.session_state.num_samples = num_samples
        
            # Noise level for 'Generate from Existing Data'
            # Only show if that method might be selected or is selected
            if st.session_state.get('generation_method') == 'Existing Data' or "Generate from Existing Data" in methods:
                noise_level_percent = st.slider(
                    "Noise Level (%) for Existing Data Replication",
                    min_value=0,
                    max_value=50, # Percentage
                    value=st.session_state.get('noise_level', 5), # Persist value
                    step=1,
                    help="Percentage of noise to introduce when replicating existing data (0-50%)."
                )
                st.session_state.noise_level = noise_level_percent
            else:
                # Ensure noise_level is still in session_state if the option is hidden
                if 'noise_level' not in st.session_state:
                     st.session_state.noise_level = 5

def show_converted_schema_option():
    """Show information about the available converted schema."""
    
    st.markdown("""
    <div class="info-box">
        <h4>Converted Schema Available</h4>
        <p>You have a converted schema from the Schema Converter. You can use it directly for data generation!</p>
    </div>
    """, unsafe_allow_html=True)

def converted_schema_flow():
    """Handle data generation from converted schema."""
    
    st.markdown("### Generate from Converted Schema")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown("""
        <div class="option-card">
            <h4>Ready to Generate</h4>
            <p>Using the schema converted by AI. Review and generate synthetic data.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Display the schema
        with st.expander("Review Converted Schema", expanded=True):
            schema_content = st.text_area(
                "Converted Schema:",
                value=st.session_state.converted_schema,
                height=300,
                help="You can still edit the schema if needed"
            )
            
            # Update if user makes changes
            if schema_content != st.session_state.converted_schema:
                st.session_state.converted_schema = schema_content
    
    with col2:
        st.markdown("### Quick Actions")
        
        # Quick validation
        if st.button("Quick Validate", key="quick_validate"):
            validate_schema_quick(st.session_state.converted_schema)
        
        # Show generation info
        st.markdown("### Generation Info")
        st.info(f"**Samples:** {st.session_state.get('num_samples', 1000):,}")
        st.info(f"**Seed:** {st.session_state.get('random_seed', 42)}")
        st.info(f"**Relationships:** {'Yes' if st.session_state.get('preserve_relationships', True) else 'No'}")
    
    # Generate button
    if st.button("Generate Synthetic Data", type="primary", key="converted_generate"):
        process_schema(st.session_state.converted_schema, st.session_state.get('num_samples', 1000))

def schema_generation_flow():
    """Handle data generation from uploaded schema."""
    
    st.markdown("### Generate from SQL Schema File") 
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown("""
        <div class="option-card">
            <h4>Upload SQL Schema</h4>
            <p>Upload a .sql or .txt file containing CREATE TABLE statements. 
            The system will attempt to identify the SQL dialect from the first line (e.g., MySQL, PostgreSQL) 
            or use AI to normalize it if an LLM service is configured.</p>
        </div>
        """, unsafe_allow_html=True)
        
        uploaded_schema_file = st.file_uploader(
            "Upload your SQL schema file",
            type=['sql', 'txt'],
            help="Upload a .sql or .txt file. The first line can optionally specify the dialect (e.g., MySQL, PostgreSQL, SQLite, MS SQL Server).",
            key="schema_uploader"
        )
    
    with col2:
        st.markdown("### Sample & Help")
        sample_schema = create_sample_schema() # Assuming this provides a generic sample
        with st.expander("View Sample Schema Template"):
            st.code(sample_schema, language='sql')
        
        st.download_button(
            label="Download Sample Template",
            data=sample_schema,
            file_name="sample_schema.sql",
            mime="text/plain",
            help="Download a sample template to get started."
        )
        
        if not uploaded_schema_file:
            st.info("Upload a schema file. If a schema was converted in the 'Schema Converter' tab, it can also be used.")
    
    if uploaded_schema_file is not None:
        schema_content_raw = uploaded_schema_file.read().decode('utf-8')
        
        llm_service = st.session_state.get('llm_service')
        
        # Try to parse first to see if dialect is already specified by the user on the first line
        parser_check = SchemaParser()
        pre_parsed_output = parser_check.parse_schema(schema_content_raw)
        dialect_from_user = pre_parsed_output.get('dialect')

        if dialect_from_user:
            st.info(f"Dialect '{dialect_from_user}' detected from the first line of your file. Processing with this dialect.")
            process_schema(schema_content_raw, st.session_state.get('num_samples', 1000))
        elif llm_service and llm_service.is_configured:
            st.info("No dialect specified on the first line. Using AI to process and standardize the schema.")
            current_model_config = st.session_state.get('model_config', LLMConfig.DEFAULT_CONFIG.copy())
            
            # The LLM is instructed to prefix its output with the dialect.
            # We ask it to convert to a specific {output_format}.
            # Let's use "MySQL" as a common target if not specified, but the LLM should state what it used.
            # The prompt (INSTRUCTION 0) asks the LLM to state the dialect on the first line.
            target_dialect_for_llm_processing = st.session_state.get('target_dialect_llm', "MySQL") # Could be a user setting

            with st.spinner("AI is processing and standardizing your schema... This may take a moment."):
                success, normalized_schema_with_dialect, validation_msg, _, _ = \
                    llm_service.convert_schema(
                        schema_content_raw, 
                        target_dialect_for_llm_processing, # Ask LLM to aim for this output format
                        current_model_config
                    )
            
            if success and normalized_schema_with_dialect:
                st.success(f"Schema processed and standardized by AI. {validation_msg}")
                # The normalized_schema_with_dialect should have the dialect as the first line as per prompt
                process_schema(normalized_schema_with_dialect, st.session_state.get('num_samples', 1000))
            else:
                st.error(f"AI schema processing failed: {validation_msg or 'Unknown error during AI processing.'}. "
                         "Attempting to parse the original schema directly. Please ensure it's well-formed.")
                process_schema(schema_content_raw, st.session_state.get('num_samples', 1000))
        else:
            st.warning("No dialect specified on the first line, and LLM Service is not available/configured. "
                       "Attempting to parse the original schema directly. "
                       "For best results, please ensure the schema is clean or specify the dialect on the first line (e.g., MySQL, PostgreSQL).")
            process_schema(schema_content_raw, st.session_state.get('num_samples', 1000))

def existing_data_flow():
    """Handle data generation from existing data analysis."""
    
    st.markdown("""
    <div class="option-card">
        <h3>Analyze & Replicate Existing Data</h3>
        <p>Upload your CSV or Excel files. The system will analyze data patterns and generate synthetic data that maintains similar distributions and characteristics.</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        uploaded_files = st.file_uploader(
            "Upload your data files",
            type=['csv', 'xlsx', 'xls'],
            accept_multiple_files=True,
            help="Upload CSV or Excel files containing your data",
            key="data_uploader"
        )
    
    with col2:
        if uploaded_files:
            st.markdown("### File Summary")
            for file in uploaded_files:
                st.write(f"• {file.name}")
        else:
            st.markdown("### Instructions")
            st.info("Upload your data files to begin analysis and synthetic data generation.")
    
    # Process uploaded files
    if uploaded_files:
        process_existing_data(uploaded_files, st.session_state.get('num_samples', 1000), st.session_state.get('noise_level', 5))

def validate_schema_quick(schema: str):
    """Quick validation of schema."""
    
    try:
        parser = SchemaParser()
        tables = parser.parse_schema(schema)
        
        if tables:
            st.success(f"Valid schema with {len(tables)} table(s)")
            
            # Show brief table info
            for table_name, columns in tables.items():
                st.write(f"• **{table_name}**: {len(columns)} columns")
        else:
            st.error("No valid tables found")
            
    except Exception as e:
        st.error(f"Validation error: {str(e)}")

def process_schema(schema_content: str, num_samples: int):
    """Process schema content (which may have a dialect prefix) and generate data."""
    
    try:
        parser = SchemaParser()
        
        with st.spinner("Parsing schema structure..."):
            # schema_content might have the dialect prefixed either by the user,
            # or by the LLM service in the previous step.
            # SchemaParser's parse_schema method will handle this.
            parsed_output = parser.parse_schema(schema_content)
            
            tables = parsed_output.get('tables')
            detected_dialect = parsed_output.get('dialect')
            
            if detected_dialect:
                st.info(f"Schema parsing based on detected SQL Dialect: **{detected_dialect}**.")
            else:
                st.warning("No specific SQL dialect prefix was found or detected in the schema. "
                           "Parsing with general SQL rules. Results may vary depending on schema complexity.")

            if not tables:
                st.error("No valid table definitions could be parsed from the schema. "
                         "Please check the schema content and ensure it contains valid CREATE TABLE statements.")
                with st.expander("View problematic schema content"):
                    st.code(schema_content, language='sql')
                return # Stop further processing if no tables are found
        
        st.success(f"Schema parsed. Found {len(tables)} table(s) to process.")
        
        # Optionally display parsed structure for verification
        with st.expander("Review Parsed Schema Structure (for Data Generation)"):
            if tables:
                for table_name, columns in tables.items():
                    st.markdown(f"**Table: `{table_name}`**")
                    # Display column name and the type that DataGenerator will use
                    cols_data = [{"Column Name": col['name'], 
                                  "Generator Type": col['type'], 
                                  "Original SQL Type": col.get('raw_type', 'N/A')} 
                                 for col in columns]
                    st.dataframe(pd.DataFrame(cols_data))
            else:
                st.write("No tables were successfully parsed.")

        if tables:
            # Proceed to generate data using the parsed tables structure
            generate_data_from_schema(tables, num_samples)
        else:
            # This case should be caught earlier, but as a safeguard:
            st.error("Data generation cannot proceed as no tables were parsed from the schema.")
            
    except Exception as e:
        st.error(f"An error occurred while processing the schema: {str(e)}")
 
def process_existing_data(uploaded_files, num_samples: int, noise_level: int):
    """Process and analyze existing data files."""
    
    try:
        analyzer = DataAnalyzer()
        analyzed_data = {}
        
        with st.spinner("Analyzing uploaded files..."):
            for file in uploaded_files:
                file_analysis = analyzer.analyze_file(file, noise_level/100)
                analyzed_data[file.name] = file_analysis
        
        # Display analysis results
        st.success(f"Analyzed {len(uploaded_files)} file(s)")
        
        with st.expander("Data Analysis Summary", expanded=True):
            for filename, analysis in analyzed_data.items():
                st.markdown(f"**File: {filename}**")
                if isinstance(analysis, dict) and 'column_info' not in analysis:
                    # Excel with multiple sheets
                    for sheet_name, sheet_data in analysis.items():
                        st.markdown(f"*Sheet: {sheet_name}*")
                        st.write(f"Rows: {sheet_data['rows']}, Columns: {sheet_data['columns']}")
                        
                        # Display column info
                        col_info = pd.DataFrame([
                            {
                                'Column': col,
                                'Type': info['type'],
                                'Unique Values': info.get('unique_count', 'N/A'),
                                'Missing %': f"{info.get('missing_percent', 0):.1f}%"
                            }
                            for col, info in sheet_data['column_info'].items()
                        ])
                        st.dataframe(col_info, use_container_width=True)
                else:
                    # Single file (CSV)
                    st.write(f"Rows: {analysis['rows']}, Columns: {analysis['columns']}")
                    col_info = pd.DataFrame([
                        {
                            'Column': col,
                            'Type': info['type'],
                            'Unique Values': info.get('unique_count', 'N/A'),
                            'Missing %': f"{info.get('missing_percent', 0):.1f}%"
                        }
                        for col, info in analysis['column_info'].items()
                    ])
                    st.dataframe(col_info, use_container_width=True)
        
        # Generate synthetic data automatically
        generate_data_from_existing(analyzed_data, num_samples, noise_level)
    
    except Exception as e:
        st.error(f"Error analyzing files: {str(e)}")

def generate_data_from_schema(tables, num_samples: int):
    """Generate synthetic data from schema."""
    
    try:
        generator = DataGenerator()
        generated_data = {}
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        total_tables = len(tables)
        
        for i, (table_name, columns) in enumerate(tables.items()):
            status_text.text(f"Generating data for table: {table_name}")
            
            # Generate data for this table
            df = generator.generate_from_schema(columns, num_samples)
            generated_data[table_name] = df
            
            progress_bar.progress((i + 1) / total_tables)
        
        st.session_state.generated_data = generated_data
        st.session_state.generation_complete = True
        
        status_text.text("Data generation complete!")
        display_generated_data(generated_data)
        
    except Exception as e:
        st.error(f"Error generating data: {str(e)}")

def generate_data_from_existing(analyzed_data, num_samples: int, noise_level: int):
    """Generate synthetic data from existing data analysis."""
    
    try:
        generator = DataGenerator()
        generated_data = {}
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        total_files = len(analyzed_data)
        
        for i, (filename, analysis) in enumerate(analyzed_data.items()):
            status_text.text(f"Generating synthetic data for: {filename}")
            
            if isinstance(analysis, dict) and 'column_info' not in analysis:
                # Excel with multiple sheets
                file_data = {}
                for sheet_name, sheet_analysis in analysis.items():
                    df = generator.generate_from_analysis(sheet_analysis, num_samples)
                    file_data[sheet_name] = df
                generated_data[filename] = file_data
            else:
                # Single CSV file
                df = generator.generate_from_analysis(analysis, num_samples)
                generated_data[filename] = df
            
            progress_bar.progress((i + 1) / total_files)
        
        st.session_state.generated_data = generated_data
        st.session_state.generation_complete = True
        
        status_text.text("Data generation complete!")
        display_generated_data(generated_data)
        
    except Exception as e:
        st.error(f"Error generating synthetic data: {str(e)}")

def display_generated_data(generated_data):
    """Display generated data with preview and download options."""
    
    st.markdown("""
    <div class="success-box">
        <h3>Synthetic Data Generated Successfully!</h3>
        <p>Your synthetic data has been generated and is ready for download.</p>
    </div>
    """, unsafe_allow_html=True)
    
    with st.expander("Preview Generated Data", expanded=True):
        # Display preview of generated data
        for name, data in generated_data.items():
            st.subheader(f"{name}")
            if isinstance(data, dict):  # Multiple sheets/tables
                for sheet_name, df in data.items():
                    st.markdown(f"**{sheet_name}**")
                    st.dataframe(df.head(10), use_container_width=True)
                    st.caption(f"Shape: {df.shape[0]} rows × {df.shape[1]} columns")
            else:  # Single dataframe
                st.dataframe(data.head(10), use_container_width=True)
                st.caption(f"Shape: {data.shape[0]} rows × {data.shape[1]} columns")
    
    # Download section
    st.subheader("Download Generated Data")
    
    # ZIP download with all files
    st.markdown("**Package**")
    if st.button("Create ZIP Package", key="create_zip"):
        zip_buffer_value = create_zip_download(generated_data)
        st.session_state.zip_buffer_for_download = zip_buffer_value
        st.success("ZIP package created and ready for download!")

    if 'zip_buffer_for_download' in st.session_state and st.session_state.zip_buffer_for_download:
        st.download_button(
            label="Download ZIP",
            data=st.session_state.zip_buffer_for_download,
            file_name="synthetic_data_package.zip",
            mime="application/zip",
            key="download_zip_final"
        )

def create_zip_download(generated_data):
    """Create ZIP file containing all generated data."""
    
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for name, data in generated_data.items():
            if isinstance(data, dict):
                # Excel file with multiple sheets
                excel_buffer = io.BytesIO()
                with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
                    for sheet_name, df in data.items():
                        df.to_excel(writer, sheet_name=sheet_name, index=False)
                
                zip_file.writestr(f"synthetic_{name}", excel_buffer.getvalue())
                
                # Also add individual CSV files
                for sheet_name, df in data.items():
                    csv_data = df.to_csv(index=False)
                    zip_file.writestr(f"csv/synthetic_{name}_{sheet_name}.csv", csv_data)
            else:
                # CSV file
                csv_data = data.to_csv(index=False)
                clean_name = name.replace('.csv', '').replace('.xlsx', '').replace('.xls', '')
                zip_file.writestr(f"synthetic_{clean_name}.csv", csv_data)
                
                # Also create Excel version
                excel_buffer = io.BytesIO()
                with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
                    data.to_excel(writer, sheet_name='Data', index=False)
                zip_file.writestr(f"excel/synthetic_{clean_name}.xlsx", excel_buffer.getvalue())
    
    return zip_buffer.getvalue()