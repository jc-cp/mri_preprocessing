import streamlit as st
from pathlib import Path
import json
from src.pipeline import Pipeline
from utils.config_display import display_config_tree


def page_pipeline_execution():
    st.header("Pipeline Execution")

    # Use maximum width for columns (total should be 12 for full width)
    col1, col2 = st.columns(
        [8, 4], gap="large"
    )  # Increased ratio numbers for wider columns

    with col1:
        st.subheader("Configuration Summary")
        st.markdown("---")
        st.markdown("**Selected Steps:**")

        # Display enabled steps and their configurations
        config = st.session_state.experiment_data["config"]
        for step in st.session_state.experiment_data["selected_steps"]:
            with st.expander(f"{step.replace('_', ' ').title()}", expanded=False):
                display_config_tree(config[step])

    with col2:
        st.subheader("Pipeline Output")

        # Create a placeholder for terminal output
        if "terminal_output" not in st.session_state:
            st.session_state.terminal_output = []

        terminal_placeholder = st.empty()

        # Display terminal-like interface
        terminal_content = "\n".join(st.session_state.terminal_output)
        terminal_placeholder.text_area(
            "Terminal Output",
            value=terminal_content,
            height=300,
            key="terminal_display",
        )

        # Add control buttons
        col_buttons1, col_buttons2 = st.columns([1, 2])
        with col_buttons1:
            if st.button("Back"):
                st.session_state.current_page = "parameter_configuration"
                st.rerun()

        with col_buttons2:
            if st.button("Start Pipeline", type="primary"):
                # Save current config to a temporary file
                temp_config_path = Path("temp_config.json")
                with open(temp_config_path, "w") as f:
                    json.dump(st.session_state.experiment_data["config"], f, indent=4)

                st.session_state.terminal_output = []
                st.session_state.terminal_output.append(
                    "Starting pipeline execution..."
                )
                st.session_state.terminal_output.append(
                    f"Loading configuration for experiment: {st.session_state.experiment_data['experiment_name']}"
                )
                st.session_state.terminal_output.append(
                    "Initializing pipeline steps..."
                )

                try:
                    pipeline = Pipeline(temp_config_path, streamlit_state=st.session_state)
                    pipeline.run()

                    st.session_state.terminal_output.append(
                        "\nPipeline execution completed!"
                    )
                except Exception as e:
                    st.session_state.terminal_output.append(
                        f"\nError during pipeline execution: {str(e)}"
                    )
                finally:
                    # Clean up temporary config file
                    if temp_config_path.exists():
                        temp_config_path.unlink()

                st.rerun()
