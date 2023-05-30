import logging

#load_dicom_image, load_nifti_image
# TODO: refine this
class ImageLoading:
    def __init__(self, config):
        # Load image based on the format
        try:
            image = steps['load_image'][config['file_format']]('data/input/image_path')  # replace 'image_path' with your actual image path
            logging.info("Successfully loaded image.")
        except Exception as e:
            logging.error(f"Error loading image: {str(e)}")
            raise e

    def run(self):
        pass