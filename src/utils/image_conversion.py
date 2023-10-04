"""
A module for converting medical images between different formats.

This module defines an `ImageConversion` class that can be used to convert medical images 
between DICOM and NIFTI formats.
The class provides a `run` method that takes a list of images and returns a 
list of converted images.
The class can be configured using a dictionary of configuration parameters.
"""
import os
import tempfile

import dicom2nifti
import nibabel as nib
import pydicom


class ImageConversion:
    """
    A class for converting medical images between DICOM and NIFTI formats.
    """

    def __init__(self, config):
        self.enabled = config["enabled"]

    def run(self, image):
        """
        Converts a medical image between DICOM and NIFTI formats.

        Args:
            image: A medical image in either DICOM or NIFTI format.

        Returns:
            A converted medical image in the opposite format.

        Raises:
            ValueError: If an image is not in DICOM or NIFTI format.
        """
        if not self.enabled:
            return image

        try:
            if isinstance(image, pydicom.dataset.Dataset):
                # We assume that image is a DICOM file if it's an instance of pydicom.dataset.Dataset
                with tempfile.TemporaryDirectory() as temp_dir:
                    dicom2nifti.convert_dicom.dicom_array_to_nifti(
                        image, temp_dir, reorient_nifti=True
                    )
                    converted_image = nib.load(os.path.join(temp_dir, os.listdir(temp_dir)[0]))
                    return converted_image
            elif isinstance(image, nib.Nifti1Image):
                # If image is a NIFTI file, just pass it through
                return image
            else:
                # If image is not a DICOM file nor a NIFTI, raise an error
                raise ValueError(f"Unsupported image format: {type(image)}")
        except RuntimeError as error:
            print(f"Error converting image to NIFTI format: {str(error)}")
