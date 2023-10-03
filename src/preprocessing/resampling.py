"""
This script demonstrates how to resample a 3D medical image using different methods.

The Resampling class provides two methods for resampling images: ANTs and SciPy. The class takes 
a configuration dictionary as input, which specifies the resampling methods to enable and the 
target voxel spacing for each method.
"""
import os

import nibabel as nib
import numpy as np
from nipype.interfaces.ants import ResampleImageBySpacing
from nipype.interfaces.fsl import FLIRT
from scipy.ndimage import zoom


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
        self.methods = {"ants": self.resample_with_ants, "scipy": self.resample_with_scipy}

    def run(self, image, path: str):
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
        for method_name, method in self.methods.items():
            if self.config["methods"][method_name]["enabled"]:
                spacing = self.config["methods"][method_name]["spacing"]
                resampled_image = method(image, spacing)
                filename = os.path.join(path, f"{method_name}.nii.gz")
                nib.save(nib.Nifti1Image(resampled_image, np.eye(4)), filename)

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
