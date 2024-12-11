import json
from pathlib import Path
from datetime import datetime
import streamlit as st

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
            serializable_data[key] = str(value)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"experiment_{timestamp}_{serializable_data['experiment_name']}.json"

    try:
        with open(log_dir / filename, "w") as f:
            json.dump(serializable_data, f, indent=4)
    except Exception as e:
        st.error(f"Error saving experiment log: {str(e)}")
        return False
    
    return True 