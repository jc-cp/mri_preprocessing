import matplotlib.pyplot as plt
import nibabel as nib


class ImageVisualization:
    def __init__(self, slice_index: int):
        self.slice_index = slice_index

    def run(self, image_data_dict: dict):
        n_steps = len(image_data_dict)
        fig, axes = plt.subplots(n_steps, 2, figsize=(10, 5 * n_steps))

        for i, (step, (image_before, image_after)) in enumerate(image_data_dict.items()):
            slice_before = self._get_slice(image_before)
            slice_after = self._get_slice(image_after)
            
            axes[i, 0].imshow(slice_before.T, cmap='gray', origin='lower')
            axes[i, 0].set_title(f'Before {step}')

            axes[i, 1].imshow(slice_after.T, cmap='gray', origin='lower')
            axes[i, 1].set_title(f'After {step}')

        plt.tight_layout()
        plt.show()

    def _get_slice(self, image):
        if isinstance(image, nib.nifti1.Nifti1Image):
            return image.get_fdata()[..., self.slice_index]
        else:
            raise TypeError("Unsupported image type. Currently only nibabel.nifti1.Nifti1Image is supported.")
