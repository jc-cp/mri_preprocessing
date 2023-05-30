import logging
import nibabel as nib


class ImageSaving:
    def __init__(self, config):
        pass

    def run(self, image):
        # Save processed image
        try:
            nib.save(image, 'data/output/processed_image.nii.gz')
            logging.info("Successfully saved processed image.")
        except Exception as e:
            logging.error(f"Error saving processed image: {str(e)}")
            raise e