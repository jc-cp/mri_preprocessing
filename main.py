"""
A script for running the MRI preprocessing pipeline.

This script defines a command-line interface for running the MRI preprocessing pipeline 
defined in the `Pipeline` class in the `pipeline.py` module.
The script takes a path to a configuration file as a command-line argument, which 
specifies the parameters.
"""
import argparse

from src.pipeline import Pipeline

# Set up command-line arguments
parser = argparse.ArgumentParser(description="Run the MRI preprocessing pipeline.")
parser.add_argument(
    "-cfg", "--config_path", help="Path to the configuration file.", default="cfg/config.json"
)
args = parser.parse_args()

# Run the pipeline
pipeline = Pipeline(args.config_path)
pipeline.run()
