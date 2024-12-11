import os
import streamlit as st
import json
import uuid

from pathlib import Path
from datetime import datetime
from src.pipeline import Pipeline

def load_config():
    with open("cfg/config.json", "r") as f:
        return json.load(f)


def save_experiment_log(experiment_data):
    log_dir = Path("experiment_logs")
    log_dir.mkdir(exist_ok=True)

    # Ensure all data is JSON serializable
    serializable_data = {}
    for key, value in experiment_data.items():
        if isinstance(value, Path):
            serializable_data[key] = str(value)
        elif isinstance(value, (dict, list, str, int, float, bool, type(None))):
            serializable_data[key] = value
        else:
            serializable_data[key] = str(value)  # Convert any other types to string

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"experiment_{timestamp}_{serializable_data['experiment_name']}.json"

    try:
        with open(log_dir / filename, "w") as f:
            json.dump(serializable_data, f, indent=4)
    except Exception as e:
        st.error(f"Error saving experiment log: {str(e)}")
        return False

    return True


def page_input_selection():
    st.header("Input Selection")

    # Initialize session state if not already done
    if "experiment_data" not in st.session_state:
        st.session_state.experiment_data = {}

    # Experiment logging information
    st.subheader("Experiment Information")
    experiment_name = st.text_input(
        "Experiment Name",
        value=st.session_state.experiment_data.get("experiment_name", ""),
        key="exp_name",
    )
    cohort_name = st.text_input(
        "Cohort Name",
        value=st.session_state.experiment_data.get("cohort_name", ""),
        key="cohort_name",
    )
    notes = st.text_area(
        "Notes", value=st.session_state.experiment_data.get("notes", ""), key="notes"
    )

    # MRI type selection
    st.subheader("MRI Configuration")
    mri_type = st.selectbox(
        "Select MRI Type",
        ["fMRI", "sMRI", "DTI"],
        index=["fMRI", "sMRI", "DTI"].index(
            st.session_state.experiment_data.get("mri_type", "fMRI")
        ),
        key="mri_type",
    )

    # Image format selection
    image_format = st.selectbox(
        "Select Image Format",
        ["DICOM", "NRRD", "NIFTI"],
        index=["DICOM", "NRRD", "NIFTI"].index(
            st.session_state.experiment_data.get("image_format", "DICOM")
        ),
        key="img_format",
    )

    # Directory selection using a file uploader
    st.subheader("Directory Selection")
    st.text("Upload a dummy file from the desired directory to select it.")
    uploaded_file = st.file_uploader(
        "Choose a file from the directory", type=None, key="file_upload"
    )

    if uploaded_file is not None:
        # Extract the directory path from the uploaded file
        image_dir = Path(os.getcwd()) / "data/input/example" / uploaded_file.name
        st.success(f"Selected directory: {image_dir}")
        st.session_state.img_dir = str(image_dir)
    else:
        image_dir = st.session_state.get("img_dir", "")

    # Store the selections in session state
    if st.button("Next", key="next_button"):
        if not experiment_name or not image_dir:
            st.error("Please fill in all required fields")
            return

        # Update experiment data
        st.session_state.experiment_data.update(
            {
                "experiment_name": experiment_name,
                "cohort_name": cohort_name,
                "notes": notes,
                "mri_type": mri_type,
                "image_format": image_format,
                "image_dir": image_dir,
                "experiment_id": st.session_state.experiment_data.get(
                    "experiment_id", str(uuid.uuid4())
                ),
                "timestamp": st.session_state.experiment_data.get(
                    "timestamp", datetime.now().isoformat()
                ),
            }
        )
        st.session_state.current_page = "pipeline_selection"
        st.rerun()


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
        st.session_state.experiment_data["config"] = st.session_state.config.copy()  # Store a copy of the config
        st.session_state.current_page = "parameter_configuration"
        st.rerun()

    if st.button("Back"):
        st.session_state.current_page = "input_selection"
        st.rerun()


