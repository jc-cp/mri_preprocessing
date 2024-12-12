"""
A module for performing image registration using various methods.

This module defines a `Registration` class that can be used to register an image 
to a template image using various registration methods.
The class provides a `run` method that takes an image and a path to a template image 
and returns the registered image.
The class can be configured using a dictionary of configuration parameters.
"""
import glob
import os

import itk
import nibabel as nib
import numpy as np
import SimpleITK as sitk
from nipype.interfaces import spm
from nipype.interfaces.fsl import FLIRT

from src.utils import helper_functions as hf
from src.utils.helper_functions import (
    convert_nii_gz_to_nii,
    nib_to_sitk,
    prepare_output_directory,
    sitk_to_nib,
)


class Registration:
    """
    The main class for performing image registration.
    """

    def __init__(self, config: dict):
        """
        Initializes a `Registration` instance.

        Args:
            config (dict): A dictionary of configuration parameters.
                The following parameters are supported:
                - methods (dict): A dictionary of registration methods and their parameters.
        """
        self.config = config
        self.methods = {
            "itk": self.itk_registration,
            "spm": self.spm_registration,
            "sitk": self.sitk_registration,
            "fsl": self.fsl_registration,
        }

    def run(self, image, image_path: str):
        """
        Registers an image to a template image using the configured methods.

        Args:
            image: The image to register.
            image_path (str): The path to the image.

        Returns:
            The registered image.
        """
        saving_images = self.config["saving_files"]
        output_dir = self.config["output_dir"]
        template = self.config["reference"]

        for method_name in self.config["methods"]:
            if self.config["methods"][method_name]["enabled"]:
                func = self.methods.get(method_name, None)
                if func:
                    image = func(image, template)
                if saving_images:
                    new_dir, img_id = prepare_output_directory(output_dir, image_path)
                    filename = os.path.join(new_dir, f"{img_id}_{method_name}_registered.nii.gz")
                    nib.save(image, filename)
        return image

    def itk_registration(self, image: nib.Nifti1Image, image_path: str):
        """
        Registers an image to a template image using the ITK registration method.

        Args:
            image: The image to register.
            image_path: The path to the image.

        Returns:
            The registered image.
        """
        template = self.config["reference"]
        if not os.path.exists(template):
            raise FileNotFoundError(f"No file found at {template}")

        try:
            fixed_img = nib.load(template)
            fixed_img = nib.as_closest_canonical(fixed_img)
            fixed_image = hf.nib_to_itk(fixed_img)

            moving_image = nib.as_closest_canonical(image)
            moving_image = hf.nib_to_itk(moving_image)

            # Define the transformation type: Rigid 3D
            transform = itk.CenteredRigid2DTransform[itk.D].New()

            # Create and set up the optimizer
            optimizer = itk.RegularStepGradientDescentOptimizerv4[itk.D].New()
            optimizer.SetLearningRate(4)
            optimizer.SetMinimumStepLength(0.001)
            optimizer.SetNumberOfIterations(200)

            # Define the metric: Mattes Mutual Information
            metric = itk.MattesMutualInformationImageToImageMetricv4[
                itk.Image[itk.F, 3], itk.Image[itk.F, 3]
            ].New()

            # Define the registration framework and set its components
            registration = itk.ImageRegistrationMethodv4.New(
                FixedImage=fixed_image,
                MovingImage=moving_image,
                Metric=metric,
                Optimizer=optimizer,
                InitialTransform=transform,
            )

            # Set up the interpolator
            interpolator = itk.LinearInterpolateImageFunction[itk.Image[itk.F, 3], itk.D].New()
            registration.SetInterpolator(interpolator)

            # Start the registration process
            registration.Update()
            image_registered = registration.GetOutput()

            image_registered = hf.itk_to_nib(image_registered)
            return image_registered

        except Exception as e:
            print("Cannot transform", image_path.split("/")[-1])
            raise Exception(f"Error in ITK registration: {str(e)}")

    def spm_registration(self, image: nib.Nifti1Image, template: str) -> nib.Nifti1Image:
        """
        Register image using SPM's Normalize12.
        
        Args:
            image: Input image to register
            template: Path to template image
        
        Returns:
            Registered image as Nifti1Image
        """
        try:
            spm_config = self.config["methods"]["spm"]
            
            # Save input image temporarily if it's in memory
            if isinstance(image, nib.Nifti1Image):
                temp_input = os.path.join(self.config["output_dir"], "temp_input.nii")
                nib.save(image, temp_input)
                input_path = temp_input
            else:
                input_path = image

            # First run segmentation to get deformation field
            segment = spm.NewSegment()
            segment.inputs.channel_files = input_path
            segment.inputs.channel_info = (0.0001, 60, (True, True))
            segment.inputs.sampling_distance = spm_config["sampling_distance"]
            segment.inputs.write_deformation_fields = [True, True]
            
            print("Running SPM segmentation...")
            segment_result = segment.run()
            
            # Then run normalization using the deformation field
            normalize = spm.Normalize12()
            normalize.inputs.image_to_align = input_path
            normalize.inputs.deformation_file = segment_result.outputs.forward_deformation_field
            normalize.inputs.jobtype = spm_config["jobtype"]
            normalize.inputs.write_wrapped = spm_config["write_wrapped"]
            normalize.inputs.write_voxel_sizes = self.config["spacing"]
            normalize.inputs.template = self.config["reference"]
            normalize.inputs.interpolation = spm_config["interpolation"]
            
            print("Running SPM normalization...")
            normalize_result = normalize.run()
            
            # Load and return the normalized image
            registered_image = nib.load(normalize_result.outputs.normalized_files)
            
            # Cleanup temporary files
            if isinstance(image, nib.Nifti1Image):
                os.remove(temp_input)
                
            return registered_image
            
        except Exception as e:
            raise Exception(f"Error in SPM registration: {str(e)}")

    def fsl_registration(self, image: nib.Nifti1Image, template: str) -> nib.Nifti1Image:
        """
        Register image using FSL FLIRT.
        
        Args:
            image: Input image to register
            template: Path to template image
        
        Returns:
            Registered image as Nifti1Image
        """
        try:
            from nipype.interfaces import fsl
            fsl_config = self.config["methods"]["fsl"]
            
            # Save input image temporarily if it's in memory
            if isinstance(image, nib.Nifti1Image):
                temp_input = os.path.join(self.config["output_dir"], "temp_input.nii.gz")
                nib.save(image, temp_input)
                input_path = temp_input
            else:
                input_path = image

            # Configure FLIRT
            flirt = fsl.FLIRT()
            flirt.inputs.in_file = input_path
            flirt.inputs.reference = template
            flirt.inputs.dof = fsl_config["dof"]
            flirt.inputs.cost = fsl_config["cost_function"]
            flirt.inputs.interp = fsl_config["interp"]
            flirt.inputs.searchr_x = fsl_config["search_angles"]
            flirt.inputs.searchr_y = fsl_config["search_angles"]
            flirt.inputs.searchr_z = fsl_config["search_angles"]
            flirt.inputs.bins = fsl_config["bins"]
            flirt.inputs.init = fsl_config["init"]
            
            print("Running FSL registration...")
            flirt_result = flirt.run()
            
            # Load and return the registered image
            registered_image = nib.load(flirt_result.outputs.out_file)
            
            # Cleanup temporary files
            if isinstance(image, nib.Nifti1Image):
                os.remove(temp_input)
                
            return registered_image
            
        except Exception as e:
            raise Exception(f"Error in FSL registration: {str(e)}")

    def sitk_registration(self, image: nib.Nifti1Image, template: str) -> nib.Nifti1Image:
        """Register the moving image to the fixed image using SimpleITK."""
        sitk_config = self.config["methods"]["sitk"]
        template_nib = nib.load(template)
        template_sitk = nib_to_sitk(template_nib)
        try:
            moving_img = nib.as_closest_canonical(image)
            moving_img = nib_to_sitk(moving_img)

            transform = sitk.CenteredTransformInitializer(
                template_sitk,
                moving_img,
                sitk.Euler3DTransform(),
                sitk.CenteredTransformInitializerFilter.GEOMETRY,
            )
            
            registration_method = sitk.ImageRegistrationMethod()
            registration_method.SetMetricAsMattesMutualInformation(
                numberOfHistogramBins=sitk_config["histogram_bins"]
            )
            registration_method.SetMetricSamplingStrategy(registration_method.RANDOM)
            registration_method.SetMetricSamplingPercentage(
                sitk_config["metric_sampling_percentage"]
            )
            registration_method.SetInterpolator(sitk.sitkLinear)
            registration_method.SetOptimizerAsGradientDescent(
                learningRate=sitk_config["learning_rate"],
                numberOfIterations=sitk_config["number_of_iterations"],
                convergenceMinimumValue=sitk_config["convergence_minimum_value"],
                convergenceWindowSize=sitk_config["convergence_window_size"],
            )
            registration_method.SetOptimizerScalesFromPhysicalShift()
            registration_method.SetShrinkFactorsPerLevel(
                shrinkFactors=sitk_config["shrink_factors"]
            )
            registration_method.SetSmoothingSigmasPerLevel(
                smoothingSigmas=sitk_config["smoothing_sigmas"]
            )
            if sitk_config["smoothing_sigmas_in_physical_units"]:
                registration_method.SmoothingSigmasAreSpecifiedInPhysicalUnitsOn()
            registration_method.SetInitialTransform(transform)
            
            print("Sitk registration ongoing...")
            final_transform = registration_method.Execute(template_sitk, moving_img)

            registered_image = sitk.Resample(
                moving_img,
                template_sitk,
                final_transform,
                sitk.sitkLinear,
                0.0,
                moving_img.GetPixelID(),
            )

            registered_image = sitk_to_nib(registered_image)
            print("Sitk registration finished...")
            return registered_image
        except Exception as e:
            raise Exception(f"Error in SimpleITK registration: {str(e)}")