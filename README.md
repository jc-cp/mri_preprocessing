# MRI customazible pre-processing pipeline

This repository aims to present a general, customazible pipeline for MRI images based on a single configuration file (in .json format) that has different flags and according to them, a certain pre-processing procedure with desired steps is performed. This would be a good approach to making a reusable and flexible system that can be used when dealing with MRI images, and which would allow researchers and engineers to easily experiment with different pre-processing steps to see which fits the specific application better. Furthermore, some templates are provided depending on the type of MRI scanning that was used, as these may require specific and different pre-processing steps (e.g. MRI may be based on structural (sMRI), functional (fMRI), diffusion tensor imaging (DTI), etc.).

## Structure of Pipeline Process
1. Load the configuration file. 
2. Depending on the configuration file, load the appropriate image file (DICOM, NIfTI, etc.). 
3. If necessary, convert the loaded image to a common working format (usually NIfTI). 
4. Apply the preprocessing steps specified in the configuration file to the image. 
5. Save the preprocessed image. 
6. Handle exceptions and log the processing information for troubleshooting and tracking.

## Folder Structure
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

## How To Run
The main.py script only needs one single configuration file, passed as an argument when running the script.
```
python3 main.py -cfg cfg/config.json
python3 main.py --config_path cfg/config.json
```

## MRI Imaging Types Examples
**Structural MRI (sMRI):** These images provide detailed 3D representations of the brain anatomy, and the pre-processing often involves steps like denoising, bias field correction, skull stripping, segmentation, and spatial normalization.

**Functional MRI (fMRI):** fMRI measures brain activity by detecting changes associated with blood flow. In addition to the pre-processing steps for sMRI, fMRI data often require additional steps like slice-timing correction, motion correction, spatial smoothing, temporal filtering, and registration of each individual's data to a common space.

**Diffusion Tensor Imaging (DTI):** DTI is a type of MRI that allows for mapping of the diffusion process of molecules, mainly water, in biological tissues, particularly in the white matter of the brain. DTI pre-processing includes steps like denoising, correction for eddy currents and subject motion, and diffusion tensor estimation.

**Arterial Spin Labeling (ASL):** ASL is a specific type of MRI that is used to measure cerebral blood flow. ASL pre-processing includes steps like motion correction, registration to a standard space, and perfusion-weighted image creation.

**Magnetic Resonance Spectroscopy (MRS):** MRS is an MRI technique used to measure the levels of different metabolites in body tissues. The pre-processing steps for MRS data often include phase correction, baseline correction, and frequency alignment.

**Susceptibility Weighted Imaging (SWI):** SWI is an MRI technique which exploits the susceptibility differences between tissues. Pre-processing steps might include phase unwrapping and filtering, and phase mask creation.

## Preprocessing
<details>
<summary>Denoising</summary>
Denoising of MRI images can be accomplished by numerous methods, each with its strengths and weaknesses. Here are two methods that are commonly used:

    Gaussian filtering: This is a simple and fast technique that blurs an image using a Gaussian kernel in order to reduce noise. It works by averaging the pixels within a neighborhood defined by the Gaussian kernel, thereby smoothing out small fluctuations caused by noise. However, a disadvantage is that it also blurs edges and fine details in the image.

    Non-local Means (NLM): This is a more sophisticated denoising technique that is particularly effective for preserving edges and fine details. It works by searching the whole image for similar patches to the one being denoised, and averaging them. The degree of averaging is based on the similarity of patches, with more similar patches contributing more to the result. This allows NLM to preserve edges and fine details while still reducing noise. However, it is computationally more expensive than simple Gaussian filtering.

    Total Variation Denoising: This method leverages the concept of Total Variation which focuses on reducing the 'total variation' of the image, where variation is measured as the integral of the absolute gradient of the image. This method is very effective in removing "salt and pepper" type noise while preserving edges and can be adapted for multiplicative noise found in MRI images.

    Anisotropic diffusion (Perona-Malik method): This technique aims to reduce noise while preserving structural edges by diffusing image pixels along the direction of less intensity variation.

    Wavelet Transform based denoising: Wavelet transform allows an image to be decomposed on a basis that includes localization in space and in frequency. By eliminating the coefficients of the wavelet transform that mainly contain noise, one can reconstruct an image with reduced noise.

It's important to note that the best method to use depends on the specifics of your image data and the analysis you want to perform. It can be beneficial to experiment with different methods to see which one gives the best results for your particular application.
</details>

<details>
<summary>Motion Correction</summary>
Motion correction, or realignment, also known as "intrasession registration" or "intra-subject registration" is used to align all the volumes of the same subject in a time series to a reference volume. It is a critical preprocessing step in MRI analysis, especially for functional MRI (fMRI) where a series of images are collected over time. The subject's head movement during the scanning can introduce substantial errors and bias in the subsequent analysis. Here are two commonly used methods:

    Volume-Realignment: This method estimates the six parameters of rigid-body spatial transformations (3 translations and 3 rotations) that best align all 3D volumes to a reference volume (typically the first volume or the mean of all volumes).

    Slice-Timing Realignment: This method is specifically for correcting the timing difference among slices within each volume. As most fMRI scans acquire different slices at different times within each TR (Repetition Time), this can lead to spatial-temporal misalignment. It can be corrected by resampling the signal at each voxel to a reference time point, using slice-timing information.
Also, note that slice timing correction is usually performed before motion correction in the fMRI preprocessing pipeline.
</details>

<details>
<summary>Normalization</summary>
Normalization is an essential pre-processing step in image analysis. It helps to standardize the intensity values of an image and to reduce the variability across different images. There are several methods of image normalization:

    Intensity Normalization: This method involves re-scaling the intensity range of the image so that it spans a standard range, typically [0, 1] or [0, 255].

    Z-score Normalization: This method normalizes the image intensity values to have zero mean and unit standard deviation. Each voxel's intensity is subtracted by the mean and divided by the standard deviation.

    Histogram Equalization: This method transforms the image to have a uniform histogram. It is particularly useful when the image's histogram is heavily skewed or if the image has low contrast.
</details>

<details>
<summary>Skull Stripping</summary>
Skull stripping is a critical pre-processing step in the analysis of neuroimaging data. Several methods have been developed for this purpose, with varying degrees of complexity and performance. Here are three common methods:

    Threshold-Based Skull Stripping: This method works by setting a threshold for the intensity of the image. Voxels with intensity values below the threshold are considered to be part of the skull and are thus removed. This method is straightforward to implement but may not perform well if the intensity distribution of the brain tissue overlaps with that of the skull.

    Morphological Operations-Based Skull Stripping: This method involves a sequence of morphological operations, such as dilation, erosion, opening, and closing. The idea is to remove small connected components and holes in the brain image, which are likely to represent non-brain tissues.

    Atlas-Based Skull Stripping: This method uses a pre-defined atlas or template of the brain, which is registered to the subject's image. The atlas typically includes a binary mask that defines the brain region. Once the atlas is aligned with the subject's image, the mask can be applied to remove the skull.
</details>