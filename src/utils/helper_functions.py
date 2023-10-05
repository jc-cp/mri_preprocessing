"""Helper functions for the project."""
import os

import itk
import nibabel as nib
import numpy as np
import SimpleITK as sitk


def sitk_to_nib(sitk_image):
    """Conversion from SimpleITK to Nibabel preserving spatial information."""
    np_image = sitk.GetArrayFromImage(sitk_image)
    np_image = np.transpose(np_image, (2, 1, 0))
    origin = np.array(sitk_image.GetOrigin())
    spacing = np.array(sitk_image.GetSpacing())
    direction = np.array(sitk_image.GetDirection()).reshape((3, 3))

    affine = np.eye(4)
    affine[:3, :3] = direction * spacing
    affine[:3, 3] = origin

    # Create the Nibabel image with the data and affine matrix
    nib_image = nib.Nifti1Image(np_image, affine)

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

    sitk_image = sitk.Cast(sitk_image, sitk.sitkFloat32)

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
    """Simple conversion to .nii format."""
    img = nib.load(nii_gz_path)
    nii_path = nii_gz_path[:-3]
    nib.save(img, nii_path)

    return nii_path


def nib_to_itk(nib_image: nib.Nifti1Image) -> itk.image:
    """
    Convert a nibabel Nifti1Image to an ITK Image while preserving spatial conditions.

    Args:
        nib_image (nib.Nifti1Image): Input nibabel image.

    Returns:
        itk.Image: Converted ITK image.
    """

    # Extract array and affine from nibabel image
    array_data = nib_image.get_fdata()
    affine = nib_image.affine
    order = [2, 1, 0]
    array_data = array_data.transpose(order)
    # Convert array data to ITK image
    itk_image = itk.GetImageFromArray(array_data.astype(np.float32))

    # Extract origin, spacing, and direction from affine
    origin = affine[:3, 3]
    spacing = np.sqrt((affine[:3, :3] ** 2).sum(axis=0))
    direction_matrix = affine[:3, :3] / spacing

    # The direction in ITK is given by the transpose of the direction matrix
    direction = itk.matrix_from_array(np.linalg.inv(direction_matrix).T)

    # Set the spatial information in the ITK image
    itk_image.SetOrigin(origin)
    itk_image.SetSpacing(spacing)
    itk_image.SetDirection(direction)

    return itk_image


def itk_to_nib(itk_image: itk.image) -> nib.Nifti1Image:
    """
    Convert an ITK Image to a nibabel Nifti1Image while preserving spatial conditions.

    Args:
        itk_image (itk.Image): Input ITK image.

    Returns:
        nib.Nifti1Image: Converted nibabel image.
    """

    # Extract array from ITK image
    array_data = itk.GetArrayFromImage(itk_image)

    # Extract origin, spacing, and direction from ITK image
    origin = np.array(itk_image.GetOrigin())
    spacing = np.array(itk_image.GetSpacing())
    direction = itk.array_from_matrix(itk_image.GetDirection())

    # Construct affine from origin, spacing, and direction
    affine = np.eye(4)
    affine[:3, :3] = direction * spacing
    affine[:3, 3] = origin

    order = [2, 1, 0]
    affine[:3, :3] = affine[:3, :3][order]
    array_data = array_data.transpose(order)

    # Create nibabel image with the array and affine
    nib_image = nib.Nifti1Image(array_data, affine)

    return nib_image
