"""
A module for performing bias field correction on medical images.

This module defines a `BiasFieldCorrection` class that can be used to perform bfc on medical images.
The class provides two methods: `itk_bias_field_correction` and `lapgm_bias_field_correction`.
The class can be configured using a dictionary of configuration parameters.
"""
import os

# import lapgm
import SimpleITK as sitk


class BiasFieldCorrection:
    """
    A class for performing bias field correction on medical images.

    Args:
        config (dict): A dictionary containing configuration parameters.

    Methods:
        run(image: str) -> sitk.Image: Runs the bfc on the specified image.
        itk_bias_field_correction(image: str) -> sitk.Image: Runs the ITK bfc.
        lapgm_bias_field_correction(image: str) -> sitk.Image: Runs the LAPGM bfc.
    """

    def __init__(self, config: dict):
        """
        Initializes a new instance of the BiasFieldCorrection class.

        Args:
            config (dict): A dictionary containing configuration parameters for the bfc.
        """
        self.config = config

    def run(self, image: str) -> sitk.Image:
        """
        Runs the bias field correction on the specified image.

        Args:
            image (str): The path to the image file.

        Returns:
            sitk.Image: The corrected image.
        """
        if self.config["methods"]["itk"]["enabled"]:
            return self.itk_bias_field_correction(image)
        elif self.config["methods"]["lapgm"]["enabled"]:
            return self.lapgm_bias_field_correction(image)
        else:
            raise ValueError("No valid bias field correction method enabled in configuration.")

    def itk_bias_field_correction(self, image: str) -> sitk.Image:
        """
        Runs the bias field correction using the ITK method.

        Args:
            image (str): The path to the image file.

        Returns:
            sitk.Image: The corrected image.
        """
        # Ensure the image file exists
        if not os.path.exists(image):
            raise FileNotFoundError(f"No file found at {image}")

        shrinking_factor = self.config["methods"]["itk"]["parameters"]["shrink_factor"]

        # Load the image
        img = sitk.ReadImage(image)

        # Create the corrector object
        corrector = sitk.N4BiasFieldCorrectionImageFilter()

        # Set parameters
        corrector.SetMaximumNumberOfIterations(
            self.config["methods"]["itk"]["parameters"]["number_of_iterations"]
        )
        # corrector.SetShrinkFactor(shrinking_factor)

        # Run the correction
        # corrected_img = corrector.Execute(img)

        # return corrected_img

    def lapgm_bias_field_correction(self, image: str) -> sitk.Image:
        """
        Runs the bias field correction using the LAPGM method.

        Args:
            image (str): The path to the image file.

        Returns:
            sitk.Image: The corrected image.
        """
        # Ensure the image file exists
        if not os.path.exists(image):
            raise FileNotFoundError(f"No file found at {image}")

        # Load the image
        img = sitk.ReadImage(image)

        # Run the correction
        # corrected_img = lapgm.bias_field_correction(img)

        # return corrected_img
