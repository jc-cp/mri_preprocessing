"""Setup script for the package."""
from setuptools import find_packages, setup

setup(
    name="mri_preprocessing",
    version="0.2",
    author="Juan Carlos Climent Pardo",
    description="A short description of your package",
    packages=find_packages(),
    install_requires=[
        "numpy",
        "scipy",
        "matplotlib",
        "nipype",
        "nibabel",
        "SimpleITK",
        "scikit-image",
    ],
)
