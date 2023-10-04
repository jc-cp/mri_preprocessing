"""
A module for performing bias field correction on medical images.

This module defines a `BiasFieldCorrection` class that can be used to perform bfc on medical images.
The class provides two methods: `itk_bias_field_correction` and `lapgm_bias_field_correction`.
The class can be configured using a dictionary of configuration parameters.
"""
import os

import nibabel as nib

# import lapgm
import SimpleITK as sitk

from src.utils.helper_functions import (
    nib_to_sitk,
    prepare_output_directory,
    sitk_to_nib,
)


class BiasFieldCorrection:
    """
    A class for performing bias field correction on medical images.

    Args:
        config (dict): A dictionary containing configuration parameters.

    Methods:
        run(image) -> nib.Nifti1Image: Runs the bfc on the specified image.
        sitk_bias_field_correction(image) -> sitk.Image: Runs the ITK bfc.
        lapgm_bias_field_correction(image) -> sitk.Image: Runs the LAPGM bfc.
    """

    def __init__(self, config: dict):
        """
        Initializes a new instance of the BiasFieldCorrection class.

        Args:
            config (dict): A dictionary containing configuration parameters for the bfc.
        """
        self.config = config
        self.methods = {
            "lapgm": self.lapgm_bias_field_correction,
            "sitk": self.sitk_bias_field_correction,
        }

    def run(self, image, image_path: str) -> nib.Nifti1Image:
        """
        Runs the bias field correction on the specified image.

        Args:
            image:  The path to the image file.

        Returns:
            sitk.Image: The corrected image.
        """
        saving_images = self.config["saving_files"]
        output_dir = self.config["output_dir"]

        for method_name in self.config["methods"]:
            if self.config["methods"][method_name]["enabled"]:
                func = self.methods.get(method_name, None)
                if func:
                    bf_corrected_image = func(image)
                if saving_images:
                    new_dir, img_id = prepare_output_directory(output_dir, image_path)
                    filename = os.path.join(new_dir, f"{img_id}_{method_name}_bf_corrected.nii.gz")
                    nib.save(bf_corrected_image, filename)
                return bf_corrected_image
            else:
                raise ValueError("No valid bias field correction method enabled in configuration.")

    def sitk_bias_field_correction(self, image) -> nib.Nifti1Image:
        """
        Runs the bias field correction using the ITK method.

        Args:
            image: The image file.

        Returns:
            nib.Nifti1Image: The corrected image.
        """

        simple = self.config["methods"]["sitk"]["simple"]
        sitk_image = nib_to_sitk(image)

        if simple:
            print("Applying simple bias field correction.")
            corrected_img = sitk.N4BiasFieldCorrection(sitk_image)
        else:
            print("Applying complex bias field correction.")
            bf_full_width_at_half_maximum = self.config["methods"]["sitk"]["bf_fw_hmax"]
            max_number_of_iterations = self.config["methods"]["sitk"]["max_number_of_iterations"]
            convergence_threshold = self.config["methods"]["sitk"]["convergence_threshold"]

            corrector = sitk.N4BiasFieldCorrectionImageFilter()

            # Parameters
            corrector.SetMaximumNumberOfIterations(max_number_of_iterations)
            corrector.SetConvergenceThreshold(convergence_threshold)
            corrector.SetBiasFieldFullWidthAtHalfMaximum(bf_full_width_at_half_maximum)
            corrected_img = corrector.Execute(sitk_image)

        return sitk_to_nib(corrected_img)

    def lapgm_bias_field_correction(self, image) -> nib.Nifti1Image:
        """
        Runs the bias field correction using the LAPGM method.

        Args:
            image: The image file.

        Returns:
            nib.Nifti1Image: The corrected image.
        """
        # Load the image
        # img = sitk.ReadImage(image)

        # Run the correction
        # corrected_img = lapgm.bias_field_correction(img)

        # return corrected_img
