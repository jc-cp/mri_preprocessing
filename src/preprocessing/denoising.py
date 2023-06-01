import SimpleITK as sitk
from skimage.restoration import denoise_nl_means, estimate_sigma, denoise_tv_chambolle, denoise_bilateral, denoise_wavelet
from skimage.util import img_as_float
import numpy as np

class Denoising:
    def __init__(self, config: dict):
        self.config = config

    def run(self, image):
        if self.config['methods']['gaussian']['enabled']:
            return self.gaussian_denoising(image)
        if self.config['methods']['nlm']['enabled']:
            return self.nlm_denoising(image)
        if self.config['methods']['tv']['enabled']:
            return self.tv_denoising(image)
        if self.config['methods']['aniso_diffusion']['enabled']:
            return self.aniso_diffusion(image)
        if self.config['methods']['wavelet']['enabled']:
            return self.wavelet_denoising(image)
        else:
            raise ValueError(f"Invalid method {self.config['methods']}")

    def gaussian_denoising(self, image):
        # Get parameters from config
        sigma = self.config['methods']['gaussian']['sigma']

        # Perform Gaussian smoothing
        smoothed = sitk.SmoothingRecursiveGaussian(image, sigma)

        return smoothed

    def nlm_denoising(self, image):
        # Get parameters from config
        search_radius = self.config['methods']['nlm']['search_radius']
        patch_radius = self.config['methods']['nlm']['patch_radius']
        channel_axis = self.config['methods']['nlm']['channel_axis']


        # Convert SimpleITK Image to NumPy array for skimage processing
        image_array = sitk.GetArrayFromImage(image)

        # Estimate the noise standard deviation from the image
        sigma_est = np.mean(estimate_sigma(image_array, channel_axis=channel_axis))

        # Perform non-local means denoising
        denoised_array = denoise_nl_means(image_array, h=1.15 * sigma_est, fast_mode=True,
                                          patch_size=patch_radius, patch_distance=search_radius)

        # Convert denoised NumPy array back to SimpleITK Image
        denoised = sitk.GetImageFromArray(denoised_array)

        return denoised
    
    def tv_denoising(self, image):
        # Get parameters from config
        weight = self.config['methods']['tv']['weight']
        channel_axis = self.config['methods']['tv']['channel_axis']

        # Convert SimpleITK Image to NumPy array for skimage processing
        image_array = sitk.GetArrayFromImage(image)
        image_array = img_as_float(image_array)

        # Perform total variation denoising
        denoised_array = denoise_tv_chambolle(image_array, weight=weight, channel_axis=channel_axis)

        # Convert denoised NumPy array back to SimpleITK Image
        denoised = sitk.GetImageFromArray(denoised_array)

        return denoised

    def aniso_diffusion(self, image):
        # Get parameters from config
        sigma_range = self.config['methods']['aniso_diffusion']['sigma_range']
        sigma_spatial = self.config['methods']['aniso_diffusion']['sigma_spatial']

        # Convert SimpleITK Image to NumPy array for skimage processing
        image_array = sitk.GetArrayFromImage(image)
        image_array = img_as_float(image_array)

        # Perform bilateral denoising (Perona-Malik anisotropic diffusion)
        denoised_array = denoise_bilateral(image_array, sigma_color=sigma_range, sigma_spatial=sigma_spatial, multichannel=True)

        # Convert denoised NumPy array back to SimpleITK Image
        denoised = sitk.GetImageFromArray(denoised_array)

        return denoised

    def wavelet_denoising(self, image):
        # Get parameters from config
        wavelet = self.config['methods']['wavelet']['wavelet']
        sigma = self.config['methods']['wavelet']['sigma']

        # Convert SimpleITK Image to NumPy array for skimage processing
        image_array = sitk.GetArrayFromImage(image)
        image_array = img_as_float(image_array)

        # Perform wavelet denoising
        denoised_array = denoise_wavelet(image_array, multichannel=True, convert2ycbcr=True, wavelet=wavelet, sigma=sigma)

        # Convert denoised NumPy array back to SimpleITK Image
        denoised = sitk.GetImageFromArray(denoised_array)

        return denoised