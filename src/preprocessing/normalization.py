import numpy as np
import SimpleITK as sitk
from skimage import exposure


class Normalization:
    def __init__(self, config: dict):
        self.config = config

    def run(self, image):
        if self.config['methods']['intensity']['enabled']:
            return self.intensity_normalization(image)
        if self.config['methods']['zscore']['enabled']:
            return self.zscore_normalization(image)
        if self.config['methods']['histogram']['enabled']:
            return self.histogram_equalization(image)
        else:
            raise ValueError(f"Invalid method {self.config['methods']}")

    def intensity_normalization(self, image):
        # Convert image to numpy array
        img_arr = sitk.GetArrayFromImage(image)

        # Perform intensity normalization
        img_arr = (img_arr - np.min(img_arr)) / (np.max(img_arr) - np.min(img_arr))

        # Convert array back to sitk image
        img_normalized = sitk.GetImageFromArray(img_arr)
        img_normalized.CopyInformation(image)

        return img_normalized

    def zscore_normalization(self, image):
        # Convert image to numpy array
        img_arr = sitk.GetArrayFromImage(image)

        # Perform z-score normalization
        img_arr = (img_arr - np.mean(img_arr)) / np.std(img_arr)

        # Convert array back to sitk image
        img_normalized = sitk.GetImageFromArray(img_arr)
        img_normalized.CopyInformation(image)

        return img_normalized

    def histogram_equalization(self, image):
        # Convert image to numpy array
        img_arr = sitk.GetArrayFromImage(image)

        # Perform histogram equalization
        img_arr = exposure.equalize_hist(img_arr)

        # Convert array back to sitk image
        img_normalized = sitk.GetImageFromArray(img_arr)
        img_normalized.CopyInformation(image)

        return img_normalized
