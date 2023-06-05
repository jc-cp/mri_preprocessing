from nipype.interfaces import fsl
import os


class MotionCorrection:
    def __init__(self, config: dict):
        self.config = config

    def run(self, image):
        if self.config['enabled']:
            return self.volume_realignment(image)
        else:
            return image

    def volume_realignment(self, image):
       # Ensure the image file exists
        if not os.path.exists(image):
            raise FileNotFoundError(f"No file found at {image}")

        # Define the MCFLIRT motion correction instance
        mcflt = fsl.MCFLIRT(in_file=image, cost='mutualinfo')
        
        try:
            mcflt.run()  
        except Exception as e:
            raise RuntimeError(f"MCFLIRT failed with error: {e}")
        
        # Output path of the realigned image
        out_file = mcflt.output_spec.out_file

        # Ensure the output file was created
        if not os.path.exists(str(out_file)):
            raise FileNotFoundError(f"Expected output file not found at {out_file}")

        return out_file