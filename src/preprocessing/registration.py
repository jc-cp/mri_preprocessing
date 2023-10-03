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
from itk import itkMINCImageIOPython
from nipype.interfaces import spm
from nipype.interfaces.fsl import FLIRT


class Registration:
    """
    A class for performing image registration using various methods.

    This class provides a `run` method that takes an image and a path to a template image
    and returns the registered image.
    The class can be configured using a dictionary of configuration parameters.

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
        self.methods = {"itk": self.itk_registration, "spm": self.spm_registration}

    def run(self, image, path: str):
        """
        Registers an image to a template image using the configured registration methods.

        Args:
            image: The image to register.
            template_path (str): The path to the template image.

        Returns:
            The registered image.
        """
        for method_name, method in self.methods.items():
            if self.config["methods"][method_name]["enabled"]:
                image = method(image, path)
        return image

    def itk_registration(self, image, path):
        """
        Registers an image to a template image using the ITK registration method.

        Args:
            image: The image to register.
            template_path (str): The path to the template image.

        Returns:
            The registered image.
        """
        template = self.config["methods"]["itk"]["template"]
        output_path = self.config["methods"]["itk"]["output_path"]

        # Ensure the image file exists
        if not os.path.exists(template):
            raise FileNotFoundError(f"No file found at {template}")

        fixed_image = itk.imread(template, itk.F)

        # Import Parameter Map
        parameter_object = itk.ParameterObject.New()
        parameter_object.AddParameterFile("data/registration_templates/Parameters_Rigid.txt")

        if "nii" in path:
            # Call registration function
            try:
                moving_image = itk.imread(path, itk.F)
                image_id = path.split("/")[-1]

                new_dir = output_path + "/" + image_id.split(".")[0]
                if not os.path.exists(new_dir):
                    os.mkdir(new_dir)

                result_image, _ = itk.elastix_registration_method(
                    fixed_image,
                    moving_image,
                    parameter_object=parameter_object,
                    output_directory=new_dir,
                    log_to_console=False,
                )

                itk.imwrite(
                    result_image, new_dir + "/" + image_id.split(".")[0] + "_registered" + ".nii.gz"
                )

                print("Registered ", image_id)

                # Convert ITK image to numpy array, create NIfTI image from array
                np_array = itk.GetArrayFromImage(result_image)
                nifti_image = nib.Nifti1Image(np_array, np.eye(4))
                return nifti_image

            except:
                print("Cannot transform", path.split("/")[-1])

        else:
            raise FileNotFoundError("File has not .nii suffix on it!")

    def spm_registration(self, image, path):
        """
        Registers an image to a template image using the SPM registration method.

        Args:
            image: The image to register.
            template_path (str): The path to the template image.

        Returns:
            The registered image.
        """
        # Ensure the image file exists
        if not os.path.exists(path):
            raise FileNotFoundError(f"No file found at {path}")

        template = self.config["methods"]["spm"]["template"]

        nii_path = self.convert_nii_gz_to_nii(path)
        deformation_file_path = self.spm_segmentation(image, path)

        # Define the SPM Normalize12 instance for registration
        norm12 = spm.Normalize12(
            jobtype="estwrite",
            tpm=template,
            apply_to_files=[nii_path],
            deformation_file=deformation_file_path,
        )

        try:
            result = norm12.run()
            print("type registration result:", type(result))

        except Exception as error:
            print(f"SPM Normalize12 failed with error: {error}")

        return result.outputs

    def convert_nii_gz_to_nii(self, nii_gz_path):
        # Load the .nii.gz file
        img = nib.load(nii_gz_path)

        # Derive the .nii file path from the .nii.gz file path
        nii_path = nii_gz_path[:-3]  # Remove the '.gz' from the end

        # Save the image data to a .nii file
        nib.save(img, nii_path)

        return nii_path

    def spm_segmentation(self, image, path):
        # Define the segmentation instance
        segmentation = spm.NewSegment()

        # Set input file
        segmentation.inputs.channel_files = path

        # Run segmentation
        try:
            seg_result = segmentation.run()
        except Exception as e:
            raise RuntimeError(f"SPM NewSegment failed with error: {e}")

        # Cleanup segmentation results
        self.cleanup_segmentation_results(path)

        # Return the forward deformation file path
        return seg_result.outputs

    def cleanup_segmentation_results(self, path):
        dir_path = os.path.dirname(path)
        pattern = "c*.nii"  # SPM segmentation results start with 'c'
        files = glob.glob(os.path.join(dir_path, pattern))
        for f in files:
            try:
                os.remove(f)
            except OSError:
                print(f"Error: {f} : {os.strerror}")

    def fsl_registration(self, image, path: str):
        # Ensure the image file exists
        if not os.path.exists(path):
            raise FileNotFoundError(f"No file found at {path}")

        # Define the FLIRT instance for resampling
        flirt = FLIRT(
            in_file=image,
            reference=self.config["methods"]["fsl"]["reference"],
            apply_isoxfm=self.config["methods"]["fsl"]["resolution"],
            interp=self.config["methods"]["fsl"]["interp"],
        )
        try:
            result = flirt.run()
        except Exception as e:
            raise RuntimeError(f"FSL FLIRT failed with error: {e}")

        return result.outputs

    def sitk_registration(self, img_path: str, output_path: str):
        template = self.config["methods"]["itk"]["template"]
        output_path = self.config["methods"]["itk"]["output_path"]

        print("Sikt registration ongoing...")
        # Ensure the image file exists
        if not os.path.exists(template):
            raise FileNotFoundError(f"No file found at {template}")

        fixed_img = itk.imread(template, itk.F)

        if "nii" in img_path:
            # Call registration function
            image_id = img_path.split("/")[-1]

            try:
                moving_img = itk.imread(img_path, itk.F)

                new_dir = output_path + "/" + image_id.split(".")[0]
                if not os.path.exists(new_dir):
                    os.makedirs(new_dir, exist_ok=True)

                transform = sitk.CenteredTransformInitializer(
                    fixed_img,
                    moving_img,
                    sitk.Euler3DTransform(),
                    sitk.CenteredTransformInitializerFilter.GEOMETRY,
                )
                # multi-resolution rigid registration using Mutual Information
                registration_method = sitk.ImageRegistrationMethod()
                registration_method.SetMetricAsMattesMutualInformation(numberOfHistogramBins=50)
                registration_method.SetMetricSamplingStrategy(registration_method.RANDOM)
                registration_method.SetMetricSamplingPercentage(0.01)
                registration_method.SetInterpolator(sitk.sitkLinear)
                registration_method.SetOptimizerAsGradientDescent(
                    learningRate=1.0,
                    numberOfIterations=100,
                    convergenceMinimumValue=1e-6,
                    convergenceWindowSize=10,
                )
                registration_method.SetOptimizerScalesFromPhysicalShift()
                registration_method.SetShrinkFactorsPerLevel(shrinkFactors=[4, 2, 1])
                registration_method.SetSmoothingSigmasPerLevel(smoothingSigmas=[2, 1, 0])
                registration_method.SmoothingSigmasAreSpecifiedInPhysicalUnitsOn()
                registration_method.SetInitialTransform(transform)
                final_transform = registration_method.Execute(fixed_img, moving_img)

                sitk.WriteImage(
                    final_transform,
                    new_dir + "/" + image_id.split(".")[0] + "_registered" + ".nii.gz",
                )

            except (FileNotFoundError, IOError, RuntimeError) as error:
                print(f"Cannot transform {image_id}, with error {error}.")

        else:
            raise FileNotFoundError("File has not .nii suffix on it!")
