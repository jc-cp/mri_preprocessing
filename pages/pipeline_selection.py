import streamlit as st

def page_pipeline_selection():
    st.header("Pipeline Step Selection")

    if "selected_steps" not in st.session_state:
        st.session_state.selected_steps = []

    selected_steps = []

    # Dynamically create toggles for each top-level processing step
    for step, step_config in st.session_state.config.items():
        if isinstance(step_config, dict) and "enabled" in step_config:
            # Create checkbox and update config immediately when changed
            is_enabled = st.checkbox(
                step.replace("_", " ").title(),
                value=step_config["enabled"],
                key=f"step_{step}",
            )

            # Update the config with the new enabled state
            st.session_state.config[step]["enabled"] = is_enabled

            if is_enabled:
                selected_steps.append(step)

    if st.button("Next"):
        if not selected_steps:
            st.error("Please select at least one pipeline step")
            return

        # Store both selected steps and updated config
        st.session_state.selected_steps = selected_steps
        st.session_state.experiment_data["selected_steps"] = selected_steps
        st.session_state.experiment_data["config"] = st.session_state.config.copy()
        st.session_state.experiment_data["config"]["image_loading"]["file_paths"] = st.session_state.experiment_data["image_paths"]
        st.session_state.experiment_data["config"]["image_loading"]["input_dir"] = st.session_state.experiment_data["image_paths"][0].parent
        st.session_state.current_page = "parameter_configuration"
        st.rerun()

    if st.button("Back"):
        st.session_state.current_page = "input_selection"
        st.rerun() 