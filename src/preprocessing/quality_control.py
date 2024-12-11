import nibabel as nib
import numpy as np
from scipy import stats
import json

class QualityControl:
    def __init__(self, config: dict):
        self.config = config
        self.qc_report = {}

    def run(self, image, img_path):
        """Comprehensive image quality check."""
        try:
            img = nib.load(image) if isinstance(image, str) else image
            data = img.get_fdata()
            
            # Basic checks
            self._check_dimensions(img)
            self._check_resolution(img)
            self._check_data_integrity(data)
            self._check_intensity_properties(data)
            self._check_orientation(img)
            
            # Optional advanced checks based on config
            if self.config.get("check_snr", False):
                self._check_snr(data)
            if self.config.get("check_contrast", False):
                self._check_contrast(data)
            print("Quality control passed, saving report...")
            # save the report
            with open(self.config.get("qc_report_path", "qc_report.json"), "w") as f:
                json.dump(self.qc_report, f)
            return img

        except Exception as error:
            print(f"Quality control failed: {str(error)}")
            with open(self.config.get("qc_report_path", "qc_report.json"), "w") as f:
                json.dump(self.qc_report, f)
            return img

    def _check_dimensions(self, img):
        """Check image dimensions and size."""
        expected_dims = self.config.get("expected_dims")
        min_voxels = self.config.get("min_voxels", 10000)
        
        # Check basic dimensions
        if expected_dims and img.shape != tuple(expected_dims):
            raise ValueError(f"Image has dimensions {img.shape}, expected {expected_dims}")
        
        # Check total volume
        total_voxels = np.prod(img.shape)
        if total_voxels < min_voxels:
            raise ValueError(f"Image has too few voxels: {total_voxels}")
        
        self.qc_report["dimensions"] = {"shape": img.shape, "total_voxels": str(total_voxels)}

    def _check_resolution(self, img):
        """Check voxel size and aspect ratio."""
        expected_voxel_size = self.config.get("expected_voxel_size")
        max_aspect_ratio = self.config.get("max_aspect_ratio", 4.0)
        
        voxel_size = img.header.get_zooms()[:3]
        aspect_ratios = [max(voxel_size)/min(voxel_size)]
        
        if expected_voxel_size and voxel_size != tuple(expected_voxel_size):
            raise ValueError(f"Image has voxel size {voxel_size}, expected {expected_voxel_size}")
        
        if max(aspect_ratios) > max_aspect_ratio:
            raise ValueError(f"Image has irregular aspect ratio: {max(aspect_ratios)}")
        
        self.qc_report["resolution"] = {"voxel_size": str(voxel_size), "aspect_ratios": str(aspect_ratios)}

    def _check_data_integrity(self, data):
        """Check for data corruption or invalid values."""
        # Check for NaN/Inf values
        if np.any(~np.isfinite(data)):
            raise ValueError("Image contains NaN or Inf values")
        
        # Check for all-zero slices in the middle 85% of the volume
        n_slices = data.shape[-1]
        start_idx = int(n_slices * 0.075)  # Skip first 7.5%
        end_idx = int(n_slices * 0.925)    # Skip last 7.5%
        
        # Find zero slices in the middle region
        middle_zero_slices = [i for i in range(start_idx, end_idx) 
                            if np.all(data[..., i] == 0)]
        
        if middle_zero_slices:
            raise ValueError(
                f"Image contains all-zero slices in central region at indices: {middle_zero_slices}"
            )
        
        # Get all zero slices for reporting
        all_zero_slices = [i for i in range(n_slices) if np.all(data[..., i] == 0)]
        self.qc_report["integrity"] = {"zero_slices": str(all_zero_slices)}

    def _check_intensity_properties(self, data):
        """Check intensity distribution properties."""
        # Basic statistics
        stats_dict = {
            "min": float(np.min(data)),
            "max": float(np.max(data)),
            "mean": float(np.mean(data)),
            "std": float(np.std(data)),
            "median": float(np.median(data))
        }
        
        # Check for reasonable intensity range
        dynamic_range = stats_dict["max"] - stats_dict["min"]
        if dynamic_range < self.config.get("min_intensity_range", 100):
            raise ValueError(f"Image has low dynamic range: {dynamic_range}")
        
        # Check for outliers
        z_scores = np.abs(stats.zscore(data.flatten()))
        outlier_percentage = np.sum(z_scores > 3) / len(z_scores)
        if outlier_percentage > self.config.get("max_outlier_percentage", 0.01):
            raise ValueError(f"Image has high percentage of outliers: {outlier_percentage:.2%}")
        
        self.qc_report["intensity"] = {**stats_dict, "outlier_percentage": str(outlier_percentage)}

    def _check_orientation(self, img):
        """Check image orientation information."""
        # Get orientation from affine
        orientation = nib.aff2axcodes(img.affine)
        # Convert expected orientation from list to tuple to match orientation type
        expected_orientation = tuple(self.config.get("expected_orientation", ["R", "A", "S"]))
        
        if orientation != expected_orientation:
            print(f"Warning: Image orientation {orientation} differs from expected {expected_orientation}")
        self.qc_report["orientation"] = {"current": str(orientation), "expected": str(expected_orientation)}

    def _check_snr(self, data):
        """Calculate Signal-to-Noise Ratio."""
        # Simple SNR calculation (mean/std)
        signal = np.mean(data)
        noise = np.std(data)
        snr = signal/noise if noise != 0 else 0
        
        min_snr = self.config.get("min_snr", 5.0)
        if snr < min_snr:
            raise ValueError(f"Image has low SNR: {snr}")
        
        self.qc_report["snr"] = str(snr)

    def _check_contrast(self, data):
        """Check image contrast."""
        # Calculate contrast using 95th and 5th percentiles
        p95 = np.percentile(data, 95)
        p5 = np.percentile(data, 5)
        contrast = (p95 - p5) / (p95 + p5) if (p95 + p5) != 0 else 0
        
        min_contrast = self.config.get("min_contrast", 0.1)
        if contrast < min_contrast:
            raise ValueError(f"Image has low contrast: {contrast}")
        
        self.qc_report["contrast"] = str(contrast)
