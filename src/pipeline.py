"""
A preprocessing pipeline for medical images.

This script defines a `Pipeline` class that can be used to run a preprocessing 
pipeline on a set of medical images.
The pipeline consists of several preprocessing steps, such as registration, 
resampling, skull stripping, and normalization.
The pipeline can be configured using a JSON configuration file.

Example usage:
    # Load configuration from file
    with open("config.json", "r") as f:
        config = json.load(f)

    # Create pipeline instance
    pipeline = Pipeline(config)

    # Run pipeline on images
    pipeline.run()
"""
import json
import logging
from src.preprocessing.quality_control import QualityControl
from src.preprocessing.bias_field_correction import BiasFieldCorrection
from src.preprocessing.binning import Binning
from src.preprocessing.denoising import Denoising
from src.preprocessing.filtering import Filtering
from src.preprocessing.normalization import Normalization
from src.preprocessing.registration import Registration
from src.preprocessing.resampling import Resampling
from src.preprocessing.skull_stripping import SkullStripping
from src.utils.image_conversion import ImageConversion
from src.utils.image_loading import ImageLoading
from src.utils.image_saving import ImageSaving
from src.utils.image_visualization import ImageVisualization
import streamlit as st

class Pipeline:
    """
    A class for running a preprocessing pipeline on a set of medical images.

    Args:
        config (dict): A dictionary containing configuration parameters for the pipeline.

    Attributes:
        config (dict): A dictionary containing configuration parameters for the pipeline.
        preprocessing_steps (dict): A dictionary mapping step names to step classes.
        image_loading (ImageLoading): An instance of a class for loading images.
        image_conversion (ImageConversion): An instance of a class for converting images.
        image_saving (ImageSaving): An instance of a class for saving images.
        image_visualization (ImageVisualization): An instance of a class for visualizing images.

    Methods:
        run(): Runs the preprocessing pipeline on the specified images.
    """

    def __init__(self, config_file, streamlit_state=None):
        logging.basicConfig(
            filename="preprocessing.log",
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        # Read configuration
        try:
            with open(config_file, "r", encoding="utf-8") as file:
                self.config = json.load(file)
            print("Successfully loaded configuration file.")
        except (IOError, FileNotFoundError) as error:
            print(f"Error loading configuration file: {error}")

        # Map step names to classes, attention: the order here becomes relevant!
        self.step_classes = {
            "quality_control": QualityControl,
            # add here motion correction 
            # add here slice timing correction
            "bias_field_correction": BiasFieldCorrection,
            "resampling": Resampling,
            "registration": Registration,
            #"skull_stripping": SkullStripping,
            "denoising": Denoising,
            "normalization": Normalization,
            #"filtering": Filtering,
            #"binning": Binning
            # add other preprocessing steps...
        }

        # Initialize utility functions
        self.image_loading = ImageLoading(self.config["image_loading"])
        self.image_conversion = ImageConversion(self.config["image_conversion"])
        self.image_saving = ImageSaving(self.config["image_saving"])
        self.image_visualization = ImageVisualization(self.config["image_visualization"])

        self.streamlit_state = streamlit_state

    def run(self):
        """
        Runs the preprocessing pipeline on the specified images one-by-one.

        Args:
            streamlit_state: Optional StreamlitSessionState to update progress

        Raises:
            ExceptionGroup: If any exception occurs during pipeline execution.
        """
        try:
            total_images = len(list(self.image_loading.run()))  # Get total number of images
            current_image = 0
            
            if self.streamlit_state is not None:
                self.streamlit_state.total_images = total_images
                self.streamlit_state.current_image = current_image
                self.streamlit_state.current_step = "Starting pipeline..."
                self.streamlit_state.progress = 0.0

            for image, path in self.image_loading.run():
                current_image += 1
                if self.streamlit_state is not None:
                    self.streamlit_state.current_image = current_image
                    self.streamlit_state.current_step = f"Processing image {current_image}/{total_images}"
                    self.streamlit_state.progress = current_image / total_images

                # Do conversion to Nifti if needed
                if self.config["image_conversion"]["enabled"]:
                    if self.streamlit_state is not None:
                        self.streamlit_state.current_step = "Converting to NIfTI..."
                    image = self.image_conversion.run(path)

                # Save initial image and template for later visualization
                initial_image = image
                print(f"Initial image has shape: {initial_image.shape}")

                # Apply preprocessing steps
                processed_data_by_step, applied_steps = self.apply_steps(
                    image, 
                    path, 
                )

                self.image_saving.run(image, path)
                if self.config["image_visualization"]["enabled"]:
                    if self.streamlit_state is not None:
                        self.streamlit_state.current_step = "Generating visualizations..."
                    template_image = self.config["registration"]["reference"]
                    self.image_visualization.run(
                        initial_image,
                        template_image,
                        processed_data_by_step,
                        applied_steps,
                    )

            if self.streamlit_state is not None:
                self.streamlit_state.current_step = "Pipeline completed!"
                self.streamlit_state.progress = 1.0

        except Exception as error:
            if self.streamlit_state is not None:
                self.streamlit_state.current_step = f"Error: {str(error)}"
            print(f"Error running pipeline: {error}")

    def apply_steps(self, image, image_path):
        """
        Applies a series of processing steps to a medical image.

        Args:
            image: A medical image to process.
            image_path: A file path corresponding to the medical image.
            streamlit_state: Optional StreamlitSessionState to update progress

        Returns:
            A tuple of lists containing the original and processed medical image,
            and a list of applied processing steps.
        """
        processed_data_by_step = []
        applied_steps = []

        total_steps = len([step for step, config in self.config.items() 
                          if isinstance(config, dict) and config.get('enabled', False)])
        current_step = 0

        for step_name, step_class in self.step_classes.items():
            if self.config[step_name]["enabled"]:
                try:
                    current_step += 1
                    if self.streamlit_state is not None:
                        self.streamlit_state.current_step = f"Applying {step_name}..."
                        self.streamlit_state.current_substep = current_step
                        self.streamlit_state.total_substeps = total_steps
                        self.streamlit_state.substep_progress = current_step / total_steps

                    step_instance = step_class(self.config[step_name])
                    print(f"Starting with pre-processing step: {step_name}")

                    # Make a deep copy of the original image data
                    image = step_instance.run(image, image_path)

                    # Store the data for visualization
                    processed_data_by_step.append(image)
                    applied_steps.append(step_name)

                    print(f"Successfully applied {step_name}.")
                except (ValueError, IOError) as error:
                    print(f"Error applying {step_name}, with error {error}.")
                    if self.streamlit_state is not None:
                        self.streamlit_state.current_step = f"Error in {step_name}: {str(error)}"

        return processed_data_by_step, applied_steps
