import os
from nipype.interfaces import spm
import itk



class Registration:
    def __init__(self, config: dict):
        self.config = config

    def run(self, image: str):
        if self.config['methods']['spm']['enabled']:
            return self.spm_registration(image)
        if self.config['methods']['itk']['enabled']:
            return self.itk_registration(image)


    def itk_registration(self, image):
        # Ensure the image file exists
        if not os.path.exists(image):
            raise FileNotFoundError(f"No file found at {image}")
         
        template = self.config['methods']['itk']['template']
        output_path = self.config['methods']['itk']['output_path']
        create_subfolder = self.config['methods']['itk']['create_subfolder']

        fixed_image = itk.imread(template, itk.F)

        # Import Parameter Map
        parameter_object = itk.ParameterObject.New()
        parameter_object.AddParameterFile('data/registration_templates/Parameters_Rigid.txt')

        if "nii" in image:
            print(image)

            # Call registration function
            try:        
                moving_image = itk.imread(image, itk.F)
                result_image, result_transform_parameters = itk.elastix_registration_method(
                    fixed_image, moving_image,
                    parameter_object=parameter_object,
                    log_to_console=False)
                image_id = image.split("/")[-1]
                
                if create_subfolder:
                    new_dir = output_path+image_id.split(".")[0] 
                    if not os.path.exists(new_dir):
                        os.mkdir(new_dir)
                    itk.imwrite(result_image, new_dir+"/"+image_id)
                else:
                    itk.imwrite(result_image, output_path+"/"+image_id)
                    
                print("Registered ", image_id)
            except:
                print("Cannot transform", image.split("/")[-1])
        else:
            raise FileNotFoundError(f"No file found with right suffix .nii!")



    def spm_registration(self, image):
        # Ensure the image file exists
        if not os.path.exists(image):
            raise FileNotFoundError(f"No file found at {image}")
         
        template = self.config['methods']['spm']['template']

        # Define the SPM Normalize12 instance for registration
        norm12 = spm.Normalize12(jobtype='estwrite',
                                 tpm=template,
                                 apply_to_files=[image])
        
        try:
            result = norm12.run()
        except Exception as e:
            raise RuntimeError(f"SPM Normalize12 failed with error: {e}")

        return result.outputs