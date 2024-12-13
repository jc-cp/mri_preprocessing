import streamlit as st
from utils.experiment_logger import save_experiment_log

def process_parameters(config_section, step, current_path=[]):
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
                        process_parameters(value, step, full_path)
                    )
            else:
                params[key] = process_parameters(value, step, full_path)
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

def process_method_parameters(config_section, step, method_name, current_path=[]):
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
                        process_method_parameters(value, step, method_name)
                    )
            else:
                method_params[key] = process_method_parameters(
                    value, step, method_name
                )
        else:
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

def page_parameter_configuration():
    st.header("Parameter Configuration")

    selected_steps = st.session_state.experiment_data["selected_steps"]
    parameters = {}

    for step in selected_steps:
        if not st.session_state.config[step]["display_step"]:
            continue
        with st.expander(f"{step.replace('_', ' ').title()}", expanded=False):
            step_config = st.session_state.config[step]
            
            if "methods" in step_config:
                method_names = list(step_config["methods"].keys())
                tabs = st.tabs([name.replace('_', ' ').title() for name in method_names])
                
                params = {"methods": {}}
                
                # Initialize the enabled method in session state if not present
                if f"enabled_method_{step}" not in st.session_state:
                    # Find the currently enabled method from config, or None if none enabled
                    current_enabled = next(
                        (name for name, config in step_config["methods"].items() 
                         if config.get("enabled", False)), 
                        None
                    )
                    st.session_state[f"enabled_method_{step}"] = current_enabled
                
                for tab, method_name in zip(tabs, method_names):
                    with tab:
                        method_config = step_config["methods"][method_name]
                        
                        # If this method is checked, uncheck all others
                        method_enabled = st.checkbox(
                            "Enable Method",
                            value=st.session_state[f"enabled_method_{step}"] == method_name,
                            key=f"method_enabled_{step}_{method_name}",
                            on_change=lambda s=step, m=method_name: set_enabled_method(s, m)
                        )

                        if method_enabled:
                            method_params = process_method_parameters(method_config, step, method_name)
                            params["methods"][method_name] = {
                                "enabled": True,
                                **method_params,
                            }
                        else:
                            params["methods"][method_name] = {"enabled": False}
            else:
                params = process_parameters(step_config, step)
            
            parameters[step] = params

    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("Back"):
            st.session_state.current_page = "pipeline_selection"
            st.rerun()
    with col2:
        if st.button("Save config"):
            st.session_state.experiment_data["parameters"] = parameters
            st.session_state.experiment_data["config"] = st.session_state.config.copy()
            save_experiment_log(st.session_state.experiment_data)
            st.success("Experiment configuration saved!")
            st.session_state.current_page = "pipeline_execution"
            st.rerun()

def set_enabled_method(step, method_name):
    """Helper function to ensure only one method is enabled at a time"""
    # If the clicked checkbox was already enabled, disable it
    if st.session_state[f"enabled_method_{step}"] == method_name:
        st.session_state[f"enabled_method_{step}"] = None
    # Otherwise, enable this method and disable all others
    else:
        st.session_state[f"enabled_method_{step}"] = method_name 
