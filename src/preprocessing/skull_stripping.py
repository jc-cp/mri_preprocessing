import SimpleITK as sitk



class SkullStripping:
    def __init__(self, config: dict):
        self.config = config

    def run(self, image):
        if self.config['methods']['threshold']['enabled']:
            return self.threshold_skull_stripping(image)
        if self.config['methods']['morphological']['enabled']:
            return self.morphological_skull_stripping(image)
        if self.config['methods']['atlas']['enabled']:
            return self.atlas_skull_stripping(image)
        else:
            raise ValueError(f"Invalid method {self.config['methods']}")

    def threshold_skull_stripping(self, image):
        # Get parameters from config
        threshold = self.config['threshold']['value']

        # Perform threshold-based skull stripping
        stripped = image > threshold
        return stripped

    def morphological_skull_stripping(self, image):
        # Perform morphological operations
        # Note: this is a simplified example and may need to be adapted
        # for your specific use case
        binary_image = sitk.BinaryThreshold(image)
        stripped = sitk.BinaryMorphologicalClosing(binary_image)
        return stripped

    def atlas_skull_stripping(self, image):
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