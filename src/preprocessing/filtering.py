import SimpleITK as sitk
from skimage.filters import threshold_otsu

class Filtering:
    def __init__(self, config: dict):
        self.config = config

    def run(self, image):
        if self.config['methods']['gaussian']['enabled']:
            return self.gaussian_smoothing(image)
        if  self.config['methods']['median']['enabled']:
            return self.median_filtering(image)
        if  self.config['methods']['bilateral']['enabled']:
            return self.bilateral_filtering(image)
        if self.config['methods']['otsu']['enabled']:
            return self.otsu_filtering(image)
        else:
            raise ValueError(f"Invalid method in config")

    def gaussian_smoothing(self, image):
        # Get parameters from config
        sigma = self.config['methods']['gaussian']['sigma']
        smoothed = sitk.SmoothingRecursiveGaussian(image, sigma)
        return smoothed

    def median_filtering(self, image):
        radius = self.config['methods']['median']['radius']
        median_filtered = sitk.Median(image, radius)
        return median_filtered

    def bilateral_filtering(self, image):
        domainSigma = self.config['methods']['bilateral']['domain_sigma']
        rangeSigma = self.config['methods']['bilateral']['range_sigma']
        bilateral_filter = sitk.BilateralImageFilter()
        bilateral_filter.SetDomainSigma(domainSigma)
        bilateral_filter.SetRangeSigma(rangeSigma)
        return bilateral_filter.Execute(image)
    
    def otsu_filtering(self, image):
        # Compute the threshold value with Otsu's method
        thresh = threshold_otsu(image)
        
        # Apply the threshold to the image: all pixels with intensities above the threshold are set to 1, the others to 0
        binary = image > thresh

        return binary
