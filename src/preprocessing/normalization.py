# pylint: disable=invalid-name
"""Module for normalizing medical images."""
import numpy as np
from skimage import exposure
from src.preprocessing.base_processor import BaseProcessor


class Normalization(BaseProcessor):
    def __init__(self, config: dict):
        super().__init__(config)
        self.methods = {
            "intensity": self.intensity_normalization,
            "zscore": self.zscore_normalization,
            "histogram": self.histogram_normalization,
            "whitening": self.whitening_normalization,
            "min_max": self.min_max_normalization
        }

    def run(self, image, image_path):
        """
        Apply enabled normalization methods to the image
        """
        return self.run_methods(image, image_path, suffix="normalized", apply_to_data=True)

    def intensity_normalization(self, image, config):
        """
        Robust intensity normalization using percentile clipping
        """
        min_value = config.get('min_value', 0.0)
        max_value = config.get('max_value', 1.0)
        p_low, p_high = config.get('percentiles', [2, 98])

        # Calculate percentiles for robust scaling
        p_min, p_max = np.percentile(image, [p_low, p_high])

        # Clip the image to the percentile range
        image_clipped = np.clip(image, p_min, p_max)

        # Scale to desired range
        image_normalized = (image_clipped - p_min) / (p_max - p_min)
        image_normalized = image_normalized * (max_value - min_value) + min_value

        return image_normalized

    def zscore_normalization(self, image, config):
        """
        Z-score normalization with option for robust scaling
        """
        robust = config.get('robust', False)

        if robust:
            # Robust z-score using median and IQR
            center = np.median(image)
            scale = np.percentile(image, 75) - np.percentile(image, 25)
            scale = np.where(scale == 0, 1e-8, scale)  # Avoid division by zero
        else:
            # Standard z-score using mean and std
            center = np.mean(image)
            scale = np.std(image)
            scale = np.where(scale == 0, 1e-8, scale)  # Avoid division by zero

        return (image - center) / scale

    def histogram_normalization(self, image, config):
        """
        Histogram equalization with optional normalization
        """
        n_bins = config.get('n_bins', 256)
        normalize = config.get('normalize', True)

        # Perform histogram equalization
        image_eq = exposure.equalize_hist(image, nbins=n_bins)

        if normalize:
            image_eq = (image_eq - np.min(image_eq)) / (np.max(image_eq) - np.min(image_eq))

        return image_eq

    def whitening_normalization(self, image, config):
        """
        Memory-efficient implementation of ZCA whitening
        """
        epsilon = config.get('epsilon', 1e-8)

        # Process each slice separately to save memory
        if image.ndim == 3:
            whitened = np.zeros_like(image)
            for i in range(image.shape[0]):
                whitened[i] = self._whiten_2d(image[i], epsilon)
            return whitened

        return self._whiten_2d(image, epsilon)

    def _whiten_2d(self, image_2d, epsilon):
        """
        Helper function to whiten 2D slices
        """
        # Reshape to 2D array
        X = image_2d.reshape(-1, 1)

        # Center the data
        X_centered = X - np.mean(X)

        # Compute covariance (scalar for 2D slice)
        cov = np.dot(X_centered.T, X_centered) / X_centered.shape[0]

        # For 2D slice, this simplifies to scalar operations
        zca_scalar = 1.0 / np.sqrt(cov + epsilon)

        # Apply whitening
        X_whitened = X_centered * zca_scalar

        return X_whitened.reshape(image_2d.shape)

    def min_max_normalization(self, image, config):
        """
        Min-max normalization to a specific range
        """
        min_value = config.get('min_value', 0.0)
        max_value = config.get('max_value', 1.0)

        img_min = np.min(image)
        img_max = np.max(image)

        # Avoid division by zero
        if img_max - img_min == 0:
            return np.zeros_like(image)

        # Scale to [0, 1] first then to [min_value, max_value]
        image_normalized = (image - img_min) / (img_max - img_min)
        image_normalized = image_normalized * (max_value - min_value) + min_value

        return image_normalized
