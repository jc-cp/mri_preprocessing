"""
Test script to verify that sitk_to_nib correctly preserves spacing information.

This script tests the conversion between SimpleITK and Nibabel formats,
ensuring that voxel spacing is properly encoded in the affine matrix.
"""
import numpy as np
import SimpleITK as sitk
import nibabel as nib
from src.utils import helper_functions as hf


def create_test_sitk_image(size=(64, 64, 64), spacing=(1.0, 1.0, 1.0), origin=(0.0, 0.0, 0.0)):
    """Create a test SimpleITK image with specified properties."""
    # Create random data
    data = np.random.rand(*size).astype(np.float32)
    
    # Create SimpleITK image
    sitk_img = sitk.GetImageFromArray(data)
    sitk_img.SetSpacing(spacing)
    sitk_img.SetOrigin(origin)
    
    # Set identity direction (no rotation)
    sitk_img.SetDirection(np.eye(3).flatten().tolist())
    
    return sitk_img


def test_spacing_preservation():
    """Test that spacing is correctly preserved in sitk_to_nib conversion."""
    print("=" * 70)
    print("Testing sitk_to_nib spacing preservation")
    print("=" * 70)
    
    test_cases = [
        {"spacing": (1.0, 1.0, 1.0), "name": "Isotropic 1mm"},
        {"spacing": (2.0, 2.0, 2.0), "name": "Isotropic 2mm"},
        {"spacing": (0.5, 0.5, 0.5), "name": "Isotropic 0.5mm"},
        {"spacing": (1.0, 1.0, 3.0), "name": "Anisotropic (1,1,3)"},
        {"spacing": (0.8, 0.8, 2.5), "name": "Anisotropic (0.8,0.8,2.5)"},
    ]
    
    all_passed = True
    
    for test_case in test_cases:
        spacing = test_case["spacing"]
        name = test_case["name"]
        
        print(f"\n{name}:")
        print(f"  Input spacing: {spacing}")
        
        # Create test image
        sitk_img = create_test_sitk_image(spacing=spacing)
        
        # Get original spacing
        original_spacing = sitk_img.GetSpacing()
        print(f"  SimpleITK spacing: {original_spacing}")
        
        # Convert to nibabel
        nib_img = hf.sitk_to_nib(sitk_img)
        
        # Get spacing from nibabel
        nib_spacing = nib_img.header.get_zooms()[:3]
        print(f"  Nibabel spacing (get_zooms): {nib_spacing}")
        
        # Verify spacing matches
        spacing_diff = np.abs(np.array(original_spacing) - np.array(nib_spacing))
        max_diff = np.max(spacing_diff)
        
        if max_diff < 1e-6:
            print(f"  ✓ PASSED - Max difference: {max_diff:.2e}")
        else:
            print(f"  ✗ FAILED - Max difference: {max_diff:.2e}")
            all_passed = False
        
        # Also check the affine matrix directly
        affine = nib_img.affine
        affine_spacing = np.sqrt((affine[:3, :3] ** 2).sum(axis=0))
        print(f"  Affine-derived spacing: {tuple(affine_spacing)}")
    
    print("\n" + "=" * 70)
    if all_passed:
        print("✓ ALL TESTS PASSED")
    else:
        print("✗ SOME TESTS FAILED")
    print("=" * 70)
    
    return all_passed


def test_roundtrip_conversion():
    """Test that nib_to_sitk -> sitk_to_nib preserves spacing."""
    print("\n" + "=" * 70)
    print("Testing roundtrip conversion (nib -> sitk -> nib)")
    print("=" * 70)
    
    # Create a nibabel image with specific spacing
    data = np.random.rand(64, 64, 64).astype(np.float32)
    affine = np.diag([1.5, 1.5, 2.0, 1.0])
    original_nib = nib.Nifti1Image(data, affine)
    
    original_spacing = original_nib.header.get_zooms()[:3]
    print(f"\nOriginal Nibabel spacing: {original_spacing}")
    
    # Convert to SimpleITK
    sitk_img = hf.nib_to_sitk(original_nib)
    sitk_spacing = sitk_img.GetSpacing()
    print(f"SimpleITK spacing after conversion: {sitk_spacing}")
    
    # Convert back to Nibabel
    final_nib = hf.sitk_to_nib(sitk_img)
    final_spacing = final_nib.header.get_zooms()[:3]
    print(f"Final Nibabel spacing: {final_spacing}")
    
    # Check if spacing is preserved
    spacing_diff = np.abs(np.array(original_spacing) - np.array(final_spacing))
    max_diff = np.max(spacing_diff)
    
    print(f"\nMax spacing difference: {max_diff:.2e}")
    
    if max_diff < 1e-6:
        print("✓ ROUNDTRIP TEST PASSED")
        return True
    else:
        print("✗ ROUNDTRIP TEST FAILED")
        return False


