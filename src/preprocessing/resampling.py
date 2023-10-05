"""
This script demonstrates how to resample a 3D medical image using different methods.

The Resampling class provides two methods for resampling images: ANTs and SciPy. The class takes 
a configuration dictionary as input, which specifies the resampling methods to enable and the 
target voxel spacing for each method.
"""
import os

import nibabel as nib
import numpy as np
import SimpleITK as sitk
from nipype.interfaces.ants import ResampleImageBySpacing
from scipy.ndimage import zoom

from src.utils.helper_functions import (
    nib_to_sitk,
    prepare_output_directory,
    sitk_to_nib,
)


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
                spacing = self.config["methods"][method_name]["spacing"]
                func = self.methods.get(method_name, None)
                if func:
                    resampled_image = func(image, spacing)
                if saving_images:
                    new_dir, img_id = prepare_output_directory(output_dir, image_path)
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

    def resample_with_scipy(self, image, spacing):
        """
        Resamples the given image using SciPy.

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
        current_spacing = nib.load(image).header.get_zooms()[:3]
        scale_factors = [current_spacing[i] / spacing[i] for i in range(3)]
        resampled_image = zoom(image, scale_factors, order=1)
        return resampled_image

    def resample_with_sitk(self, _, spacing) -> nib.Nifti1Image:
        """
        Resamples and aligns the given moving image to have the same orientation,
        spacing, and origin as the fixed image.

        Parameters
        ----------
        moving_img : SimpleITK.Image
            The moving image to resample.
        fixed_img : SimpleITK.Image
            The fixed image to align with.

        Returns
        -------
        SimpleITK.Image
            The resampled and aligned image.
        """
        template = self.config["methods"]["sitk"]["reference"]
        interp_type = self.config["methods"]["sitk"]["interpolation"]

        fixed_img = nib.load(template)
        fixed_img = nib.as_closest_canonical(fixed_img)
        fixed_img = nib_to_sitk(fixed_img)

        try:
            if interp_type == "linear":
                interp_type = sitk.sitkLinear
            elif interp_type == "bspline":
                interp_type = sitk.sitkBSpline
            elif interp_type == "nearest_neighbor":
                interp_type = sitk.sitkNearestNeighbor

            old_size = fixed_img.GetSize()
            old_spacing = fixed_img.GetSpacing()
            new_spacing = tuple(spacing)
            new_size = [
                int(round((old_size[0] * old_spacing[0]) / float(new_spacing[0]))),
                int(round((old_size[1] * old_spacing[1]) / float(new_spacing[1]))),
                int(round((old_size[2] * old_spacing[2]) / float(new_spacing[2]))),
            ]

            resampler = sitk.ResampleImageFilter()
            resampler.SetOutputDirection(fixed_img.GetDirection())
            resampler.SetOutputSpacing(new_spacing)
            resampler.SetSize(new_size)
            resampler.SetOutputOrigin(fixed_img.GetOrigin())
            resampler.SetDefaultPixelValue(fixed_img.GetPixelIDValue())
            resampler.SetOutputPixelType(sitk.sitkFloat32)
            resampler.SetInterpolator(interp_type)

            resampled_img = resampler.Execute(fixed_img)

            resampled_img = sitk_to_nib(resampled_img)

        except ExceptionGroup:
            print("Exception thrown while setting up the resampling filter.")

        return resampled_img
