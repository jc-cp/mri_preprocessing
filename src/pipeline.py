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
from pathlib import Path
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
            # "skull_stripping": SkullStripping,
            "denoising": Denoising,
            "normalization": Normalization,
            # "filtering": Filtering,
            # "binning": Binning
            # add other preprocessing steps...
        }

        # Initialize utility functions
        self.image_loading = ImageLoading(self.config["image_loading"])
        self.image_conversion = ImageConversion(self.config["image_conversion"])
        self.image_saving = ImageSaving(self.config["image_saving"])
        self.image_visualization = ImageVisualization(
            self.config["image_visualization"]
        )

        self.streamlit_state = streamlit_state

        print("Initialized pipeline with following steps: "),
    

    def run(self):
        """
        Runs the preprocessing pipeline on the specified images one-by-one.
        """
        # Initialize the processed_images list if it doesn't exist
        if self.streamlit_state is not None and "processed_images" not in self.streamlit_state:
            self.streamlit_state.processed_images = []

        # Get total number of images
        image_list = list(self.image_loading.run())
        total_images = len(image_list)
        current_image = 0

        print(f"\nStarting pipeline processing for {total_images} images")
        print("=" * 50)

        if self.streamlit_state is not None:
            self.streamlit_state.total_images = total_images
            self.streamlit_state.current_image = current_image
            self.streamlit_state.current_step = "Starting pipeline..."
            self.streamlit_state.progress = 0.0

        for image, path in image_list:
            current_image += 1
            image_name = Path(path).name
            print(f"\nProcessing image {current_image}/{total_images}: {image_name}")
            print("-" * 40)

            if self.streamlit_state is not None:
                self.streamlit_state.current_image = current_image
                self.streamlit_state.current_step = f"Processing image {current_image}/{total_images}: {image_name}"
                self.streamlit_state.progress = current_image / total_images

                # Create a new list for this image's processing steps
                current_image_steps = []
                self.streamlit_state.processed_images.append({
                    "image_path": path,
                    "image_name": image_name,
                    "processing_steps": current_image_steps
                })

            # Do conversion to Nifti if needed
            if self.config["image_conversion"]["enabled"]:
                print("Converting image to NIfTI format...")
                if self.streamlit_state is not None:
                    self.streamlit_state.current_step = "Converting to NIfTI..."
                image = self.image_conversion.run(path)

            # Save initial image and template for later visualization
            initial_image = image
            print(f"Initial image loaded with shape: {initial_image.shape}")

            # Apply preprocessing steps
            processed_data_by_step, applied_steps = self.apply_steps(
                image,
                path,
                current_image_steps if self.streamlit_state is not None else None
            )

            self.image_saving.run(image, path)
            if self.config["image_visualization"]["enabled"]:
                print("Generating visualizations...")
                if self.streamlit_state is not None:
                    self.streamlit_state.current_step = "Generating visualizations..."

                template_image = self.config["registration"]["reference"]
                self.image_visualization.run(
                    initial_image,
                    template_image,
                    processed_data_by_step,
                    applied_steps,
                )

            print(f"Completed processing for image: {image_name}")

        print("\nPipeline execution completed!")
        print("=" * 50)

        if self.streamlit_state is not None:
            self.streamlit_state.current_step = "Pipeline completed!"
            self.streamlit_state.progress = 1.0


    def apply_steps(self, image, image_path, current_image_steps=None):
        """
        Applies a series of processing steps to a medical image.
        """
        processed_data_by_step = []
        applied_steps = []

        # Count only steps that are enabled AND have display_step=True
        total_steps = len([
            step for step, config in self.config.items()
            if isinstance(config, dict) 
            and config.get("enabled", False)
            and config.get("display_step", True)
        ])
        current_step = 0

        for step_name, step_class in self.step_classes.items():
            if self.config[step_name]["enabled"]:
                try:
                    step_message = f"Applying {step_name}..."
                    print(f"\n{step_message}")

                    # Only increment step counter for displayed steps
                    if self.config[step_name].get("display_step", True):
                        current_step += 1

                    if self.streamlit_state is not None:
                        self.streamlit_state.current_step = step_message
                        self.streamlit_state.current_substep = current_step
                        self.streamlit_state.total_substeps = total_steps
                        self.streamlit_state.substep_progress = current_step / total_steps if total_steps > 0 else 0
                        self.streamlit_state.terminal_output.append(step_message)

                    step_instance = step_class(self.config[step_name])
                    
                    # Process the image
                    image = step_instance.run(image, image_path)

                    # Store the data for visualization only if display_step is True
                    if current_image_steps is not None and self.config[step_name].get("display_step", True):
                        success_message = f"Successfully applied {step_name}"
                        self.streamlit_state.terminal_output.append(success_message)

                        current_image_steps.append({
                            "current_step": step_name,
                            "current_substep": current_step,
                            "image": self._prepare_img_for_viz(image),
                            "path": image_path,
                        })

                    processed_data_by_step.append(image)
                    applied_steps.append(step_name)

                    print(f"Successfully completed {step_name}")
                except (ValueError, IOError) as error:
                    error_message = f"Error applying {step_name}: {str(error)}"
                    print(f"ERROR: {error_message}")
                    if self.streamlit_state is not None:
                        self.streamlit_state.current_step = error_message
                        self.streamlit_state.terminal_output.append(error_message)

        return processed_data_by_step, applied_steps

    def _normalize_image(self, image):
        """
        Normalizes an image to be displayed in Streamlit.
        """
        image_min = image.min()
        image_max = image.max()
        if image_max > image_min:
            return (image - image_min) / (image_max - image_min)
        return image

    def _prepare_img_for_viz(self, image):
        """
        Prepares an image for visualization.
        """
        image = self.image_visualization._get_slice(image)
        image = self._normalize_image(image)

        return image
