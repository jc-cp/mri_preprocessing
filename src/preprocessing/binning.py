import numpy as np


class Binning:
    def __init__(self, config: dict):
        self.config = config

    def run(self, image):
        if self.config['methods']['fixed_width']['enabled']:
            return self.fixed_width_binning(image)
        elif self.config['methods']['quantile']['enabled']:
            return self.quantile_binning(image)
        else:
            raise ValueError(f"No enabled method in the config: {self.config}")

    def fixed_width_binning(self, image):
        # Get parameters from config
        bin_width = self.config['methods']['fixed_width']['bin_width']

        # Perform fixed-width binning
        hist, bin_edges = np.histogram(image, bins=np.arange(np.min(image), np.max(image) + bin_width, bin_width))

        # Create new image using bin indices
        new_image = np.digitize(image, bin_edges)

        return new_image

    def quantile_binning(self, image):
        # Get parameters from config
        num_bins = self.config['methods']['quantile']['num_bins']

        # Perform quantile binning
        quantiles = np.quantile(image, np.linspace(0, 1, num_bins + 1))
        new_image = np.digitize(image, quantiles)

        return new_image

