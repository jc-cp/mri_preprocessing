import json
import logging
import os
import sys

from preprocessing.bias_field_correction import BiasFieldCorrection
from preprocessing.binning import Binning

# Steps
from preprocessing.denoising import Denoising
from preprocessing.filtering import Filtering
from preprocessing.normalization import Normalization
from preprocessing.registration import Registration
from preprocessing.resampling import Resampling
from preprocessing.skull_stripping import SkullStripping
from utils.image_conversion import ImageConversion
from utils.image_loading import ImageLoading
from utils.image_saving import ImageSaving
from utils.image_visualization import ImageVisualization


class Pipeline:
    def __init__(self, config_file):
        logging.basicConfig(
            filename="preprocessing.log",
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        # Read configuration
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                self.config = json.load(f)
            logging.info("Successfully loaded configuration file.")
        except Exception as error:
            logging.error(f"Error loading configuration file: {error}")
            raise error

        # TODO: check the order of the pre-processing
        # Map step names to classes, attention: the order here becomes relevant!
        self.step_classes = {
            "registration": Registration,
            "resampling": Resampling,
            "skull_stripping": SkullStripping,
            "bias_field_correction": BiasFieldCorrection,
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
        # Set up logging
        logging.basicConfig(
            filename="preprocessing.log",
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # Load image
        image_data, image_paths = self.image_loading.run()
        print(f"Loaded {len(image_data)} images")  # Debugging print

        # Convert image if necessary
        if self.config["image_conversion"]["enabled"]:
            image_data = [self.image_conversion.run(image) for image in image_data]
            print(f"Converted {len(image_data)} images")  # Debugging print

        # Store initial state in dictionary
        image_data_dict = {}
        image_data_dict = {"initial": (image_data, image_data.copy())}

        # Apply steps
        original_image_data = image_data  # A copy for comparison through visualization
        for step_name, step_class in self.step_classes.items():
            if self.config[step_name]["enabled"]:
                try:
                    step_instance = step_class(self.config[step_name])
                    original_image_data = image_data.copy()
                    image_data = [
                        step_instance.run(image, path)
                        for image, path in zip(image_data, image_paths)
                    ]
                    image_data_dict[step_name] = (original_image_data, image_data)
                    logging.info(f"Successfully applied {step_name}.")
                except Exception as error:
                    logging.error(f"Error applying {step_name}: {str(error)}")
                    raise error

        self.image_saving.run(image_data, image_paths)

        # Visualization if enabled
        if self.config["image_visualization"]["enabled"]:
            self.image_visualization.run(image_data_dict)
