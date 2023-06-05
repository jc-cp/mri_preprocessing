from nipype.interfaces.fsl import FLIRT
from nipype.interfaces.ants import ResampleImageBySpacing
import os

# TODO:
# - check the output of libs

class Resampling:
    def __init__(self, config: dict):
        self.config = config

    def run(self, image: str):
        # Check which method is enabled in the configuration
        if self.config['methods']['fsl']['enabled']:
            return self.resample_with_flirt(image)
        elif self.config['methods']['ants']['enabled']:
            return self.resample_with_ants(image)
        else:
            raise ValueError("No valid resampling method enabled in configuration.")

    def resample_with_flirt(self, image: str):
        # Ensure the image file exists
        if not os.path.exists(image):
            raise FileNotFoundError(f"No file found at {image}")

        # Define the FLIRT instance for resampling
        flirt = FLIRT(in_file=image,
                      reference=self.config['methods']['fsl']['reference'],
                      apply_isoxfm=self.config['methods']['fsl']['resolution'],
                      interp=self.config['methods']['fsl']['interp']
                      )
        try:
            result = flirt.run()
        except Exception as e:
            raise RuntimeError(f"FSL FLIRT failed with error: {e}")

        return result.outputs.output_file

    def resample_with_ants(self, image: str):
        # Ensure the image file exists
        if not os.path.exists(image):
            raise FileNotFoundError(f"No file found at {image}")

        # Define the ANTs resampling instance
        resample = ResampleImageBySpacing(dimension=3,
                                          output_spacing=self.config['methods']['ants']['spacing'],
                                          interpolator=self.config['methods']['ants']['interp'],
                                          input_image=image)
        try:
            result = resample.run()
        except Exception as e:
            raise RuntimeError(f"ANTs ResampleImageBySpacing failed with error: {e}")

        return result.outputs.output_image
