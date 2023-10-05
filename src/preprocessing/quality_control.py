import nibabel as nib
import numpy as np


class QualityControl:
    def __init__(self, config: dict):
        self.config = config

    def run(self, image):
        """Check image quality and report if it fails at some point."""
        try:
            img = nib.load(image)
        except ValueError as error:
            print(f"Unable to load image {image}. Error: {error}")

        # Check image dimensions
        expected_dims = self.config.get("expected_dims")
        if expected_dims is not None:
            if img.shape != tuple(expected_dims):
                raise ValueError(
                    f"Image {image} has dimensions {img.shape}, expected {expected_dims}"
                )

        # Check voxel size (resolution)
        expected_voxel_size = self.config.get("expected_voxel_size")
        if expected_voxel_size is not None:
            voxel_size = img.header.get_zooms()[:3]  # Assuming 3D image
            if voxel_size != tuple(expected_voxel_size):
                raise ValueError(
                    f"Image {image} has voxel size {voxel_size}, expected {expected_voxel_size}"
                )

        # Check for NaN values
        if np.any(np.isnan(img.get_fdata())):
            raise ValueError(f"Image {image} contains NaN values")

        return True
