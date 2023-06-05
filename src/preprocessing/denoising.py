from skimage.restoration import denoise_nl_means, denoise_tv_chambolle, denoise_bilateral, denoise_wavelet
from skimage.filters import gaussian
import numpy as np
from scipy.signal import medfilt


class Denoising:
    def __init__(self, config: dict):
        self.config = config
        self.methods = {
            "gaussian": self.gaussian_denoising,
            "nlm": self.nlm_denoising,
            "tv": self.tv_denoising,
            "aniso_diffusion": self.aniso_diffusion_denoising,
            "wavelet": self.wavelet_denoising,
            "medfilt": self.medfilt_denoising
        }

    def run(self, image):
        for method_name, method in self.methods.items():
            if self.config['methods'][method_name]['enabled']:
                image = method(image, self.config['methods'][method_name])
        return image

    def gaussian_denoising(self, image, config):
        sigma = config.get('sigma_gaussian', 1)
        smoothed = gaussian(image, sigma=sigma)

        return smoothed

    def nlm_denoising(self, image, config):
        search_radius = config.get('search_radius', 3)
        patch_radius = config.get('patch_radius', 1)

        std_dev = np.std(image)

        # Perform non-local means denoising
        denoised = denoise_nl_means(image, h=1.15 * std_dev, fast_mode=True,
                                          patch_size=patch_radius, patch_distance=search_radius)

        return denoised
    
    def tv_denoising(self, image, config):
        # Get parameters from config
        weight = config.get('weight', 0.1)
        channel_axis = config.get('channel_axis', 3)

        # Perform total variation denoising
        denoised = denoise_tv_chambolle(image, weight=weight, channel_axis=channel_axis)

        return denoised

    def aniso_diffusion_denoising(self, image, config):
        # Get parameters from config
        sigma_range = config.get('sigma_range')
        sigma_spatial = config.get('sigma_spatial')

        # Perform bilateral denoising (Perona-Malik anisotropic diffusion)
        denoised = denoise_bilateral(image, sigma_color=sigma_range, sigma_spatial=sigma_spatial, multichannel=True)

        return denoised

    def wavelet_denoising(self, image, config):
        # Get parameters from config
        wavelet = config.get('wavelet', 'db1')
        sigma = config.get('sigma_wavelet', None)

        # Perform wavelet denoising
        denoised = denoise_wavelet(image, multichannel=True, convert2ycbcr=True, wavelet=wavelet, sigma=sigma, method='BayesShrink')

        return denoised
    
    def medfilt_denoising(self, image, config):
        # Get parameters from config
        kernel_size = config.get('kernel_size', 3)
        return medfilt(image, kernel_size)