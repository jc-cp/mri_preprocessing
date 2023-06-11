import os
import nibabel as nib
from pydicom import dcmread
from pydicom.filebase import DicomBytesIO
import pandas as pd

class ImageLoading:
    '''
    Class description:
        1. Takes in a configuration dictionary that can specify a CSV file of image paths (file_path), a list of image paths (image_paths), and a flag for whether to recursively search for images (recursive).
        2. Retrieves image paths from a CSV file, if provided, or directly from the configuration.
        3. Searches for images recursively in directories if the recursive flag is set to True, otherwise it only searches for images in the specified directories.
        4. Checks whether the images are in DICOM or NIFTI format, and loads them appropriately.
        5. Adds all the loaded images to a list and returns them.
    '''

    def __init__(self, config: dict):
        self.file_path = config.get('file_path', None)
        self.recursive = config.get('recursive', False)
        self.paths = config.get('input_dir', None)

    def run(self):
        image_paths = self._get_image_paths()
        images = []
        for image_path in image_paths:
            try:
                if image_path.lower().endswith('.dcm'):
                    print('Loading DICOM image.')
                    with open(image_path, 'rb') as file:
                        bytesio_obj = DicomBytesIO(file.read())
                        image = dcmread(bytesio_obj)
                elif image_path.lower().endswith('.nii') or image_path.lower().endswith('.gz'):
                    print('Loading Nifti image.')
                    image = nib.load(image_path)
                    image = nib.as_closest_canonical(image) # Reorient to closest canonical (RAS)
                else:
                    raise ValueError(f"Unsupported file extension in file {image_path}")
                images.append(image)
            except Exception as e:
                raise RuntimeError(f"Error loading image from {image_path}: {str(e)}")
        return images, image_paths

    def _get_image_paths(self):
        if self.file_path and self.file_path.lower().endswith('.csv'):
            df = pd.read_csv(self.file_path)
            return df['image_path'].tolist()
        elif self.paths:
            image_paths = []
            for path in self.paths:
                if os.path.isdir(path):
                    image_paths.extend(self._get_images_from_directory(path))
                elif os.path.isfile(path):
                    image_paths.append(path)
                else:
                    raise FileNotFoundError(f"No file or directory found at {path}")
            if not image_paths:
                raise ValueError("No images found in the provided paths.")
            return image_paths
        else:
            raise ValueError("No valid image path or file with image paths provided.")

    def _get_images_from_directory(self, directory):
        if self.recursive:
            image_files = []
            for root, _, files in os.walk(directory):
                for file in files:
                    if file.lower().endswith(('.dcm', '.nii', '.gz')):
                        image_files.append(os.path.join(root, file))
            return image_files
        else:
            return [os.path.join(directory, f) for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f)) and f.lower().endswith(('.dcm', '.nii', '.gz'))]


