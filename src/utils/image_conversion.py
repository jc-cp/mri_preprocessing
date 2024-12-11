"""
A module for converting medical images between different formats.

This module defines an `ImageConversion` class that can be used to convert medical images 
between DICOM, NRRD, and NIFTI formats.
The class provides a `run` method that takes an image and returns a converted NIFTI image.
The class can be configured using a dictionary of configuration parameters.
"""
import os
import tempfile

import dicom2nifti
import nibabel as nib
import nrrd
import numpy as np
import pydicom
import SimpleITK as sitk


class ImageConversion:
    """
    A class for converting medical images to NIFTI format.
    Supports DICOM and NRRD input formats.
    """

    def __init__(self, config):
        self.enabled = config["enabled"]

    def run(self, image_path):
        """
        Converts a medical image to NIFTI format.

        Args:
            image_path: Path to the medical image file.

        Returns:
            nib.Nifti1Image: The converted medical image in NIFTI format.

        Raises:
            ValueError: If the image format is not supported.
        """
        if not self.enabled:
            return image_path

        try:
            # Check file extension
            ext = image_path.split('.')[-1] if '.' in image_path else ''
            if ext.lower() == 'nrrd':
                nifti_image =  self._convert_nrrd_to_nifti(image_path)
            elif ext.lower() in ['dcm', ''] or os.path.splitext(image_path)[0].endswith('.dcm'):
                nifti_image = self._convert_dicom_to_nifti(image_path)
            elif ext.lower() in ['nii', 'gz']:
                nifti_image = nib.load(image_path)
            else:
                raise ValueError(f"Unsupported image format: {ext}")
            # Ensure the image is in the closest canonical orientation
            nifti_image = nib.as_closest_canonical(nifti_image)
            return nifti_image
        except Exception as error:
            print(f"Error converting image to NIFTI format: {str(error)}")
            raise

    def _convert_nrrd_to_nifti(self, image_path):
        """Convert NRRD to NIFTI format."""
        # Read NRRD file
        data, header = nrrd.read(image_path)
        
        # Reorient to match NIFTI convention (RAS+)
        space_directions = header.get('space directions')
        if space_directions is not None:
            # Convert to numpy array for easier manipulation
            space_directions = np.array(space_directions)
            
            # Determine the primary direction of each axis
            primary_directions = np.argmax(np.abs(space_directions), axis=1)
            
            # Get the signs of the primary directions
            signs = np.sign([space_directions[i, primary_directions[i]] for i in range(3)])
            
            # First transpose to match NIFTI dimension order
            data = np.transpose(data, (2, 1, 0))
            
            # Flip axes where needed to match RAS+ orientation
            for i in range(3):
                if signs[i] < 0:
                    data = np.flip(data, axis=i)
        else:
            # If no space directions, just transpose to match NIFTI convention
            data = np.transpose(data, (2, 1, 0))
        
        # Create affine matrix
        spacing = header.get('spacing', (1.0, 1.0, 1.0))
        affine = np.diag(list(spacing) + [1.0])
        
        # Create NIFTI image
        nifti_image = nib.Nifti1Image(data, affine)
        return nifti_image

    def _convert_dicom_to_nifti(self, image_path):
        """Convert DICOM to NIFTI format."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # If image_path is a directory, assume it contains DICOM series
            if os.path.isdir(image_path):
                dicom2nifti.convert_directory(image_path, temp_dir, reorient_nifti=True)
            else:
                # Single DICOM file
                dicom_image = pydicom.dcmread(image_path)
                dicom2nifti.convert_dicom.dicom_array_to_nifti(
                    dicom_image, temp_dir, reorient_nifti=True
                )
            
            # Load the converted NIFTI file
            nifti_file = os.path.join(temp_dir, os.listdir(temp_dir)[0])
            return nib.load(nifti_file)
