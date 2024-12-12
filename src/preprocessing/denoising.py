from skimage.restoration import denoise_nl_means, denoise_tv_chambolle, denoise_bilateral, denoise_wavelet
from skimage.filters import gaussian
import numpy as np
from scipy.signal import medfilt
import nibabel as nib
import os
from src.utils.helper_functions import prepare_output_directory


class Denoising:
    def __init__(self, config: dict):
        self.config = config
        self.methods = {
            "gaussian": self.gaussian_denoising,
            "nlm": self.nlm_denoising,
            "tv": self.tv_denoising,
            "bilateral": self.bilateral_denoising,
            "aniso_diffusion": self.aniso_diffusion_denoising,
            "wavelet": self.wavelet_denoising,
            "medfilt": self.medfilt_denoising
        }

    def run(self, image, image_path):
        """
        Expects a nibabel image object or numpy array
        Returns denoised image data
        """
        saving_images = self.config["saving_files"]
        output_dir = self.config["output_dir"]  
        # Convert nibabel image to numpy array if needed
        if isinstance(image, nib.Nifti1Image):
            image_data = image.get_fdata()
        else:
            image_data = image

        # Apply enabled denoising methods
        for method_name, method in self.methods.items():
            if self.config['methods'][method_name]['enabled']:
                func = self.methods.get(method_name, None)
                if func:
                    image_data = func(image_data, self.config['methods'][method_name])
                if saving_images:
                    new_dir, img_id = prepare_output_directory(output_dir, image_path)
                    filename = os.path.join(new_dir, f"{img_id}_{method_name}_denoised.nii.gz")
                    nib.save(image, filename)
        
        return nib.Nifti1Image(image_data, image.affine, image.header)

    def gaussian_denoising(self, image, config):
        sigma = config.get('sigma_gaussian', 1)
        smoothed = gaussian(image, sigma=sigma)

        return smoothed

    def nlm_denoising(self, image, config):
        h = config.get('h', 1.15)
        search_radius = config.get('search_radius', 3)
        patch_radius = config.get('patch_radius', 1)

        # Handle 3D images slice by slice
        if image.ndim == 3:
            denoised = np.zeros_like(image)
            for i in range(image.shape[0]):
                denoised[i] = denoise_nl_means(image[i], 
                                             h=h * np.std(image[i]),
                                             patch_size=patch_radius,
                                             patch_distance=search_radius,
                                             fast_mode=True)
            return denoised
        return denoise_nl_means(image, h=h * np.std(image),
                              patch_size=patch_radius,
                              patch_distance=search_radius,
                              fast_mode=True)
    
    def tv_denoising(self, image, config):
        weight = config.get('weight', 0.1)
        n_iter_max = config.get('n_iter_max', 200)
        
        return denoise_tv_chambolle(image, weight=weight,
                                  max_num_iter=n_iter_max,
                                  channel_axis=None)  # None for 3D images

    def bilateral_denoising(self, image, config):
        """
        Apply bilateral filtering for edge-preserving smoothing
        """
        win_size = config.get('win_size', 5)
        sigma_color = config.get('sigma_color', 0.1)
        sigma_spatial = config.get('sigma_spatial', 1.0)
        bins = config.get('bins', 10000)
        mode = config.get('mode', 'constant')
        cval = config.get('cval', 0)

        # Handle 3D images slice by slice
        if image.ndim == 3:
            denoised = np.zeros_like(image)
            for i in range(image.shape[0]):
                denoised[i] = denoise_bilateral(
                    image[i],
                    win_size=win_size,
                    sigma_color=sigma_color,
                    sigma_spatial=sigma_spatial,
                    bins=bins,
                    mode=mode,
                    cval=cval
                )
            return denoised
        
        return denoise_bilateral(
            image,
            win_size=win_size,
            sigma_color=sigma_color,
            sigma_spatial=sigma_spatial,
            bins=bins,
            mode=mode,
            cval=cval
        )

    def aniso_diffusion_denoising(self, image, config):
        """
        Implementation of Perona-Malik anisotropic diffusion.
        """
        n_iter = config.get('n_iter', 10)
        kappa = config.get('kappa', 50)
        gamma = config.get('gamma', 0.1)
        option = config.get('option', 1)

        # Copy the image to avoid modifying the original
        img = np.copy(image).astype(np.float32)

        # Initialize some parameters
        dx = 1
        dy = 1
        dd = np.sqrt(2)

        # 2D to 3D expansion of directional vectors
        if image.ndim == 3:
            for _ in range(n_iter):
                # Calculate gradients
                deltaS = np.roll(img, -1, axis=0) - img
                deltaN = np.roll(img, 1, axis=0) - img
                deltaE = np.roll(img, -1, axis=1) - img
                deltaW = np.roll(img, 1, axis=1) - img
                deltaU = np.roll(img, -1, axis=2) - img
                deltaD = np.roll(img, 1, axis=2) - img

                # Calculate conduction gradients
                if option == 1:
                    cS = np.exp(-(deltaS/kappa)**2)
                    cN = np.exp(-(deltaN/kappa)**2)
                    cE = np.exp(-(deltaE/kappa)**2)
                    cW = np.exp(-(deltaW/kappa)**2)
                    cU = np.exp(-(deltaU/kappa)**2)
                    cD = np.exp(-(deltaD/kappa)**2)
                elif option == 2:
                    cS = 1 / (1 + (deltaS/kappa)**2)
                    cN = 1 / (1 + (deltaN/kappa)**2)
                    cE = 1 / (1 + (deltaE/kappa)**2)
                    cW = 1 / (1 + (deltaW/kappa)**2)
                    cU = 1 / (1 + (deltaU/kappa)**2)
                    cD = 1 / (1 + (deltaD/kappa)**2)

                # Update image
                img += gamma * (
                    (cN * deltaN + cS * deltaS) / dx +
                    (cE * deltaE + cW * deltaW) / dy +
                    (cU * deltaU + cD * deltaD) / dd
                )

        else:  # 2D case
            for _ in range(n_iter):
                # Calculate gradients
                deltaS = np.roll(img, -1, axis=0) - img
                deltaN = np.roll(img, 1, axis=0) - img
                deltaE = np.roll(img, -1, axis=1) - img
                deltaW = np.roll(img, 1, axis=1) - img

                # Calculate conduction gradients
                if option == 1:
                    cS = np.exp(-(deltaS/kappa)**2)
                    cN = np.exp(-(deltaN/kappa)**2)
                    cE = np.exp(-(deltaE/kappa)**2)
                    cW = np.exp(-(deltaW/kappa)**2)
                elif option == 2:
                    cS = 1 / (1 + (deltaS/kappa)**2)
                    cN = 1 / (1 + (deltaN/kappa)**2)
                    cE = 1 / (1 + (deltaE/kappa)**2)
                    cW = 1 / (1 + (deltaW/kappa)**2)

                # Update image
                img += gamma * (
                    (cN * deltaN + cS * deltaS) / dx +
                    (cE * deltaE + cW * deltaW) / dy
                )

        return img

    def wavelet_denoising(self, image, config):
        wavelet = config.get('wavelet', 'db1')
        sigma = config.get('sigma_wavelet')
        wavelet_levels = config.get('wavelet_levels', 3)
        mode = config.get('mode', 'soft')

        return denoise_wavelet(image, 
                             wavelet=wavelet,
                             sigma=sigma,
                             wavelet_levels=wavelet_levels,
                             mode=mode,
                             channel_axis=None)  # None for 3D images
    
    def medfilt_denoising(self, image, config):
        # Get parameters from config
        kernel_size = config.get('kernel_size', 3)
        return medfilt(image, kernel_size)