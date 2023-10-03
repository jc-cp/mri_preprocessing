import matplotlib.pyplot as plt
import nibabel as nib


class ImageVisualization:
    def __init__(self, config: int):
        self.slice_index = config["slice_index"]
        self.output_file = config["output_file"]

    def run(self, original_data_by_step, processed_data_by_step, applied_steps):
        if not original_data_by_step or not processed_data_by_step:
            raise ValueError("No image data to visualize. 'image_data_dict' is empty.")

        n_steps = len(applied_steps)
        n_images = len(original_data_by_step[0])
        fig, axes = plt.subplots(n_steps, 2 * n_images, figsize=(20, 5 * n_steps), squeeze=False)

        for i, step_instance in enumerate(applied_steps):
            images_before = original_data_by_step[i]
            images_after = processed_data_by_step[i]

            for j, (image_before, image_after) in enumerate(zip(images_before, images_after)):
                slice_before = self._get_slice(image_before)
                slice_after = self._get_slice(image_after)

                axes[i, 2 * j].imshow(slice_before.T, cmap="gray", origin="lower")
                axes[i, 2 * j].set_title(f"Before {step_instance}")

                axes[i, 2 * j + 1].imshow(slice_after.T, cmap="gray", origin="lower")
                axes[i, 2 * j + 1].set_title(f"After {step_instance}")

        plt.tight_layout()
        plt.savefig(self.output_file)  # Saves the plot to 'output.png'
        # plt.show(block=True)

    def _get_slice(self, image):
        if isinstance(image, nib.nifti1.Nifti1Image):
            return image.get_fdata()[:, :, self.slice_index]
        else:
            raise TypeError(
                "Unsupported image type. Currently only nibabel.nifti1.Nifti1Image is supported."
            )
