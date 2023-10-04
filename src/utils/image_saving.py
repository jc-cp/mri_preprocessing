"""Module for saving images to disk."""
import os

import nibabel as nib


class ImageSaving:
    def __init__(self, config: dict):
        self.output_dir = config["output_dir"]
        self.input_dir = config["input_dir"]

    def run(self, images, input_paths):
        for image, input_path in zip(images, input_paths):
            output_path = self._get_output_path(input_path)
            self._save_image(image, output_path)

    def _get_output_path(self, input_path):
        # Get the relative path to the input file from the root input directory
        relative_path = os.path.relpath(input_path, self.input_dir)

        # Create the same directory structure in the output directory
        output_path = os.path.join(self.output_dir, relative_path)
        base_name = os.path.splitext(os.path.splitext(output_path)[0])[0]
        output_path = base_name + "_pp.nii.gz"

        # Make sure the output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        return output_path

    def _save_image(self, image, output_path):
        try:
            nib.save(image, output_path)
        except RuntimeError as error:
            print(f"Error saving image to {output_path}: {str(error)}")
