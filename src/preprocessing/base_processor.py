"""
Base class for preprocessing steps to eliminate code duplication.

This module defines a `BaseProcessor` class that provides common functionality
for all preprocessing steps, including method execution, file saving, and
image format handling.
"""
import os
import nibabel as nib
from src.utils.helper_functions import prepare_output_directory


class BaseProcessor:
    """
    Base class for preprocessing steps.
    
    Provides common functionality for:
    - Running enabled methods from configuration
    - Saving intermediate results
    - Handling nibabel/numpy conversions
    
    Subclasses should:
    - Define self.methods dict mapping method names to functions
    - Implement individual processing methods
    - Call super().__init__(config) in their __init__
    """
    
    def __init__(self, config: dict):
        """
        Initialize the base processor.
        
        Args:
            config (dict): Configuration dictionary containing:
                - saving_files (bool): Whether to save intermediate results
                - output_dir (str): Directory for saving files
                - methods (dict): Dictionary of method configurations
        """
        self.config = config
        self.methods = {}  # Subclasses should populate this
    
    def _get_image_data(self, image):
        """
        Extract numpy array from image, handling both nibabel and numpy inputs.
        
        Args:
            image: Either nib.Nifti1Image or numpy array
            
        Returns:
            numpy.ndarray: Image data as numpy array
        """
        if isinstance(image, nib.Nifti1Image):
            return image.get_fdata()
        return image
    
    def _create_nifti_image(self, data, reference_image):
        """
        Create a nibabel NIfTI image from data using reference image metadata.
        
        Args:
            data: Numpy array of image data
            reference_image: Reference nibabel image for affine and header
            
        Returns:
            nib.Nifti1Image: New NIfTI image with processed data
        """
        return nib.Nifti1Image(data, reference_image.affine, reference_image.header)
    
    def _save_result(self, image, image_path, method_name, suffix):
        """
        Save processing result to file.
        
        Args:
            image: Image to save (nibabel or numpy)
            image_path: Original image path for naming
            method_name: Name of the method used
            suffix: Suffix for output filename (e.g., 'denoised', 'normalized')
        """
        output_dir = self.config["output_dir"]
        new_dir, img_id = prepare_output_directory(output_dir, image_path)
        filename = os.path.join(new_dir, f"{img_id}_{method_name}_{suffix}.nii.gz")
        
        if isinstance(image, nib.Nifti1Image):
            nib.save(image, filename)
        else:
            # If it's numpy array, we need reference image - this shouldn't happen
            # but handle it gracefully
            raise ValueError(
                f"Cannot save numpy array without reference image metadata. "
                f"Method: {method_name}"
            )
    
    def run_methods(self, image, image_path, suffix, apply_to_data=True):
        """
        Run all enabled methods on the image.
        
        This is the common pattern used by denoising, normalization, etc.
        
        Args:
            image: Input image (nibabel or numpy)
            image_path: Path to original image
            suffix: Suffix for saved files (e.g., 'denoised', 'normalized')
            apply_to_data: If True, extract data and apply methods to numpy array.
                          If False, apply methods to nibabel image directly.
        
        Returns:
            nib.Nifti1Image: Processed image
        """
        saving_images = self.config["saving_files"]
        
        # Get image data if needed
        if apply_to_data:
            image_data = self._get_image_data(image)
        else:
            image_data = image
        
        # Apply enabled methods
        for method_name, method_func in self.methods.items():
            if self.config['methods'][method_name]['enabled']:
                method_config = self.config['methods'][method_name]
                image_data = method_func(image_data, method_config)
                
                # Save if requested
                if saving_images and apply_to_data:
                    # Create temporary nibabel image for saving
                    temp_image = self._create_nifti_image(image_data, image)
                    self._save_result(temp_image, image_path, method_name, suffix)
                elif saving_images and not apply_to_data:
                    self._save_result(image_data, image_path, method_name, suffix)
        
        # Return as nibabel image
        if apply_to_data:
            return self._create_nifti_image(image_data, image)
        return image_data

