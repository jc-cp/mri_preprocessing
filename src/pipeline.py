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

import nibabel as nib

from src.preprocessing.bias_field_correction import BiasFieldCorrection
from src.preprocessing.binning import Binning
from src.preprocessing.denoising import Denoising
from src.preprocessing.filtering import Filtering
from src.preprocessing.normalization import Normalization
from src.preprocessing.registration import Registration
from src.preprocessing.resampling import Resampling
from src.preprocessing.skull_stripping import SkullStripping
from src.utils.helper_functions import copy_nifti_image
from src.utils.image_conversion import ImageConversion
from src.utils.image_loading import ImageLoading
from src.utils.image_saving import ImageSaving
from src.utils.image_visualization import ImageVisualization


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

    def __init__(self, config_file):
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
            "bias_field_correction": BiasFieldCorrection,
            "resampling": Resampling,
            "registration": Registration,
            "skull_stripping": SkullStripping,
            "normalization": Normalization,
            "filtering": Filtering,
            "denoising": Denoising,
            "binning": Binning
            # add other preprocessing steps...
        }

        # Initialize utility functions
        self.image_loading = ImageLoading(self.config["image_loading"])
        self.image_conversion = ImageConversion(self.config["image_conversion"])
        self.image_saving = ImageSaving(self.config["image_saving"])
        self.image_visualization = ImageVisualization(self.config["image_visualization"])

    def run(self):
        """
        Runs the preprocessing pipeline on the specified images.

        Raises:
            ExceptionGroup: If any exception occurs during pipeline execution.
        """

        try:
            """Runs the preprocessing pipeline on the specified images."""
            for image, path in self.load_images():
                image = self.convert_image(image)

                initial_image = image

                (
                    original_data_by_step,
                    processed_data_by_step,
                    applied_steps,
                    template_image,
                ) = self.apply_steps([image], [path])
                self.save_images([image], [path])
                self.visualize_images(
                    initial_image,
                    template_image,
                    original_data_by_step,
                    processed_data_by_step,
                    applied_steps,
                )
        except ExceptionGroup as error:
            print(f"Error running pipeline: {error}")

    def load_images(self):
        """
        Loads medical images from DICOM or NIFTI files.

        Returns:
            A tuple of loaded medical images and their file paths.

        Raises:
            ValueError: If `file_path` or `image_paths` is not specified in the configuration.
        """
        image_data, image_paths = self.image_loading.run()
        print(f"Loaded {len(image_data)} images!")
        return image_data, image_paths

    def convert_images(self, image_data):
        """
        Converts medical images between DICOM and NIFTI formats.

        Args:
            image_data (list): A list of medical images in either DICOM or NIFTI format.

        Returns:
            A list of converted medical images in the opposite format.

        Raises:
            ValueError: If `enabled` is not specified in the configuration.
        """
        if self.config["image_conversion"]["enabled"]:
            image_data = [self.image_conversion.run(image) for image in image_data]
            print(f"Converted {len(image_data)} images.")
        return image_data

    def apply_steps(self, image_data, image_paths):
        """
        Applies a series of processing steps to medical images.

        Args:
            image_data (list): A list of medical images to process.
            image_paths (list): A list of file paths corresponding to the medical images.

        Returns:
            A tuple of lists containing the original and processed medical images,
            and a list of applied processing steps.

        Raises:
            ValueError: If `enabled` is not specified in the configuration.
            ValueError: If `image_data` or `image_paths` is empty.
            ValueError: If an error occurs during processing.
        """
        original_data_by_step = []
        processed_data_by_step = []
        applied_steps = []

        for step_name, step_class in self.step_classes.items():
            if self.config[step_name]["enabled"]:
                try:
                    step_instance = step_class(self.config[step_name])
                    print(f"Starting with pre-processing step: {step_name}")
                    # Make a deep copy of the original image data
                    original_image_data = [copy_nifti_image(img) for img in image_data]
                    image_data = [
                        step_instance.run(image, path)
                        for image, path in zip(image_data, image_paths)
                    ]
                    # Store the data for visualization
                    original_data_by_step.append(original_image_data)
                    processed_data_by_step.append(image_data)
                    applied_steps.append(step_name)
                    print(f"Successfully applied {step_name}.")
                except (ValueError, IOError) as error:
                    print(f"Error applying {step_name}, with error {error}.")
        return original_data_by_step, processed_data_by_step, applied_steps

    def save_images(self, image_data, image_paths):
        """
        Saves medical images to DICOM or NIFTI files.

        Args:
            image_data (list): A list of medical images to save.
            image_paths (list): A list of file paths corresponding to the medical images.

        Raises:
            ValueError: If `enabled` is not specified in the configuration.
        """
        self.image_saving.run(image_data, image_paths)

    def visualize_images(
        self,
        initial_image,
        template_image,
        original_data_by_step,
        processed_data_by_step,
        applied_steps,
    ):
        """
        Visualizes medical images before and after processing.

        Args:
            original_data_by_step (list): A list of lists of medical images before processing.
            processed_data_by_step (list): A list of lists of medical images after processing.
            applied_steps (list): A list of strings representing the processing steps applied.

        Raises:
            ValueError: If `enabled` is not specified in the configuration.
            ValueError: If `original_data_by_step` or `processed_data_by_step` is empty.
        """
        if self.config["image_visualization"]["enabled"]:
            self.image_visualization.run(
                initial_image,
                template_image,
                original_data_by_step,
                processed_data_by_step,
                applied_steps,
            )
