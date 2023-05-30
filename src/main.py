import argparse
from pipeline import Pipeline

# Set up command-line arguments
parser = argparse.ArgumentParser(description='Run the MRI preprocessing pipeline.')
parser.add_argument('-cfg', '--config_path', help='Path to the configuration file.', default='cfg/config.json')
args = parser.parse_args()

# Run the pipeline
pipeline = Pipeline(args.config_path)
pipeline.run()
