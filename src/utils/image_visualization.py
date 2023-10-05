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
        self.output_file = config["output_file"]

    def run(self, initial_image, template, processed_data_by_step, applied_steps):
        """
        Visualizes medical images before and after processing.
        ... [rest of the docstring remains unchanged] ...
        """
        template = nib.load(template)
        template = nib.as_closest_canonical(template)
        if not processed_data_by_step:
            raise ValueError("No image data to visualize. 'image_data_dict' is empty.")

        n_steps = len(applied_steps)

        # Create combined subplots
        n_rows = n_steps // 2 + 1 if n_steps % 2 == 0 else n_steps // 2 + 2
        _, axes = plt.subplots(n_rows, 2, figsize=(20, 5 * n_rows), squeeze=False)

        # Display initial image and template
        axes[0, 0].imshow(self._get_slice(initial_image).T, cmap="gray", origin="lower")
        axes[0, 0].set_title("Initial Image")
        axes[0, 1].imshow(self._get_slice(template).T, cmap="gray", origin="lower")
        axes[0, 1].set_title("Template Image")

        # Display images after each preprocessing step
        for i, step_name in enumerate(applied_steps):
            image_after = processed_data_by_step[i]
            slice_after = self._get_slice(image_after)

            # Calculate row and column index
            row = (i // 2) + 1  # Incremented by 1 to account for the initial row
            col = i % 2

            # The 'After [step]' image in the respective column
            axes[row, col].imshow(slice_after.T, cmap="gray", origin="lower")
            axes[row, col].set_title(f"After {step_name}")

        plt.tight_layout()
        plt.savefig(self.output_file)

    def _get_slice(self, image):
        z_midpoint = image.shape[2] // 2
        if isinstance(image, nib.nifti1.Nifti1Image):
            return image.get_fdata()[:, :, z_midpoint]
        else:
            try:
                nib_image = sitk_to_nib(image)
                return nib_image.get_fdata()[:, :, z_midpoint]
            except TypeError:
                print(
                    "Unsupported image type. Currently only nibabel.nifti1.Nifti1Image"
                    "and Sikt conversion is supported."
                )
