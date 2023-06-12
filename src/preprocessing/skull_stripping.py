import SimpleITK as sitk



class SkullStripping:
    def __init__(self, config: dict):
        self.config = config
        self.methods = {
            "threshold": self.threshold_skull_stripping,
            "morphological": self.morphological_skull_stripping,
            "atlas": self.atlas_skull_stripping
        }

    def run(self, image, path: str):
        for method_name, method in self.methods.items():
            if self.config['methods'][method_name]['enabled']:
                image = method(image, path)
        return image


    def threshold_skull_stripping(self, image, path):
        # Get parameters from config
        threshold = self.config['threshold']['value']

        # Perform threshold-based skull stripping
        stripped = image > threshold
        return stripped

    def morphological_skull_stripping(self, image, path):
        # Perform morphological operations
        # Note: this is a simplified example and may need to be adapted
        binary_image = sitk.BinaryThreshold(image)
        stripped = sitk.BinaryMorphologicalClosing(binary_image)
        return stripped

    def atlas_skull_stripping(self, image, path):
        # Get parameters from config
        atlas_path = self.config['atlas']['path']

        # Load atlas
        atlas = sitk.ReadImage(atlas_path)

        # Register atlas to subject's image
        # Note: registration is a complex task and this is a simplified example
        transform = sitk.CenteredTransformInitializer(atlas, image, sitk.Euler3DTransform())
        registered_atlas = sitk.Resample(atlas, image, transform)

        # Apply atlas mask to remove skull
        mask = sitk.BinaryThreshold(registered_atlas)
        stripped = sitk.Mask(image, mask)

        return stripped