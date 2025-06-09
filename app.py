import streamlit as st
from page.schema_converter import schema_converter_page
from page.data_generator_page import data_generator_page
from config.app_config import setup_page_config, load_custom_css
from services.llm_service import LLMService
from config.llm_config import LLMConfig

def main():
    # Setup page configuration
    setup_page_config()
    
    # Load custom CSS
    load_custom_css()
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>GenSQL66</h1>
        <p>Convert schemas and generate realistic synthetic data</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize session state
    if 'converted_schema' not in st.session_state:
        st.session_state.converted_schema = None
    if 'generated_data' not in st.session_state:
        st.session_state.generated_data = {}
    if 'generation_complete' not in st.session_state:
        st.session_state.generation_complete = False
    
    if 'llm_service' not in st.session_state: # Ensure LLMService is initialized
        st.session_state.llm_service = LLMService()
    
    if 'model_config' not in st.session_state: # Ensure model_config is initialized
        st.session_state.model_config = LLMConfig.DEFAULT_CONFIG.copy()
    
    # Tab navigation
    tab1, tab2 = st.tabs(["Schema Converter", "Data Generator"])
    
    with tab1:
        schema_converter_page()
    
    with tab2:
        data_generator_page()

if __name__ == "__main__":
    main()