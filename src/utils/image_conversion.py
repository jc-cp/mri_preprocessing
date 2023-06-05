import dicom2nifti
import nibabel as nib
import os
import pydicom
import tempfile


class ImageConversion:
    def __init__(self, config):
        self.enabled = config['enabled']
    
    def run(self, images):
        if not self.enabled:
            return images

        converted_images = []
        for image in images:
            try:
                if isinstance(image, pydicom.dataset.Dataset):
                    # We assume that image is a DICOM file if it's an instance of pydicom.dataset.Dataset
                    with tempfile.TemporaryDirectory() as temp_dir:
                        dicom2nifti.convert_dicom.dicom_array_to_nifti(image, temp_dir, reorient_nifti=True)
                        converted_image = nib.load(os.path.join(temp_dir, os.listdir(temp_dir)[0]))
                        converted_images.append(converted_image)
                elif isinstance(image, nib.Nifti1Image):
                    # If image is a NIFTI file, just pass it through
                    converted_images.append(image)
                else:
                    # If image is not a DICOM file pass it through
                    raise ValueError(f"Unsupported image format: {type(image)}")
            except Exception as e:
                raise RuntimeError(f"Error converting image to NIFTI format: {str(e)}")

        return converted_images