def page_parameter_configuration():
    st.header("Parameter Configuration")

    selected_steps = st.session_state.experiment_data["selected_steps"]
    parameters = {}

    for step in selected_steps:
        # Create expandable section for each step
        with st.expander(f"{step.replace('_', ' ').title()}", expanded=False):
            step_config = st.session_state.config[step]

            # Check if the step has methods
            if "methods" in step_config:
                # Create tabs for different methods
                method_names = list(step_config["methods"].keys())
                tabs = st.tabs(
                    [name.replace("_", " ").title() for name in method_names]
                )

                params = {"methods": {}}

                # Process each method in its own tab
                for tab, method_name in zip(tabs, method_names):
                    with tab:
                        method_config = step_config["methods"][method_name]

                        # Process method parameters
                        def process_method_parameters(config_section, current_path=[]):
                            method_params = {}
                            for key, value in config_section.items():
                                if key == "enabled":
                                    continue

                                full_path = current_path + [key]
                                param_id = "_".join([str(x) for x in full_path])

                                if isinstance(value, dict):
                                    if "enabled" in value:
                                        enabled = st.checkbox(
                                            f"Enable {key.replace('_', ' ').title()}",
                                            value=value["enabled"],
                                            key=f"checkbox_{step}_{method_name}_{param_id}",
                                        )
                                        method_params[key] = {"enabled": enabled}
                                        if enabled:
                                            method_params[key].update(
                                                process_method_parameters(
                                                    value, full_path
                                                )
                                            )
                                    else:
                                        method_params[key] = process_method_parameters(
                                            value, full_path
                                        )
                                else:
                                    # Create appropriate input field based on value type
                                    if isinstance(value, bool):
                                        method_params[key] = st.checkbox(
                                            key.replace("_", " ").title(),
                                            value=value,
                                            key=f"bool_{step}_{method_name}_{param_id}",
                                        )
                                    elif isinstance(value, (int, float)):
                                        method_params[key] = st.number_input(
                                            key.replace("_", " ").title(),
                                            value=value,
                                            key=f"num_{step}_{method_name}_{param_id}",
                                        )
                                    elif isinstance(value, list):
                                        method_params[key] = st.text_input(
                                            key.replace("_", " ").title(),
                                            value=str(value),
                                            key=f"list_{step}_{method_name}_{param_id}",
                                        )
                                    else:
                                        method_params[key] = st.text_input(
                                            key.replace("_", " ").title(),
                                            value=str(value),
                                            key=f"text_{step}_{method_name}_{param_id}",
                                        )
                            return method_params

                        # Enable/disable method
                        method_enabled = st.checkbox(
                            "Enable Method",
                            value=method_config.get("enabled", False),
                            key=f"method_enabled_{step}_{method_name}",
                        )

                        if method_enabled:
                            method_params = process_method_parameters(method_config)
                            params["methods"][method_name] = {
                                "enabled": True,
                                **method_params,
                            }
                        else:
                            params["methods"][method_name] = {"enabled": False}

            else:
                # Process regular parameters (non-method steps)
                def process_parameters(config_section, current_path=[]):
                    params = {}
                    for key, value in config_section.items():
                        if key == "enabled":
                            continue

                        full_path = current_path + [key]
                        param_id = "_".join([str(x) for x in full_path])

                        if isinstance(value, dict):
                            if "enabled" in value:
                                enabled = st.checkbox(
                                    f"Enable {key.replace('_', ' ').title()}",
                                    value=value["enabled"],
                                    key=f"checkbox_{step}_{param_id}",
                                )
                                params[key] = {"enabled": enabled}
                                if enabled:
                                    params[key].update(
                                        process_parameters(value, full_path)
                                    )
                            else:
                                params[key] = process_parameters(value, full_path)
                        else:
                            if isinstance(value, bool):
                                params[key] = st.checkbox(
                                    key.replace("_", " ").title(),
                                    value=value,
                                    key=f"bool_{step}_{param_id}",
                                )
                            elif isinstance(value, (int, float)):
                                params[key] = st.number_input(
                                    key.replace("_", " ").title(),
                                    value=value,
                                    key=f"num_{step}_{param_id}",
                                )
                            elif isinstance(value, list):
                                params[key] = st.text_input(
                                    key.replace("_", " ").title(),
                                    value=str(value),
                                    key=f"list_{step}_{param_id}",
                                )
                            else:
                                params[key] = st.text_input(
                                    key.replace("_", " ").title(),
                                    value=str(value),
                                    key=f"text_{step}_{param_id}",
                                )
                    return params

                params = process_parameters(step_config)

            parameters[step] = params

    col1, col2 = st.columns([1, 5])

    with col1:
        if st.button("Back"):
            st.session_state.current_page = "pipeline_selection"
            st.rerun()
    with col2:
        if st.button("Save and Run"):
            st.session_state.experiment_data["parameters"] = parameters
            st.session_state.experiment_data["config"] = st.session_state.config.copy()
            save_experiment_log(st.session_state.experiment_data)
            st.success("Experiment configuration saved!")
            st.session_state.current_page = "pipeline_execution"
            st.rerun()


