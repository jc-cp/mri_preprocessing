"""
A module for loading medical images from DICOM or NIFTI files.
"""
import os

import nibabel as nib
import pandas as pd
from pydicom import dcmread
from pydicom.filebase import DicomBytesIO


class ImageLoading:
    """
    Class description:
        1. Takes in a configuration dictionary that can specify a CSV file with image paths,
        a directory with image paths, and a flag for whether to recursively search for images.
        2. Retrieves image paths from a CSV file, if provided, or directly from the configuration.
        3. Searches for images recursively in directories if the recursive flag is set to True,
        otherwise it only searches for images in the specified directories.
        4. Checks whether the images are in DICOM or NIFTI format, and loads them appropriately.
        5. Adds all the loaded images to a list and returns them.
    """

    def __init__(self, config: dict):
        self.file_path = config.get("file_path", None)
        self.recursive = config.get("recursive", False)
        self.paths = config.get("input_dir", None)

    def run(self):
        """Main function to load the files."""
        image_paths = self.get_image_paths()
        for image_path in image_paths:
            try:
                if image_path.lower().endswith(".dcm"):
                    print("Loading images of type: DICOM.")
                    with open(image_path, "rb") as file:
                        bytesio_obj = DicomBytesIO(file.read())
                        image = dcmread(bytesio_obj)
                elif image_path.lower().endswith(".nii") or image_path.lower().endswith(".gz"):
                    print("Loading images of type: NIFTI.")
                    image = nib.load(image_path)
                    image = nib.as_closest_canonical(image)  # Reorient to closest canonical (RAS)
                else:
                    raise ValueError(f"Unsupported file extension in file {image_path}")
            except (IOError, RuntimeError, FileNotFoundError) as error:
                print(f"Error loading image from {image_path}: {str(error)}")
            finally:
                yield image, image_path

    def get_image_paths(self):
        """
        Yields paths to medical image files.

        If a CSV file path is specified in the configuration, the method reads the file
        and yields the image paths in the "image_path" column.
        If a list of image paths is specified in the configuration, the method yields
        the paths directly.
        If a directory path is specified in the configuration, the method searches for
        image files in the directory and yields their paths.
        If no valid image path or file with image paths is provided, the method raises a ValueError.

        Yields:
            A path to a medical image file.

        Raises:
            ValueError: If no valid image path or file with image paths is provided.
            FileNotFoundError: If no file or directory is found at a specified path.
        """
        if self.file_path and self.file_path.lower().endswith(".csv"):
            d_f = pd.read_csv(self.file_path)
            for image_path in d_f["image_path"].tolist():
                yield image_path
        elif self.paths:
            for path in self.paths:
                if os.path.isdir(path):
                    for image_path in self._get_images_from_directory(path):
                        yield image_path
                elif os.path.isfile(path):
                    yield path
                else:
                    raise FileNotFoundError(f"No file or directory found at {path}")
        else:
            raise ValueError("No valid image path or file with image paths provided.")

    def _get_images_from_directory(self, directory):
        if self.recursive:
            for root, _, files in os.walk(directory):
                for file in files:
                    if file.lower().endswith((".dcm", ".nii", ".gz")):
                        yield os.path.join(root, file)
        else:
            for f in os.listdir(directory):
                if os.path.isfile(os.path.join(directory, f)) and f.lower().endswith(
                    (".dcm", ".nii", ".gz")
                ):
                    yield os.path.join(directory, f)
