import os
from pathlib import Path
import zipfile
from io import BytesIO

def get_domain(user_mail):
    # Get the domain of mail adress
    mailDomain = user_mail.split('@')[1]

    if "uni" in mailDomain:
        return "uni"
    elif "uksh" in mailDomain:
        return "uksh"
    return "unknown"

def get_user_name(user_mail):
    return user_mail.split("@")[0]

# Returns a zip file in memory, containing the segmentation and its preprocessed data
# The param segmentation_path is the path to the segmentation file
# The param preprocessed_path is the path to the directory, which contains the preprocessed data
def zip_segmentation(segmentation_path, preprocessed_path, file_format):
    # Create the zip file in memory
    memory_file = BytesIO()
    # Using ZIP_STORED archiving for faster runtime (no compression)
    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_STORED) as zipf:
        # The basefolder, the segmentation is in
        base_folder = f"segmentation"
        # Add the segmentation subfolder containing the segmentation
        arcname = os.path.join(base_folder, "segmentation", os.path.basename(segmentation_path))
        zipf.write(segmentation_path, arcname=arcname)
        
        # Handle dicom file structure
        if file_format == "dicom":
            # Dicom files are in the subdirectory /dicom
            preprocessed_path = os.path.join(preprocessed_path, "dicom")
            # Add the preprocessed subfolder containing all preprocessed files
            for root, _, files in os.walk(preprocessed_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, preprocessed_path)
                    arcname = os.path.join(base_folder, "preprocessed", rel_path)
                    zipf.write(file_path, arcname=arcname)    

        # Handle nifti file format
        elif file_format == "nifti":
            for file in os.listdir(preprocessed_path):
                print(file)  
                file_path = os.path.join(preprocessed_path, file)
                # Ignore files (and directories) that do not start with nifti
                if not file.startswith("nifti"):
                    continue
                # Add other to zip
                arcname = os.path.join(base_folder, "preprocessed", file)
                zipf.write(file_path, arcname=arcname)

    memory_file.seek(0)
    return memory_file

# Returns a zip file in memory, containing the preprocessed data of the preprocessed_path
def zip_preprocessed_files(preprocessed_path):
    # Get the preprocessed files
    t1_path = Path(f'{preprocessed_path}/t1')
    t1km_path = Path(f'{preprocessed_path}/t1km')
    t2_path = Path(f'{preprocessed_path}/t2')
    flair_path = Path(f'{preprocessed_path}/flair')

    # Create the zip file in memory
    memory_file = BytesIO()
    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Add all sequences into a separate directory 
        for directory, folder_name in [(t1_path, 't1'), (t1km_path, 't1km'), (t2_path, 't2'), (flair_path, 'flair')]:
            if directory.exists() and directory.is_dir():
                for file in directory.glob('*.*'):
                    zipf.write(file, arcname=f'{folder_name}/{file.name}')

    memory_file.seek(0)
    return memory_file

# map file_format to /relative/path
file_format_mapping = {
    "nifti": (".nii.gz"),
    "dicom": ("dicom/segmentation.dcm")
}
