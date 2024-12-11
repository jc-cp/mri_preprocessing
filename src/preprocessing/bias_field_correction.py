"""
A module for performing bias field correction on medical images.

This module defines a `BiasFieldCorrection` class that can be used to perform bfc on medical images.
The class provides two methods: `itk_bias_field_correction` and `lapgm_bias_field_correction`.
The class can be configured using a dictionary of configuration parameters.
"""
import os

import nibabel as nib
import numpy as np

import lapgm
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

        correction_applied = False
        for method_name in self.config["methods"]:
            if self.config["methods"][method_name]["enabled"]:
                func = self.methods.get(method_name, None)
                if func:
                    bf_corrected_image = func(image)
                    correction_applied = True
                if saving_images:
                    new_dir, img_id = prepare_output_directory(output_dir, image_path)
                    filename = os.path.join(new_dir, f"{img_id}_{method_name}_bf_corrected.nii.gz")
                    nib.save(bf_corrected_image, filename)
                return bf_corrected_image
        if not correction_applied:
            raise ValueError("No bias field correction method enabled in configuration.")

    def sitk_bias_field_correction(self, image) -> nib.Nifti1Image:
        """
        Runs the bias field correction using the ITK method.

        Args:
            image: The image file.

        Returns:
            nib.Nifti1Image: The corrected image.
        """

        simple = self.config["methods"]["sitk"]["automatic"]
        sitk_image = nib_to_sitk(image)

        if simple:
            print("Applying automatic bias field correction.")
            corrected_img = sitk.N4BiasFieldCorrection(sitk_image)
        else:
            print("Applying complex bias field correction.")
            # Default parameters based on literature
            default_params = {
                "n_fitting_levels": 4,
                "n_iterations": [50, 50, 50, 50],  # iterations per level
                "convergence_threshold": 0.001,
                "bf_fwhm": 0.15,  # Bias field FWHM in mm
                "wiener_noise": 0.01,
                "histogram_bins": 200,
            }
            params = {**default_params, **self.config.get("sitk_params", {})}

            # Setup N4 corrector
            corrector = sitk.N4BiasFieldCorrectionImageFilter()
            corrector.SetMaximumNumberOfIterations(params["n_iterations"])
            corrector.SetConvergenceThreshold(params["convergence_threshold"])
            corrector.SetBiasFieldFullWidthAtHalfMaximum(params["bf_fwhm"])
            corrector.SetWienerFilterNoise(params["wiener_noise"])
            corrector.SetNumberOfHistogramBins(params["histogram_bins"])
    
            # Execute correction
            corrected_img = corrector.Execute(sitk_image)

        return sitk_to_nib(corrected_img)

    def lapgm_bias_field_correction(self, image) -> nib.Nifti1Image:
        """
        Local Adaptive Patch-based Gaussian Mixture (LAPGM) bias field correction.
        Based on: https://github.com/lucianoAvinas/lapgm
        """
        try:
            
            # Set GPU if configured
            config = self.config.get("bias_field_correction", {}).get("methods", {}).get("lapgm", {})

            use_gpu = config.get("use_gpu", False)
            if use_gpu:
                print("Setting LAPGM to use GPU")
                lapgm.use_gpu(True)
            
            # Convert image to sequence array format
            image_data = image.get_fdata()
            
            # Simple normalization to [0,1] range
            image_data = image_data - image_data.min()
            image_data = image_data / (image_data.max() + np.finfo(float).eps)
            
            # Scale to reasonable intensity range [0.1, 1.0] to avoid numerical issues
            image_data = 0.9 * image_data + 0.1
            
            sequence_array = lapgm.to_sequence_array([image_data])
            
            # Initialize LapGM
            debias_obj = lapgm.LapGM()
            
            # Set required hyperparameters from config or defaults
            debias_obj.set_hyperparameters(
                tau=config.get("tau", 1.0),  # inverse penalty strength
                n_classes=config.get("n_classes", 3)  # number of classes
            )
            
            # Specify cylindrical decay
            debias_obj.specify_cylindrical_decay(
                alpha=config.get("alpha", 2.0)  # penalty relaxation
            )
            
            # Estimate parameters and debias
            params = debias_obj.estimate_parameters(sequence_array)
            debiased_array = lapgm.debias(sequence_array, params)
            
            # Normalize if specified
            if config.get("normalize", True):
                target_intensity = config.get("target_intensity", 1000.0)
                debiased_array = lapgm.normalize(debiased_array, params, target_intensity)
            
            # Convert back to Nifti (take first channel)
            debiased_image = debiased_array[0]
            
            # Rescale back to original intensity range
            orig_range = image.get_fdata().max() - image.get_fdata().min()
            debiased_image = (debiased_image - 0.1) / 0.9  # Undo [0.1, 1.0] scaling
            debiased_image = debiased_image * orig_range + image.get_fdata().min()
            # Reset GPU setting if it was enabled
            if use_gpu:
                lapgm.use_gpu(False)
            return nib.Nifti1Image(debiased_image, image.affine)
            
        except Exception as e:
            print(f"Error during bias field correction: {e}")
            raise e
        