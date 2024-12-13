import os
import streamlit as st
import uuid

from pathlib import Path
from datetime import datetime

def page_input_selection():
    st.header("Input Selection")

    # Initialize session state if not already done
    if "experiment_data" not in st.session_state:
        st.session_state.experiment_data = {}

    # Experiment logging information
    st.subheader("Experiment Information")
    experiment_name = st.text_input(
        "Experiment Name",
        value=st.session_state.experiment_data.get("experiment_name", ""),
        key="exp_name",
    )
    cohort_name = st.text_input(
        "Cohort Name",
        value=st.session_state.experiment_data.get("cohort_name", ""),
        key="cohort_name",
    )
    notes = st.text_area(
        "Notes", 
        value=st.session_state.experiment_data.get("notes", ""), 
        key="notes"
    )

    # MRI type selection
    st.subheader("MRI Configuration")
    mri_type = st.selectbox(
        "Select MRI Type",
        ["fMRI", "sMRI", "DTI"],
        index=["fMRI", "sMRI", "DTI"].index(
            st.session_state.experiment_data.get("mri_type", "fMRI")
        ),
        key="mri_type",
    )

    # Image format selection
    image_format = st.selectbox(
        "Select Image Format",
        ["DICOM", "NRRD", "NIFTI"],
        index=["DICOM", "NRRD", "NIFTI"].index(
            st.session_state.experiment_data.get("image_format", "NIFTI")
        ),
        key="img_format",
    )

    # Directory selection using a file uploader
    st.subheader("Directory Selection")
    st.text("Select the images you want to process.")
    uploaded_files = st.file_uploader(
        "Choose multiple files", 
        type=None, 
        key="file_upload",
        accept_multiple_files=True,
    )
    if len(uploaded_files) > 0:
        for root, dirs, files in os.walk(Path(os.getcwd())):
            if uploaded_files[0].name in files:
                image_dir = Path(root)
                break
        st.success(f"Selected directory: {image_dir}")
        st.session_state.img_dir = str(image_dir)
    else:
        image_dir = st.session_state.get("img_dir", "")
    
    if image_dir:
        file_paths = [image_dir / path for path in sorted(os.listdir(image_dir))]
    


    # Store the selections in session state
    if st.button("Next", key="next_button"):
        if not experiment_name or not image_dir:
            st.error("Please fill in all required fields")
            return

        # Update experiment data
        st.session_state.experiment_data.update(
            {
                "experiment_name": experiment_name,
                "cohort_name": cohort_name,
                "notes": notes,
                "mri_type": mri_type,
                "image_format": image_format,
                "image_paths": file_paths,
                "image_count": len(file_paths),
                "loaded_dir": image_dir,
                "experiment_id": st.session_state.experiment_data.get(
                    "experiment_id", str(uuid.uuid4())
                ),
                "timestamp": st.session_state.experiment_data.get(
                    "timestamp", datetime.now().isoformat()
                ),
            }
        )
        st.session_state.current_page = "pipeline_selection"
        st.rerun() 