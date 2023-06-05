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
<summary>Bias Field Correction (N4)</summary>
N4 bias field correction is a key preprocessing step for improving the quality of MRI images. It compensates for the intensity inhomogeneities, or bias field, which are inherent in MRI images due to variations in the sensitivity of the radio frequency coils and other factors. This variation can distort the intensity values of the voxels, making subsequent image analysis tasks challenging. The presented implementation methods include:

    1. An SITK variant, which is great but tends to be a little slow
    2. An LapGM implementation

</details>

<details>
<summary>Binning</summary>
Usually refers to the process of reducing the number of levels in an image or signal. This can often be thought of as a type of quantization. For instance, if you have an image with a bit depth of 16 (meaning there are 65,536 possible levels for each pixel), you might reduce this to 8 bits (256 levels) or less. Some common binning strategies include:

    Fixed-Width Binning: The range of the data is divided into a set of equally spaced bins. Each bin has the same width. This is the most common binning strategy and is typically used when the data is uniformly distributed.

    Adaptive Binning: The bin widths are not constant and are determined based on the data. This strategy is often used when the data has a skewed distribution. There are various methods for determining the bin widths, such as Freedman-Diaconis rule or Scott's rule.

    Quantile Binning: The data is divided into a set of equal-sized bins, where each bin contains approximately the same number of data points. This is especially useful when dealing with skewed data or when it's important to rank data points relative to one another.
</details>

<details>
<summary>Conversion (3D to 2D)</summary>
Used when the memory to train a 3D model is limited; or when scarce amount of data. Attention: make sure to co-register the scans beforehand, so when the axial 2D slices are created the iteration is over the same axis.
</details>

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
<summary>Filtering</summary>

    This usually refers to the process of making the image less detailed or blurry, which can help in reducing high-frequency noise and making the image interpretation simpler. Methods for smoothing include Gaussian smoothing, Median Filtering, and Bilateral Filtering. Attention: While some methods like Gaussian smoothing or NLM can be used for both denoising and smoothing, the goals and the parameters used might be different. For example, in denoising, you might want to preserve more details and thus use a smaller parameter for the extent of smoothing, while for smoothing, you might want to reduce more details and thus use a larger parameter.

    The implemenation of otsu_filtering applies the calcualted threshold to the input image to create a binary image: all pixels with intensities above the threshold are set to 1, the others to 0.

</details>


<details>
<summary>Motion Correction</summary>

    Motion correction, also known as "intrasession registration" or "intra-subject registration" is used to align all the volumes of the same subject in a time series to a reference volume. It is a critical preprocessing step in MRI analysis, especially for functional MRI (fMRI) where a series of images are collected over time. The subject's head movement during the scanning can introduce substantial errors and bias in the subsequent analysis. A specific method is Volume-Realignment, which estimates the six parameters of rigid-body spatial transformations (3 translations and 3 rotations) that best align all 3D volumes to a reference volume (typically the first volume or the mean of all volumes).

</details>

<details>
<summary>Normalization</summary>
Normalization is an essential pre-processing step in image analysis. It helps to standardize the intensity values of an image and to reduce the variability across different images. There are several methods of image normalization:

    Intensity Normalization: This method involves re-scaling the intensity range of the image so that it spans a standard range, typically [0, 1] or [0, 255].

    Z-score Normalization: This method normalizes the image intensity values to have zero mean and unit standard deviation. Each voxel's intensity is subtracted by the mean and divided by the standard deviation.

    Histogram Equalization: This method transforms the image to have a uniform histogram. It is particularly useful when the image's histogram is heavily skewed or if the image has low contrast.
</details>

<details>
<summary>Quality Control</summary>
This step involves ensuring that the collected MRI data is of high quality. Poor quality data can occur due to numerous factors such as patient movement, technical issues with the scanner, etc. QC involves steps like visual inspection of the data, checking for excessive motion, verifying good signal-to-noise ratio, etc. This is crucial because poor quality data can affect the subsequent steps and lead to incorrect results. In some automated pipelines, QC might involve algorithms for outlier detection or checks for unexpected data characteristics.
</details>

