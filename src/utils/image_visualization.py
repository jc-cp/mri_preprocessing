"""Visualization methods for comparing plots."""
import matplotlib.pyplot as plt
import nibabel as nib

from src.utils.helper_functions import sitk_to_nib


class ImageVisualization:
    """
    Initializes an `ImageVisualization` instance.

    Args:
        config (int): A dictionary of configuration parameters.
            The following parameters are supported:
            - slice_index (int): The index of the slice to visualize (default: 0).
            - output_file (str): The path to the output  visualization (default: None).
    """

    def __init__(self, config: int):
        self.slice_index = config["slice_index"]
        self.output_file = config["output_file"]

    def run(self, original_data_by_step, processed_data_by_step, applied_steps):
        """
        Visualizes medical images before and after processing.

        Args:
            original_data_by_step (list): A list of lists of medical images before processing.
            processed_data_by_step (list): A list of lists of medical images after processing.
            applied_steps (list): A list of strings representing the processing steps applied.

        Raises:
            ValueError: If `original_data_by_step` or `processed_data_by_step` is empty.
        """
        if not original_data_by_step or not processed_data_by_step:
            raise ValueError("No image data to visualize. 'image_data_dict' is empty.")

        n_steps = len(applied_steps)
        n_images = len(original_data_by_step[0])
        _, axes = plt.subplots(n_steps, 2 * n_images, figsize=(20, 5 * n_steps), squeeze=False)

        for i, step_name in enumerate(applied_steps):
            images_before = original_data_by_step[i]
            images_after = processed_data_by_step[i]
            print(type(images_after[0]))
            for j, (image_before, image_after) in enumerate(zip(images_before, images_after)):
                slice_before = self._get_slice(image_before)
                slice_after = self._get_slice(image_after)

                axes[i, 2 * j].imshow(slice_before.T, cmap="gray", origin="lower")
                axes[i, 2 * j].set_title(f"Before {step_name}")

                axes[i, 2 * j + 1].imshow(slice_after.T, cmap="gray", origin="lower")
                axes[i, 2 * j + 1].set_title(f"After {step_name}")

        plt.tight_layout()
        plt.savefig(self.output_file)

    def _get_slice(self, image):
        if isinstance(image, nib.nifti1.Nifti1Image):
            return image.get_fdata()[:, :, self.slice_index]
        else:
            try:
                nib_image = sitk_to_nib(image)
                return nib_image.get_fdata()[:, :, self.slice_index]
            except TypeError:
                print(
                    "Unsupported image type. Currently only nibabel.nifti1.Nifti1Image"
                    "and Sikt conversion is supported."
                )
