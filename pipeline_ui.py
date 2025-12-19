"""Main UI module for the MRI preprocessing pipeline."""
import json

import streamlit as st

from pages.input_selection import page_input_selection
from pages.pipeline_selection import page_pipeline_selection
from pages.parameter_configuration import page_parameter_configuration
from pages.pipeline_execution import page_pipeline_execution


def load_config():
    """Load configuration from JSON file."""
    with open("cfg/config.json", "r", encoding="utf-8") as f:
        return json.load(f)

def create_sidebar():
    """Create a sidebar showing the current progress in the pipeline"""
    with st.sidebar:
        st.header("Pipeline Progress")
        steps = [
            ("Input Selection", "input_selection"),
            ("Pipeline Selection", "pipeline_selection"),
            ("Parameter Configuration", "parameter_configuration"),
            ("Pipeline Execution", "pipeline_execution")
        ]

        for step_name, step_id in steps:
            if st.session_state.current_page == step_id:
                st.markdown(f"**→ {step_name}**")
            else:
                st.markdown(f"&nbsp;&nbsp;&nbsp;{step_name}")

        st.markdown("---")
        if "experiment_data" in st.session_state:
            st.markdown("**Current Experiment:**")
            exp_name = st.session_state.experiment_data.get('experiment_name', '')
            st.markdown(f"**Name:** {exp_name}")
            mri_type = st.session_state.experiment_data.get('mri_type', '')
            st.markdown(f"**Type:** {mri_type}")
            cohort = st.session_state.experiment_data.get('cohort_name', '')
            st.markdown(f"**Cohort:** {cohort}")
            notes = st.session_state.experiment_data.get('notes', '')
            st.markdown(f"Notes: {notes}")
            img_fmt = st.session_state.experiment_data.get('image_format', '')
            st.markdown(f"Image Format: {img_fmt}")
            img_cnt = st.session_state.experiment_data.get('image_count', '')
            st.markdown(f"Image Count: {img_cnt}")
            loaded_dir = st.session_state.experiment_data.get('loaded_dir', '')
            st.markdown(f"Loaded Directory: {loaded_dir}")

def main():
    """Main function to run the MRI preprocessing pipeline UI."""
    # Set wide mode before anything else
    st.set_page_config(
        page_title="MRI Preprocessing Pipeline",
        layout="wide",  # This makes the page wide
        initial_sidebar_state="expanded"
    )

    st.title("MRI Preprocessing Pipeline")

    config = load_config()

    # Initialize session state with a deep copy of the config
    if "config" not in st.session_state:
        st.session_state.config = config.copy()

    # Initialize session state
    if "current_page" not in st.session_state:
        st.session_state.current_page = "input_selection"

    # Create sidebar
    create_sidebar()

    # Display current page
    if st.session_state.current_page == "input_selection":
        page_input_selection()
    elif st.session_state.current_page == "pipeline_selection":
        page_pipeline_selection()
    elif st.session_state.current_page == "parameter_configuration":
        page_parameter_configuration()
    elif st.session_state.current_page == "pipeline_execution":
        page_pipeline_execution()

if __name__ == "__main__":
    main()
