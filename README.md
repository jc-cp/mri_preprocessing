# MRI images customazible pre-processing pipeline

This repository aims to present a general, customazible pipeline for MRI images based on a single configuration file (in .json format) that has different flags and according to them, a certain pre-processing procedure with desired steps is performed. This would be a good approach to making a reusable and flexible system that can be used when dealing with MRI images, and which would allow researchers and engineers to easily experiment with different pre-processing steps to see which fits the specific application better. Furthermore, some templates are provided depending on the type of MRI scanning that was used, as these may require specific and different pre-processing steps (e.g. MRI may be based on structural (sMRI), functional (fMRI), diffusion tensor imaging (DTI), etc.).

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
|-- /configs
|   |-- config.json
|   |-- /templates
|   |   |-- fmri_template.json
|   |   |-- smri_template.json
|   |   |-- dwi_template.json
|   |   |-- ...
|-- README.md
```
