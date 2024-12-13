import streamlit as st

def display_config_tree(config_data, indent=0):
    """Helper function to display config in a tree-like structure"""
    for key, value in config_data.items():
        if key == "display_step":
            continue
        if isinstance(value, dict):
            st.markdown("&nbsp;" * indent + f"**{key}:**")
            display_config_tree(value, indent + 2)
        else:
            st.markdown("&nbsp;" * indent + f"**{key}:** {value}") 