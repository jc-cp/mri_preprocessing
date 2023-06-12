import os
from nipype.interfaces import spm
from nipype.interfaces.fsl import FLIRT
import itk
from itk import itkMINCImageIOPython
import nibabel as nib
import numpy as np
import glob

class Registration:
    def __init__(self, config: dict):
        self.config = config
        self.methods = {
            "itk": self.itk_registration,
            "spm": self.spm_registration
        }

    def run(self, image, path: str):
        for method_name, method in self.methods.items():
            if self.config['methods'][method_name]['enabled']:
                image = method(image, path)
        return image

    def itk_registration(self, image, path):
        template = self.config['methods']['itk']['template']
        output_path = self.config['methods']['itk']['output_path']

        # Ensure the image file exists
        if not os.path.exists(template):
            raise FileNotFoundError(f"No file found at {template}")

        fixed_image = itk.imread(template, itk.F)

        # Import Parameter Map
        parameter_object = itk.ParameterObject.New()
        parameter_object.AddParameterFile('data/registration_templates/Parameters_Rigid.txt')

        if "nii" in path:
            # Call registration function
            try:        
                moving_image = itk.imread(path, itk.F)
                image_id = path.split("/")[-1]

                new_dir = output_path+"/"+image_id.split(".")[0]
                if not os.path.exists(new_dir):
                    os.mkdir(new_dir)
                    
                result_image, _ = itk.elastix_registration_method(
                    fixed_image, moving_image,
                    parameter_object=parameter_object,
                    output_directory=new_dir,
                    log_to_console=False)

                itk.imwrite(result_image, new_dir+"/"+image_id.split(".")[0]+'_registered'+'.nii.gz')
                 
                print("Registered ", image_id)
                
                # Convert ITK image to numpy array, create NIfTI image from array
                np_array = itk.GetArrayFromImage(result_image)
                nifti_image = nib.Nifti1Image(np_array, np.eye(4))
                return nifti_image

            except:
                print("Cannot transform", path.split("/")[-1])
        
        else:
            raise FileNotFoundError('File has not .nii suffix on it!')

    def spm_registration(self, image, path):
        # Ensure the image file exists
        if not os.path.exists(path):
            raise FileNotFoundError(f"No file found at {path}")
        
        template = self.config['methods']['spm']['template']

        nii_path = self.convert_nii_gz_to_nii(path)
        deformation_file_path = self.spm_segmentation(image, path)
        
        # Define the SPM Normalize12 instance for registration
        norm12 = spm.Normalize12(jobtype='estwrite',
                                 tpm=template,
                                 apply_to_files=[nii_path],
                                 deformation_file=deformation_file_path)
        
        try:
            result = norm12.run()
            print('type registration result:', type(result))
        
        except Exception as e:
            raise RuntimeError(f"SPM Normalize12 failed with error: {e}")

        return result.outputs
    
    def convert_nii_gz_to_nii(self, nii_gz_path):
        # Load the .nii.gz file
        img = nib.load(nii_gz_path)

        # Derive the .nii file path from the .nii.gz file path
        nii_path = nii_gz_path[:-3]  # Remove the '.gz' from the end

        # Save the image data to a .nii file
        nib.save(img, nii_path)

        return nii_path

    def spm_segmentation(self, image, path):
        # Define the segmentation instance
        segmentation = spm.NewSegment()
        
        # Set input file
        segmentation.inputs.channel_files = path
        
        # Run segmentation
        try:
            seg_result = segmentation.run()
        except Exception as e:
            raise RuntimeError(f"SPM NewSegment failed with error: {e}")
        
        # Cleanup segmentation results
        self.cleanup_segmentation_results(path)
        
        # Return the forward deformation file path
        return seg_result.outputs

    def cleanup_segmentation_results(self, path):
        dir_path = os.path.dirname(path)
        pattern = "c*.nii"  # SPM segmentation results start with 'c'
        files = glob.glob(os.path.join(dir_path, pattern))
        for f in files:
            try:
                os.remove(f)
            except OSError:
                print(f"Error: {f} : {os.strerror}")

    def fsl_registration(self, image, path: str):
            # Ensure the image file exists
            if not os.path.exists(path):
                raise FileNotFoundError(f"No file found at {path}")

            # Define the FLIRT instance for resampling
            flirt = FLIRT(in_file=image,
                        reference=self.config['methods']['fsl']['reference'],
                        apply_isoxfm=self.config['methods']['fsl']['resolution'],
                        interp=self.config['methods']['fsl']['interp']
                        )
            try:
                result = flirt.run()
            except Exception as e:
                raise RuntimeError(f"FSL FLIRT failed with error: {e}")

            return result.outputs