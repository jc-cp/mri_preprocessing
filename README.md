# MRI images customazible pre-processing pipeline

This repository aims to present a general, customazible pipeline for MRI images based on a single configuration file (in .json format) that has different flags and according to them, a certain pre-processing procedure with desired steps is performed. This would be a good approach to making a reusable and flexible system that can be used when dealing with MRI images, and which would allow researchers and engineers to easily experiment with different pre-processing steps to see which fits the specific application better. Furthermore, some templates are provided depending on the type of MRI scanning that was used, as these may require specific and different pre-processing steps (e.g. MRI may be based on structural (sMRI), functional (fMRI), diffusion tensor imaging (DTI), etc.).

### Structure of Pipeline Process
1. Load the configuration file. 
2. Depending on the configuration file, load the appropriate image file (DICOM, NIfTI, etc.). 
3. If necessary, convert the loaded image to a common working format (usually NIfTI). 
4. Apply the preprocessing steps specified in the configuration file to the image. 
5. Save the preprocessed image. 
6. Handle exceptions and log the processing information for troubleshooting and tracking.

### Folder Structure
```
/mri_preprocessing 
|-- /data
|   |-- /input
|   |-- /output
|-- /src
|   |-- /preprocessing
|   |   |-- __init__.py
|   |   |-- denoising.py
|   |   |-- skull_stripping.py
|   |   |-- slice_timing_correction.py
|   |   |-- motion_correction.py
|   |   |-- normalization.py
|   |   |-- resampling.py
|   |   |-- segmentation.py
|   |   |-- registration.py
|   |   |-- bias_field_correction.py
|   |   |-- spatial_smoothing.py
|   |   |-- feature_extraction.py
|   |   |-- quality_control.py
|   |-- /utils
|   |   |-- __init__.py
|   |   |-- image_loading.py
|   |   |-- image_conversion.py
|   |-- pipeline.py
|   |-- main.py
|-- /cfg
|   |-- config.json
|   |-- /templates
|   |   |-- fmri_template.json
|   |   |-- smri_template.json
|   |   |-- dwi_template.json
|   |   |-- ...
|-- README.md
```

### How To Run
The main.py script only needs one single configuration file, passed as an argument when running the script.
```
python3 main.py -cfg cfg/config.json
python3 main.py --config_path cfg/config.json
```

### MRI Imaging Types Examples
**Structural MRI (sMRI):** These images provide detailed 3D representations of the brain anatomy, and the pre-processing often involves steps like denoising, bias field correction, skull stripping, segmentation, and spatial normalization.

**Functional MRI (fMRI):** fMRI measures brain activity by detecting changes associated with blood flow. In addition to the pre-processing steps for sMRI, fMRI data often require additional steps like slice-timing correction, motion correction, spatial smoothing, temporal filtering, and registration of each individual's data to a common space.

**Diffusion Tensor Imaging (DTI):** DTI is a type of MRI that allows for mapping of the diffusion process of molecules, mainly water, in biological tissues, particularly in the white matter of the brain. DTI pre-processing includes steps like denoising, correction for eddy currents and subject motion, and diffusion tensor estimation.

**Arterial Spin Labeling (ASL):** ASL is a specific type of MRI that is used to measure cerebral blood flow. ASL pre-processing includes steps like motion correction, registration to a standard space, and perfusion-weighted image creation.

**Magnetic Resonance Spectroscopy (MRS):** MRS is an MRI technique used to measure the levels of different metabolites in body tissues. The pre-processing steps for MRS data often include phase correction, baseline correction, and frequency alignment.

**Susceptibility Weighted Imaging (SWI):** SWI is an MRI technique which exploits the susceptibility differences between tissues. Pre-processing steps might include phase unwrapping and filtering, and phase mask creation.