def display_config_tree(config_data, indent=0):
    """Helper function to display config in a tree-like structure"""
    for key, value in config_data.items():
        if isinstance(value, dict):
            st.markdown("&nbsp;" * indent + f"**{key}:**")
            display_config_tree(value, indent + 2)
        else:
            st.markdown("&nbsp;" * indent + f"**{key}:** {value}")


def page_pipeline_execution():
    st.header("Pipeline Execution")

    # Create two columns: config view and terminal output
    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("Configuration Summary")
        st.markdown("---")
        
        # Display experiment info
        st.markdown("**Experiment Information:**")
        st.markdown(f"Name: {st.session_state.experiment_data['experiment_name']}")
        st.markdown(f"Cohort: {st.session_state.experiment_data['cohort_name']}")
        st.markdown(f"MRI Type: {st.session_state.experiment_data['mri_type']}")
        st.markdown(f"Image Format: {st.session_state.experiment_data['image_format']}")
        
        st.markdown("---")
        st.markdown("**Selected Steps:**")
        
        # Display enabled steps and their configurations
        config = st.session_state.experiment_data['config']
        for step in st.session_state.experiment_data['selected_steps']:
            with st.expander(f"{step.replace('_', ' ').title()}", expanded=True):
                display_config_tree(config[step])

    with col2:
        st.subheader("Pipeline Output")
        
        # Create a placeholder for terminal output
        if "terminal_output" not in st.session_state:
            st.session_state.terminal_output = []
        
        terminal_placeholder = st.empty()

        # Display terminal-like interface
        terminal_content = "\n".join(st.session_state.terminal_output)
        terminal_placeholder.text_area("Terminal Output", 
                                     value=terminal_content,
                                     height=600,
                                     key="terminal_display")
        
        # Add control buttons
        col_buttons1, col_buttons2 = st.columns([1, 4])
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
                st.session_state.terminal_output.append("Starting pipeline execution...")
                st.session_state.terminal_output.append(f"Loading configuration for experiment: {st.session_state.experiment_data['experiment_name']}")
                st.session_state.terminal_output.append("Initializing pipeline steps...")
                
                try:
                    pipeline = Pipeline(temp_config_path)
                    pipeline.run()
                    
                    st.session_state.terminal_output.append("\nPipeline execution completed!")
                except Exception as e:
                    st.session_state.terminal_output.append(f"\nError during pipeline execution: {str(e)}")
                finally:
                    # Clean up temporary config file
                    if temp_config_path.exists():
                        temp_config_path.unlink()
                
                st.rerun()


def main():
    st.title("MRI Preprocessing Pipeline")

    config = load_config()

    # Initialize session state with a deep copy of the config
    if "config" not in st.session_state:
        st.session_state.config = config.copy()

    # Initialize session state
    if "current_page" not in st.session_state:
        st.session_state.current_page = "input_selection"

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
