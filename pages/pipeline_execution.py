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
        st.markdown("**Selected Steps:**")

        config = st.session_state.experiment_data["config"]
        for step in st.session_state.experiment_data["selected_steps"]:
            if config[step]["display_step"]:
                with st.expander(f"{step.replace('_', ' ').title()}", expanded=False):
                    display_config_tree(config[step])

    with col2:
        st.subheader("Pipeline Output")

        # Create placeholders for progress tracking
        progress_placeholder = st.empty()
        status_placeholder = st.empty()
        substep_progress_placeholder = st.empty()

        # Create a placeholder for terminal output
        if "terminal_output" not in st.session_state:
            st.session_state.terminal_output = []

        # Display progress information if available
        if "progress" in st.session_state:
            progress_placeholder.progress(st.session_state.progress, "Overall Progress")

        if "current_step" in st.session_state:
            status_placeholder.info(st.session_state.current_step)
            # Add step to terminal output
            if (
                st.session_state.terminal_output
                and st.session_state.terminal_output[-1]
                != st.session_state.current_step
            ):
                st.session_state.terminal_output.append(st.session_state.current_step)

        # Display substep progress if available
        if (
            "current_substep" in st.session_state
            and "total_substeps" in st.session_state
        ):
            substep_text = f"Step {st.session_state.current_substep} of {st.session_state.total_substeps}"
            if "substep_progress" in st.session_state:
                substep_progress_placeholder.progress(
                    st.session_state.substep_progress, substep_text
                )

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

                st.session_state.experiment_data["config"]["image_loading"]["file_paths"] = [str(path) for path in st.session_state.experiment_data["image_paths"]]
                st.session_state.experiment_data["config"]["image_loading"]["input_dir"] = str(st.session_state.experiment_data["image_paths"][0].parent)

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
                # Initialize processed_images in session state
                st.session_state.processed_images = []

                print("current_step", st.session_state.processed_images)

                pipeline = Pipeline(temp_config_path, streamlit_state=st.session_state)
                pipeline.run()

                st.session_state.terminal_output.append(
                    "\nPipeline execution completed!"
                )

                # Clean up temporary config file
                if temp_config_path.exists():
                    temp_config_path.unlink()
                st.rerun()

    # Display processed images in real-time
    if "processed_images" in st.session_state and st.session_state.processed_images:
        st.markdown("---")
        st.header("Processing Results")

        # For each image in the pipeline
        for img_data in st.session_state.processed_images:
            # Create an expander for each image
            with st.expander(f"Image: {img_data['image_name']}", expanded=True):
                if img_data["processing_steps"]:
                    # Create columns for each processing step
                    cols = st.columns(len(img_data["processing_steps"]))
                    
                    # Display each processing step result in its own column
                    for idx, (col, step_data) in enumerate(zip(cols, img_data["processing_steps"])):
                        with col:
                            st.markdown(f"**Step {idx + 1}: {step_data['current_step'].replace('_', ' ').title()}**")
                            st.image(
                                step_data["image"],
                                caption=f"After {step_data['current_step'].replace('_', ' ').title()}",
                                use_container_width=True,
                                clamp=True,
                            )
                            st.markdown(
                                f"*Step {step_data['current_substep']} of {st.session_state.total_substeps}*"
                            )
                else:
                    st.info("Processing not started or in progress...")
            
            # Add a separator between images
            st.markdown("---")
