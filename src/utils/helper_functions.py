"""Helper functions for the project."""
import os

import nibabel as nib
import numpy as np
import SimpleITK as sitk


def sitk_to_nib(sitk_image):
    """Conversion from SimpleITK to Nibabel."""
    np_image = sitk.GetArrayFromImage(sitk_image)
    nib_image = nib.Nifti1Image(np_image, np.eye(4))
    return nib_image


def nib_to_sitk(nib_image):
    """
    Convert a nibabel image to a SimpleITK Image.

    Parameters
    ----------
    nib_image : nibabel image object
        The nibabel image to convert.

    Returns
    -------
    SimpleITK.Image
        The converted SimpleITK image.
    """
    data = nib_image.get_fdata()
    affine = nib_image.affine
    origin = affine[:3, 3]
    direction = affine[:3, :3].flatten()
    spacing = np.sqrt((affine[:3, :3] ** 2).sum(axis=0))

    sitk_image = sitk.GetImageFromArray(np.transpose(data, (2, 1, 0)))
    sitk_image.SetOrigin(origin)
    sitk_image.SetSpacing(spacing)
    sitk_image.SetDirection(direction)

    return sitk_image


def copy_nifti_image(image):
    """
    Creates a deep copy of a NIFTI medical image.

    Args:
        image: The NIFTI medical image to copy.

    Returns:
        A deep copy of the NIFTI medical image.
    """
    data_copy = image.get_fdata().copy()
    header_copy = image.header.copy()
    image_copy = nib.Nifti1Image(data_copy, image.affine, header_copy)

    return image_copy


def prepare_output_directory(output_dir, image_path):
    """Creates output directory for the given image."""
    image_id = image_path.split("/")[-1]
    image_id = image_id.split(".")[0]
    new_dir = os.path.join(output_dir, image_id)
    if os.makedirs(new_dir, exist_ok=True):
        print("Output dir already exists.")
    return new_dir, image_id


def convert_nii_gz_to_nii(nii_gz_path):
    img = nib.load(nii_gz_path)
    nii_path = nii_gz_path[:-3]
    nib.save(img, nii_path)

    return nii_path
