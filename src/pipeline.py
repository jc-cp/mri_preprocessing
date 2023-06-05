import json
import logging

# Steps
from preprocessing.denoising import Denoising
from preprocessing.skull_stripping import SkullStripping
from preprocessing.registration import Registration

# Utils
from utils.image_conversion import ImageConversion
from utils.image_loading import ImageLoading
from utils.image_saving import ImageSaving


class Pipeline:
    def __init__(self, config_file):
        # Read configuration
        try:
            with open(config_file, 'r') as f:
                self.config = json.load(f)
            logging.info("Successfully loaded configuration file.")
        except Exception as e:
            logging.error(f"Error loading configuration file: {str(e)}")
            raise e

        # TODO: check the order of the pre-processing
        # Map step names to classes, attention: the order here becomes relevant!
        self.step_classes = {
            'registration': Registration,
            'denoising': Denoising,
            'skull_stripping': SkullStripping,
            # add other preprocessing steps...
        }

        # Initialize utility functions
        self.image_loading = ImageLoading(self.config['image_loading'])
        self.image_conversion = ImageConversion(self.config['image_conversion'])
        self.image_saving = ImageSaving(self.config['image_saving'])
        # initialize other utility functions...

    def run(self):
        # Set up logging
        logging.basicConfig(filename='preprocessing.log', level=logging.INFO,
                            format='%(asctime)s - %(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

        # Load image
        image = self.image_loading.run()

        # Convert image if necessary
        if self.config['image_conversion']['enabled']:
            image = self.image_conversion.run(image)

        # Apply steps
        for step_name, StepClass in self.step_classes.items():
            if self.config[step_name]['enabled']:
                try:
                    step_instance = StepClass(self.config[step_name])
                    image = step_instance.run(image)
                    logging.info(f"Successfully applied {step_name}.")
                except Exception as e:
                    logging.error(f"Error applying {step_name}: {str(e)}")
                    raise e
        self.image_saving.run(image)
