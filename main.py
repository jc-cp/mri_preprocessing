"""
A script for running the MRI preprocessing pipeline.

This script defines a command-line interface for running the MRI preprocessing pipeline 
defined in the `Pipeline` class in the `pipeline.py` module.
The script takes a path to a configuration file as a command-line argument, which 
specifies the parameters.
"""
import argparse
import sys
from src.pipeline import Pipeline

def run_pipeline(config_path, streamlit_state=None):
    """
    Run the pipeline with optional Streamlit state tracking.
    
    Args:
        config_path: Path to the configuration file
        streamlit_state: Optional StreamlitSessionState for progress tracking
    """
    pipeline = Pipeline(config_path)
    pipeline.run(streamlit_state)

if __name__ == "__main__":
    # Set up command-line arguments
    parser = argparse.ArgumentParser(description="Run the MRI preprocessing pipeline.")
    parser.add_argument(
        "-cfg", "--config_path", 
        help="Path to the configuration file.", 
        default="cfg/config.json"
    )
    args = parser.parse_args()

    # Run the pipeline without Streamlit state when called from CLI
    run_pipeline(args.config_path)
