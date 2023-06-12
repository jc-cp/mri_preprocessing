from nipype.interfaces.fsl import FLIRT
from nipype.interfaces.ants import ResampleImageBySpacing
import os
from scipy.ndimage import zoom
import nibabel as nib
import numpy as np

class Resampling:
    def __init__(self, config: dict):
        self.config = config
        self.methods = {
            "ants": self.resample_with_ants,
            "scipy": self.resample_with_scipy
        }

    def run(self, image, path: str):
        for method_name, method in self.methods.items():
            if self.config['methods'][method_name]['enabled']:
                image = method(image, path)
        return image

    def resample_with_ants(self, image, path: str):
        # Ensure the image file exists
        if not os.path.exists(path):
            raise FileNotFoundError(f"No file found at {path}")

        # Define the ANTs resampling instance
        resample = ResampleImageBySpacing(dimension=3)
        resample.inputs.input_image = path
        resample.inputs.out_spacing = self.config['methods']['ants']['spacing']
        resample.inputs.apply_smoothing = self.config['methods']['ants']['smoothing'] 
   
        try:
            result = resample.run()
            print(type(result))
        except Exception as e:
            raise RuntimeError(f"ANTs ResampleImageBySpacing failed with error: {e}")

        return result.outputs

    def resample_with_scipy(self, image, path):
        '''
        order=0: Nearest-neighbor interpolation
        order=1: Linear interpolation (bilinear for 2D images, trilinear for 3D images)
        order=2: Quadratic (cubic for 2D images, etc.)
        order=3: Cubic (quartic for 2D images, etc.)
        '''
        numpy_img = image.get_fdata()
        scale_factor = self.config['methods']['scipy']['scale_factor']
        order = self.config['methods']['scipy']['order']

        rescaled_image = zoom(numpy_img, scale_factor, order=order)
        # Define affine transformation
        affine = np.eye(4)

        # Create the Nibabel image
        nifti_rescaled_image = nib.Nifti1Image(rescaled_image, affine)

        return nifti_rescaled_image