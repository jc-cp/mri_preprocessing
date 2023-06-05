import lapgm
import SimpleITK as sitk
import os

# TODO: 
# - do proper LAPGM implmenetation

class BiasFieldCorrection:
    def __init__(self, config: dict):
        self.config = config

    def run(self, image: str):
        if self.config['methods']['itk']['enabled']:
            return self.itk_bias_field_correction(image)
        elif self.config['methods']['lapgm']['enabled']:
            return self.lapgm_bias_field_correction(image)
        else:
            raise ValueError("No valid bias field correction method enabled in configuration.")

    def itk_bias_field_correction(self, image: str):
        # Ensure the image file exists
        if not os.path.exists(image):
            raise FileNotFoundError(f"No file found at {image}")

        shrinking_factor = self.config['methods']['itk']['parameters']['shrink_factor']

        # Load the image
        img = sitk.ReadImage(image)

        # Create the corrector object
        corrector = sitk.N4BiasFieldCorrectionImageFilter()

        # Set parameters
        corrector.SetMaximumNumberOfIterations(self.config['methods']['itk']['parameters']['number_of_iterations'])
        corrector.SetConvergenceThreshold(self.config['methods']['itk']['parameters']['convergence_threshold'])


        # Run the correction
        try:
            corrected_image = corrector.Execute(img, shrinking_factor)
        except Exception as e:
            raise RuntimeError(f"SimpleITK N4BiasFieldCorrection failed with error: {e}")

        # Save the result and return the file path
        corrected_image_path = os.path.splitext(image)[0] + "_corrected.nii.gz"
        sitk.WriteImage(corrected_image, corrected_image_path)

        return corrected_image_path

    def lapgm_bias_field_correction(self, image: str):
        # Ensure the image file exists
        if not os.path.exists(image):
            raise FileNotFoundError(f"No file found at {image}")

        # TODO: LAPGEM bias field correction would go here

        # For this example, just returning the input file
        print("LAPGEM method is not implemented. Returning input file.")
        return image