def test_resampling_workflow():
    """Test the actual resampling workflow to ensure spacing is correct."""
    print("\n" + "=" * 70)
    print("Testing resampling workflow (simulating actual pipeline use)")
    print("=" * 70)
    
    # Create a test image with non-isotropic spacing
    original_spacing = (2.0, 2.0, 3.0)
    target_spacing = (1.0, 1.0, 1.0)
    
    print(f"\nOriginal spacing: {original_spacing}")
    print(f"Target spacing: {target_spacing}")
    
    # Create test SimpleITK image
    sitk_img = create_test_sitk_image(size=(32, 32, 32), spacing=original_spacing)
    
    # Simulate resampling
    old_size = sitk_img.GetSize()
    old_spacing = sitk_img.GetSpacing()
    new_spacing = target_spacing
    
    new_size = [
        int(round((old_size[0] * old_spacing[0]) / float(new_spacing[0]))),
        int(round((old_size[1] * old_spacing[1]) / float(new_spacing[1]))),
        int(round((old_size[2] * old_spacing[2]) / float(new_spacing[2]))),
    ]
    
    print(f"Old size: {old_size}")
    print(f"New size: {new_size}")
    
    # Create resampler
    resampler = sitk.ResampleImageFilter()
    resampler.SetOutputSpacing(new_spacing)
    resampler.SetSize(new_size)
    resampler.SetOutputPixelType(sitk.sitkFloat32)
    resampler.SetInterpolator(sitk.sitkLinear)
    resampler.SetOutputDirection(sitk_img.GetDirection())
    resampler.SetOutputOrigin(sitk_img.GetOrigin())
    
    # Execute resampling
    resampled_sitk = resampler.Execute(sitk_img)
    
    print(f"\nResampled SimpleITK spacing: {resampled_sitk.GetSpacing()}")
    
    # Convert to nibabel (this is where the bug was)
    resampled_nib = hf.sitk_to_nib(resampled_sitk)
    
    final_spacing = resampled_nib.header.get_zooms()[:3]
    print(f"Final Nibabel spacing: {final_spacing}")
    
    # Check if spacing matches target
    spacing_diff = np.abs(np.array(target_spacing) - np.array(final_spacing))
    max_diff = np.max(spacing_diff)
    
    print(f"\nMax difference from target: {max_diff:.2e}")
    
    if max_diff < 1e-6:
        print("✓ RESAMPLING WORKFLOW TEST PASSED")
        return True
    else:
        print("✗ RESAMPLING WORKFLOW TEST FAILED")
        print(f"  Expected: {target_spacing}")
        print(f"  Got: {tuple(final_spacing)}")
        return False


def explain_affine_math():
    """Explain the math behind the affine matrix construction."""
    print("\n" + "=" * 70)
    print("EXPLANATION: Affine Matrix Construction")
    print("=" * 70)
    
    print("""
The affine matrix in NIfTI format encodes the transformation from voxel
coordinates to physical (world) coordinates. It's a 4x4 matrix:

    [R11*s1  R12*s2  R13*s3  tx]
    [R21*s1  R22*s2  R23*s3  ty]
    [R31*s1  R32*s2  R33*s3  tz]
    [  0       0       0      1 ]

Where:
- R is the 3x3 rotation/direction matrix (defines orientation)
- s1, s2, s3 are the voxel spacings (physical distance between voxels)
- tx, ty, tz are the origin coordinates (physical location of voxel [0,0,0])

The key insight is that the top-left 3x3 submatrix combines BOTH
direction and spacing. The correct construction is:

    affine[:3, :3] = direction @ np.diag(spacing)

This is MATRIX MULTIPLICATION, not element-wise multiplication.

Why this matters:
- When nibabel calls get_zooms(), it computes: sqrt(sum(affine[:3, :3]^2, axis=0))
- This is the L2 norm of each column, which gives back the spacing values
- If we use element-wise multiplication (*), the spacing is incorrectly encoded

Example:
    direction = [[1, 0, 0],
                 [0, 1, 0],
                 [0, 0, 1]]  (identity - no rotation)
    
    spacing = [1.0, 1.0, 1.0]
    
    Correct (matrix mult):
        direction @ diag(spacing) = [[1, 0, 0],
                                      [0, 1, 0],
                                      [0, 0, 1]]
    
    Incorrect (element-wise):
        direction * spacing = [[1, 0, 0],
                               [0, 1, 0],
                               [0, 0, 1]]
    
    In this case they're the same, but with non-identity direction matrices,
    element-wise multiplication produces incorrect results!
""")


if __name__ == "__main__":
    # Run all tests
    explain_affine_math()
    
    test1 = test_spacing_preservation()
    test2 = test_roundtrip_conversion()
    test3 = test_resampling_workflow()
    
    print("\n" + "=" * 70)
    print("FINAL SUMMARY")
    print("=" * 70)
    print(f"Spacing preservation test: {'✓ PASSED' if test1 else '✗ FAILED'}")
    print(f"Roundtrip conversion test: {'✓ PASSED' if test2 else '✗ FAILED'}")
    print(f"Resampling workflow test: {'✓ PASSED' if test3 else '✗ FAILED'}")
    
    if test1 and test2 and test3:
        print("\n✓✓✓ ALL TESTS PASSED ✓✓✓")
    else:
        print("\n✗✗✗ SOME TESTS FAILED ✗✗✗")
    print("=" * 70)

