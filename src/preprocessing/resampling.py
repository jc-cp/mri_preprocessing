"""
This script demonstrates how to resample a 3D medical image using different methods.

The Resampling class provides two methods for resampling images: ANTs and SciPy. The class takes 
a configuration dictionary as input, which specifies the resampling methods to enable and the 
target voxel spacing for each method.
"""
import os

import itk
import nibabel as nib
import numpy as np
import SimpleITK as sitk
from nipype.interfaces.ants import ResampleImageBySpacing
from scipy.ndimage import zoom

from src.utils import helper_functions as hf


class Resampling:
    """
    A class for resampling images using different methods.

    Parameters
    ----------
    config : dict
        A dictionary containing configuration options for the resampling methods.

    Methods
    -------
    run(image, path)
        Resamples the given image using the enabled resampling methods and
        saves the results to the specified path.
    resample_with_ants(image, spacing)
        Resamples the given image using ANTs.
    resample_with_scipy(image, spacing)
        Resamples the given image using SciPy.
    """

    def __init__(self, config: dict):
        """
        Initializes a new instance of the Resampling class.

        Parameters
        ----------
        config : dict
            A dictionary containing configuration options for the resampling methods.
        """
        self.config = config
        self.methods = {
            "ants": self.resample_with_ants,
            "scipy": self.resample_with_scipy,
            "sitk": self.resample_with_sitk,
            "itk": self.resample_with_itk,
        }

    def run(self, image, image_path: str):
        """
        Resamples the given image using the enabled resampling methods and
        saves the results to the specified path.

        Parameters
        ----------
        image : numpy.ndarray
            The image to resample.
        path : str
            The path to save the resampled images to.
        """
        saving_images = self.config["saving_files"]
        output_dir = self.config["output_dir"]

        for method_name in self.config["methods"]:
            if self.config["methods"][method_name]["enabled"]:
                func = self.methods.get(method_name, None)
                spacing = tuple(self.config["spacing"])
                if func:
                    resampled_image = func(image, spacing)
                if saving_images:
                    new_dir, img_id = hf.prepare_output_directory(output_dir, image_path)
                    filename = os.path.join(new_dir, f"{img_id}_{method_name}_resampled.nii.gz")
                    nib.save(resampled_image, filename)
                return resampled_image

    def resample_with_ants(self, image, spacing):
        """
        Resamples the given image using ANTs.

        Parameters
        ----------
        image : numpy.ndarray
            The image to resample.
        spacing : tuple
            The target voxel spacing.

        Returns
        -------
        numpy.ndarray
            The resampled image.
        """
        resampler = ResampleImageBySpacing()
        resampler.inputs.input_image = nib.Nifti1Image(image, np.eye(4))
        resampler.inputs.output_image = "output.nii.gz"
        resampler.inputs.output_image_dtype = "float32"
        resampler.inputs.spacing = spacing
        resampler.run()
        resampled_image = nib.load("output.nii.gz").get_fdata()
        os.remove("output.nii.gz")
        return resampled_image

    def resample_with_scipy(self, image: nib.Nifti1Image, spacing: tuple) -> np.ndarray:
        """
        Resamples the given image using SciPy's zoom function with configurable parameters.
        
        Parameters
        ----------
        image : nib.Nifti1Image
            The input image to resample
        Returns
        -------
        np.ndarray
            The resampled image
        """
        try:
            # Get configuration parameters
            config = self.config["methods"]["scipy"]
            order = config.get("order", 1)
            mode = config.get("mode", "constant")
            preserve_range = config.get("preserve_range", True)

            # Calculate zoom factors
            img_data = image.get_fdata()
            current_spacing = np.array(image.header.get_zooms()[:3])
            scale_factors = current_spacing / np.array(spacing)
            
            # Apply resampling
            resampled = zoom(
                img_data,
                scale_factors,
                order=order,
                mode=mode,
                prefilter=True,
                grid_mode=False
            )
            
            if preserve_range:
                # Ensure output intensity range matches input
                resampled = np.clip(resampled, img_data.min(), img_data.max())
                
            new_affine = image.affine.copy()
            new_affine[:3, :3] = np.diag(spacing)
            return nib.Nifti1Image(resampled, new_affine)
            
        except Exception as e:
            raise Exception(f"Error in scipy resampling: {str(e)}")

    def resample_with_sitk(self, image: nib.Nifti1Image, spacing: tuple) -> nib.Nifti1Image:
        """
        Resamples image using SimpleITK with configurable interpolation.
        
        Parameters
        ----------
        image : nib.Nifti1Image
            Input image
        spacing : tuple
            Target spacing
            
        Returns
        -------
        nib.Nifti1Image
            Resampled image
        """
        try:
            config = self.config["methods"]["sitk"]
            interp_type = config.get("interpolation", "linear")
            spacing = config.get("spacing", [1.0, 1.0, 1.0])

            # Convert to SimpleITK
            sitk_image = hf.nib_to_sitk(image)
            # Calculate new size
            old_size = sitk_image.GetSize()
            old_spacing = sitk_image.GetSpacing()
            new_spacing = tuple(spacing)
            new_size = [
                int(round((old_size[0] * old_spacing[0]) / float(new_spacing[0]))),
                int(round((old_size[1] * old_spacing[1]) / float(new_spacing[1]))),
                int(round((old_size[2] * old_spacing[2]) / float(new_spacing[2]))),
            ]
            # Set interpolator
            interpolator_map = {
                "linear": sitk.sitkLinear,
                "bspline": sitk.sitkBSpline,
                "nearest_neighbor": sitk.sitkNearestNeighbor
            }
            interpolator = interpolator_map.get(interp_type, sitk.sitkLinear)


            # Configure resampler
            resampler = sitk.ResampleImageFilter()
            resampler.SetOutputSpacing(new_spacing)
            resampler.SetSize(new_size)
            resampler.SetDefaultPixelValue(sitk_image.GetPixelIDValue())
            resampler.SetOutputPixelType(sitk.sitkFloat32)
            resampler.SetInterpolator(interpolator)
            resampler.SetOutputDirection(sitk_image.GetDirection())
            resampler.SetOutputOrigin(sitk_image.GetOrigin())

            # Execute resampling
            resampled_img = resampler.Execute(sitk_image)
            
            # Convert back to Nibabel
            return hf.sitk_to_nib(resampled_img)
            
        except Exception as e:
            print(f"Exception thrown while setting up the resampling filter: {e}")
            raise Exception(f"Error in SimpleITK resampling: {str(e)}")

    def resample_with_itk(self, image: nib.Nifti1Image, spacing: tuple) -> nib.Nifti1Image:
        """
        Resample the moving image to 1x1x1mm spacing using ITK.
        
        Parameters
        ----------
        moving_image : nib.Nifti1Image
            Input image to resample
        _ : ignored
            Spacing parameter is ignored as we use fixed 1x1x1mm spacing
            
        Returns
        -------
        nib.Nifti1Image
            Resampled image
        """
        try:
            # Convert to canonical orientation for consistency
            image = nib.as_closest_canonical(image)
            
            # Convert to ITK
            ImageType = itk.Image[itk.F, 3]
            itk_image = itk.GetImageFromArray(image.get_fdata().astype(np.float32))
            itk_image.SetSpacing(image.header.get_zooms()[:3])
            
            # Get original size and spacing
            original_size = itk_image.GetLargestPossibleRegion().GetSize()
            original_spacing = itk_image.GetSpacing()
            
            # Set target spacing
            target_spacing = spacing
            
            # Calculate new size
            new_size = [
                int(round(original_size[i] * original_spacing[i] / target_spacing[i]))
                for i in range(3)
            ]

            # Create resampling filter
            resample = itk.ResampleImageFilter[ImageType, ImageType].New()
            resample.SetInput(itk_image)
            resample.SetSize(new_size)
            resample.SetOutputSpacing(target_spacing)
            resample.SetOutputOrigin(itk_image.GetOrigin())
            resample.SetOutputDirection(itk_image.GetDirection())
            resample.SetDefaultPixelValue(0)
            
            # Set linear interpolation
            interpolator = itk.LinearInterpolateImageFunction[ImageType, itk.D].New()
            resample.SetInterpolator(interpolator)
            
            # Execute resampling
            resampled_image = resample.Execute()

            # Convert back to numpy and create Nifti
            resampled_array = itk.GetArrayFromImage(resampled_image)
            
            # Create new affine with 1mm spacing
            new_affine = image.affine.copy()
            new_affine[:3, :3] = np.diag(spacing)
            
            return nib.Nifti1Image(resampled_array, new_affine)

        except Exception as e:
            raise Exception(f"Error in ITK resampling: {str(e)}")
