import numpy as np
import nibabel as nib
from nilearn import image
from nipype.interfaces import fsl, spm
import os

#TODO:
# slice order and the time acquisition used in the slice timing correction should match your actual MRI data acquisition parameters
# recheck errors in this file and libraries

class MotionCorrection:
    def __init__(self, config: dict):
        self.config = config

    def run(self, image):
        if self.config['methods']['volume']['enabled']:
            return self.volume_realignment(image)
        if self.config['methods']['slice_timing']['enabled']:
            return self.slice_timing_realignment(image)
        else:
            raise ValueError(f"Invalid method {self.config['methods']}")

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
        out_file = mcflt.outputs.out_file

        # Ensure the output file was created
        if not os.path.exists(out_file):
            raise FileNotFoundError(f"Expected output file not found at {out_file}")

        return out_file
    
    def slice_timing_realignment(self, image):
# Ensure the image file exists
        if not os.path.exists(image):
            raise FileNotFoundError(f"No file found at {image}")

        # Load the image
        img = nib.load(image)

        # Get TR from image header
        header = img.header
        tr = header.get_zooms()[-1]

        # Assume that slices are acquired interleaved ascending and time acquisition is '1' (you need to adjust this according to your own data)
        time_acquisition = tr - tr/img.shape[-1]

        # Define SPM SliceTiming correction instance
        st = spm.SliceTiming(in_file=image, num_slices=img.shape[-1], time_acquisition=time_acquisition, 
                             time_repetition=tr, slice_order=list(range(1, img.shape[-1] + 1, 2)) + list(range(2, img.shape[-1] + 1, 2)))
        try:
            st.run()
        except Exception as e:
            raise RuntimeError(f"SPM SliceTiming failed with error: {e}")

        # Output path of the slice timing corrected image
        out_file = st.outputs.timecorrected_files

        # Ensure the output file was created
        if not os.path.exists(out_file):
            raise FileNotFoundError(f"Expected output file not found at {out_file}")

        return out_file
