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
            st.session_state.experiment_data.get("image_format", "DICOM")
        ),
        key="img_format",
    )

    # Directory selection using a file uploader
    st.subheader("Directory Selection")
    st.text("Upload a dummy file from the desired directory to select it.")
    uploaded_file = st.file_uploader(
        "Choose a file from the directory", 
        type=None, 
        key="file_upload"
    )

    if uploaded_file is not None:
        # Extract the directory path from the uploaded file
        image_dir = Path(os.getcwd()) / "data/input/example" / uploaded_file.name
        st.success(f"Selected directory: {image_dir}")
        st.session_state.img_dir = str(image_dir)
    else:
        image_dir = st.session_state.get("img_dir", "")

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
                "image_dir": image_dir,
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