<details>
<summary>Registration</summary>

    Registration is a broader term that refers to the process of aligning different datasets into one common space. In MRI, this is often used to align an individual's anatomical scan with a standard template (like the MNI template), allowing for group analyses across individuals. It could also refer to the process of aligning an individual's functional images with their own anatomical scan, which ensures that the functional data can be accurately overlaid onto the correct anatomical structures.

    When performing the registration step for MRI (pediatric) brain images, please access the NIHPD template website for brain volumes from the 4.5 to 18.5y age range (https://www.mcgill.ca/bic/software/tools-data-analysis/anatomical-mri/atlases/nihpd). The download files cna be accessed here (http://www.bic.mni.mcgill.ca/~vfonov/nihpd/obj1/). Please include / copy the dowloaded templates to the "/mri-preprocessing/data/registration_templates/" folder if you want to enable the registration setp.

</details>


<details>
<summary>Resampling</summary>
    
    In the MRI preprocessing pipeline, resampling is often done after the registration step. The idea is to bring all the images to the same standard space (like MNI space) and the same resolution, so that each voxel corresponds to the same physical location across subjects. In terms of implementation, various tools can be used for resampling, such as:

        1. FSL's FLIRT
        2.ANTs (Advanced Normalization Tools)
    
    Remember that ANTs' ResampleImageBySpacing changes the spacing between pixels/voxels in the image, whereas FLIRT changes the resolution to an isotropic voxel size
</details>

<details>
<summary>Skull Stripping</summary>
Skull stripping is a critical pre-processing step in the analysis of neuroimaging data. Several methods have been developed for this purpose, with varying degrees of complexity and performance. Here are three common methods:

    Threshold-Based Skull Stripping: This method works by setting a threshold for the intensity of the image. Voxels with intensity values below the threshold are considered to be part of the skull and are thus removed. This method is straightforward to implement but may not perform well if the intensity distribution of the brain tissue overlaps with that of the skull.

    Morphological Operations-Based Skull Stripping: This method involves a sequence of morphological operations, such as dilation, erosion, opening, and closing. The idea is to remove small connected components and holes in the brain image, which are likely to represent non-brain tissues.

    Atlas-Based Skull Stripping: This method uses a pre-defined atlas or template of the brain, which is registered to the subject's image. The atlas typically includes a binary mask that defines the brain region. Once the atlas is aligned with the subject's image, the mask can be applied to remove the skull.
</details>

<details>
<summary>Slice-Timing Realignment</summary>

    Depending on the scanner setup, the slices os MRIs could be acquired sequentially or in an interleaved fashion. This means that there is a small delay between when the first slice is acquired and when the last slice is acquired. As most fMRI scans acquire different slices at different times within each TR (Repetition Time), this can lead to spatial-temporal misalignment. However, when analyzing the data, it is often assumed that all slices from a given volume are acquired simultaneously. Slice-timing is specifically for correcting the timing difference among slices within each volume. It can be corrected by resampling the signal at each voxel to a reference time point, using the slice-timing information. Also note that slice timing correction is usually performed before motion correction in the overall fMRI preprocessing pipeline.

</details>


### To do's
- [ ] Add other quality control checks as needed
- [ ] Check MRIQC for quality control
- [ ] Implement LAPGM Bias Field Correction
- [ ] Check Binning expected format for the class 
- [ ] Implement final conversion from 3d to 2d
- [ ] Create methods dict in classes to get parameters easier 
- [ ] Create Feature extraction class and add readme description
- [ ] Rethink pre-processing segmentation options
- [ ] Recheck slice order and the time acquisition used in the slice timing correction -- should match your actual MRI data acquisition parameters
- [ ] Implement intensity normalization option from https://github.com/jcreinhold/intensity-normalization
- [ ] Check output from spm registration
- [ ] Check how to make parameter file for registration modular, how to properly get it 
- [ ] Check output from the libraries in resmapling
- [ ] Implement option for HDBET skull stripping and add to the installation
- [x] Implement the DICOM to NIFTI conversion with checks 
- [x] Rethink and implement the image loading class
- [x] Rethink and implement the image saving class
- [ ] Finalise the list of steps in the pipeline, taking into account the order 
- [ ] Have one default config.json in proper format
- [ ] Have a fmri template JSON
- [ ] Have a smri template JSON
- [ ] Have a dti template JSON
- [ ] Edit readme.md folder structure overview
- [ ] Create the requirements.txt 
- [ ] Think about deployment in docker
- [ ] Edit readme.md folder structure overview
- [ ] Fix the Pylint CI errors
- [ ] Add A/B tests and some other GitActions (like formatting)
- [ ] Look at the BIDS standard and see if reasonable
- [ ] Testing of different steps 
- [ ] Add visualization script to test the functionalities 
- [ ] Do an overall method to readme check for completeness

